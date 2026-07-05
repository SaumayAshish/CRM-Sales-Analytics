"""
Lead scoring engine.

Traces to: BR-02, BR-18, FR-49, FR-50, FR-51. Plain-English summary: a lead's
score is the sum of the weights of every scoring_criteria row that matches
the lead, evaluated against the single active scoring_rule. Criteria fall
into four families (FR-50):

  - attribute-based   ("source equals Referral", "company_size greater_than 500")
  - behavior-based    ("activity_type_exists equals Meeting" -- e.g. a demo happened)
  - recency-based     ("activity_recency_days less_than_or_equal 7" -- engaged recently)
  - negative-signal   ("no_response_days greater_than_or_equal 30" -- gone quiet, weight is negative)

The same field_name/operator/comparison_value/weight shape covers all four;
only the *interpretation* of field_name differs, dispatched below.
"""
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.lead import Lead
from app.models.reference import ActivityType, LeadSource
from app.models.workflow import ScoringCriteria, ScoringRule


def _last_activity_at(db: Session, lead_id) -> datetime | None:
    return (
        db.query(func.max(Activity.created_at))
        .filter(Activity.lead_id == lead_id, Activity.deleted_at.is_(None))
        .scalar()
    )


def _compare(actual: float, operator: str, expected: float) -> bool:
    if operator == "greater_than":
        return actual > expected
    if operator == "greater_than_or_equal":
        return actual >= expected
    if operator == "less_than":
        return actual < expected
    if operator == "less_than_or_equal":
        return actual <= expected
    if operator == "equals":
        return actual == expected
    return False


def _criterion_matches(db: Session, lead: Lead, criterion: ScoringCriteria) -> bool:
    field = criterion.field_name

    if field == "source":
        source = db.query(LeadSource).filter(LeadSource.id == lead.source_id).first()
        return criterion.operator == "equals" and source is not None and source.name == criterion.comparison_value

    if field == "company_size":
        size = (lead.custom_fields or {}).get("company_size")
        if size is None:
            return False
        return _compare(float(size), criterion.operator, float(criterion.comparison_value))

    if field == "activity_recency_days":
        last_activity = _last_activity_at(db, lead.id)
        if last_activity is None:
            return False
        days_ago = (datetime.now(timezone.utc) - last_activity).days
        return _compare(days_ago, criterion.operator, float(criterion.comparison_value))

    if field == "no_response_days":
        last_activity = _last_activity_at(db, lead.id) or lead.created_at
        days_ago = (datetime.now(timezone.utc) - last_activity).days
        return _compare(days_ago, criterion.operator, float(criterion.comparison_value))

    if field == "activity_type_exists":
        exists = (
            db.query(Activity)
            .join(ActivityType, Activity.type_id == ActivityType.id)
            .filter(Activity.lead_id == lead.id, ActivityType.name == criterion.comparison_value)
            .first()
        )
        return criterion.operator == "equals" and exists is not None

    return False


def score_band(score: int, hot_threshold: int, warm_threshold: int) -> str:
    if score >= hot_threshold:
        return "Hot"
    if score >= warm_threshold:
        return "Warm"
    return "Cold"


def evaluate_lead_score(db: Session, lead: Lead) -> tuple[int, str, list[dict], str | None]:
    """FR-49/FR-51: returns (score, band, matched_criteria_breakdown, scoring_rule_id)."""
    rule = db.query(ScoringRule).filter(ScoringRule.is_active.is_(True)).first()
    if rule is None:
        return 0, "Cold", [], None

    criteria = db.query(ScoringCriteria).filter(ScoringCriteria.scoring_rule_id == rule.id).all()
    matched: list[dict] = []
    total = 0
    for criterion in criteria:
        if _criterion_matches(db, lead, criterion):
            total += criterion.weight
            matched.append(
                {
                    "criterion_id": str(criterion.id), "field_name": criterion.field_name,
                    "operator": criterion.operator, "comparison_value": criterion.comparison_value,
                    "weight": criterion.weight,
                }
            )

    band = score_band(total, rule.hot_threshold, rule.warm_threshold)
    return total, band, matched, str(rule.id)
