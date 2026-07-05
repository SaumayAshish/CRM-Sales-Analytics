"""
Lead scoring rule management and score inspection endpoints.

Traces to: FR-34 (Admin config), FR-51 (transparency/score breakdown).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.lead import Lead
from app.models.workflow import ScoringCriteria, ScoringRule
from app.schemas.scoring import ScoreBreakdownResponse, ScoringRuleCreate, ScoringRuleRead
from app.services.audit import write_audit_log
from app.services.scoring_engine import evaluate_lead_score

router = APIRouter()


@router.get("/lead-scoring/rules", response_model=list[ScoringRuleRead])
def list_scoring_rules(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[ScoringRule]:
    return db.query(ScoringRule).all()


@router.post("/lead-scoring/rules", response_model=ScoringRuleRead, status_code=status.HTTP_201_CREATED)
def create_scoring_rule(
    payload: ScoringRuleCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> ScoringRule:
    """FR-34: Admin-only. Creating an active rule while another is active is
    allowed here (evaluate_lead_score takes the first active one found) --
    Admin is expected to deactivate the old rule via PATCH when replacing it."""
    rule = ScoringRule(
        name=payload.name, hot_threshold=payload.hot_threshold,
        warm_threshold=payload.warm_threshold, is_active=payload.is_active,
    )
    db.add(rule)
    db.flush()
    for c in payload.criteria:
        db.add(
            ScoringCriteria(
                scoring_rule_id=rule.id, field_name=c.field_name, operator=c.operator,
                comparison_value=c.comparison_value, weight=c.weight,
            )
        )
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="scoring_rules", entity_id=rule.id)
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/leads/{lead_id}/recalculate-score", response_model=ScoreBreakdownResponse)
def recalculate_score(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """FR-49: re-run the scoring engine on demand (e.g., after a new activity)."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    lead.score = score
    lead.score_band = band
    lead.scoring_rule_id = rule_id
    db.commit()

    return {
        "lead_id": lead.id, "score": score, "score_band": band,
        "scoring_rule_id": rule_id, "matched_criteria": matched,
    }


@router.get("/leads/{lead_id}/score-breakdown", response_model=ScoreBreakdownResponse)
def get_score_breakdown(
    lead_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> dict:
    """FR-51: transparency -- shows which criteria matched without mutating the lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    return {
        "lead_id": lead.id, "score": score, "score_band": band,
        "scoring_rule_id": rule_id, "matched_criteria": matched,
    }
