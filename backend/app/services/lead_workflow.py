"""
Glue between the scoring engine and the auto-assignment engine, invoked on
lead create/update and on new-activity-logged.

Traces to: FR-49 (scoring triggers), FR-52 (Hot leads auto-assign),
FR-36 (automated actions logged with a null/system actor, distinct from
human actions).
"""
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.services.assignment_engine import assign_lead_to_rep
from app.services.audit import write_audit_log
from app.services.scoring_engine import evaluate_lead_score
from app.services.workflow_engine import dispatch_event


def rescore_and_maybe_assign(db: Session, lead: Lead) -> None:
    previous_band = lead.score_band
    score, band, _matched, rule_id = evaluate_lead_score(db, lead)

    lead.score = score
    lead.score_band = band
    lead.scoring_rule_id = rule_id

    write_audit_log(
        db, actor_id=None, action="UPDATE", entity_type="leads", entity_id=lead.id,
        before_state={"score_band": previous_band}, after_state={"score_band": band, "score": score},
    )

    # FR-52: only auto-assign on the transition into Hot, and only if not already assigned.
    if band == "Hot" and previous_band != "Hot" and lead.assigned_to is None:
        rep = assign_lead_to_rep(db)
        if rep is not None:
            lead.assigned_to = rep.id
            write_audit_log(
                db, actor_id=None, action="UPDATE", entity_type="leads", entity_id=lead.id,
                before_state={"assigned_to": None}, after_state={"assigned_to": str(rep.id)},
            )

    # FR-59: lead_scored is a workflow trigger event, independent of the
    # built-in auto-assignment above (a workflow rule might e.g. notify a
    # Manager on any Hot lead, which is a separate concern from assignment).
    dispatch_event(
        db, event="lead_scored", entity_type="leads", entity_id=lead.id,
        context={"score": score, "score_band": band, "owner_id": lead.assigned_to},
    )
