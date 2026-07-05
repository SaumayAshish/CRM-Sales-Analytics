"""
Workflow automation engine: event -> condition -> action, evaluated
synchronously in-process (no Celery/background worker, per Phase 3
kickoff decision -- explicitly deferred to a future phase if ever needed).

Traces to: BR-18, BR-22, FR-58, FR-59, FR-60, FR-61.

Plain-English summary: when a named event happens (e.g. "lead_scored"),
every active workflow_rule registered for that event is checked. A rule's
`conditions` (a list of {field, operator, value}) are evaluated against a
small context dict describing the event; if every condition matches, the
rule's `actions` (a list of {type, params}) run in order. Every evaluation
attempt -- matched or not -- is recorded in workflow_execution_log so
Admin can see why a rule did or didn't fire (FR-61).
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.reference import ActivityType
from app.models.workflow import WorkflowExecutionLog, WorkflowRule
from app.services.assignment_engine import assign_lead_to_rep
from app.services.notification_service import create_notification

_ENTITY_MODELS = {"leads": Lead, "opportunities": Opportunity}


def _condition_matches(context: dict[str, Any], condition: dict[str, Any]) -> bool:
    actual = context.get(condition["field"])
    if actual is None:
        return False
    operator = condition["operator"]
    expected = condition["value"]
    try:
        actual_num, expected_num = float(actual), float(expected)
        if operator == "greater_than":
            return actual_num > expected_num
        if operator == "greater_than_or_equal":
            return actual_num >= expected_num
        if operator == "less_than":
            return actual_num < expected_num
        if operator == "less_than_or_equal":
            return actual_num <= expected_num
        if operator == "equals":
            return actual_num == expected_num
    except (TypeError, ValueError):
        pass
    if operator == "equals":
        return str(actual) == str(expected)
    return False


def _execute_action(
    db: Session, action: dict[str, Any], *, entity_type: str, entity_id: uuid.UUID, context: dict[str, Any],
) -> dict[str, Any]:
    action_type = action["type"]
    params = action.get("params", {})
    entity_model = _ENTITY_MODELS.get(entity_type)
    entity = db.query(entity_model).filter(entity_model.id == entity_id).first() if entity_model else None

    if action_type == "assign_owner" and isinstance(entity, Lead):
        rep = assign_lead_to_rep(db)
        if rep is not None:
            entity.assigned_to = rep.id
            return {"type": action_type, "assigned_to": str(rep.id)}
        return {"type": action_type, "assigned_to": None, "reason": "no active Rep available"}

    if action_type == "send_notification":
        target_user_id = context.get("owner_id") or params.get("user_id")
        if target_user_id:
            create_notification(
                db, user_id=target_user_id, message=params.get("message", "A workflow rule triggered a notification."),
                link_entity_type=entity_type, link_entity_id=entity_id,
            )
            return {"type": action_type, "notified_user_id": str(target_user_id)}
        return {"type": action_type, "notified_user_id": None, "reason": "no target user resolvable"}

    if action_type == "update_field" and entity is not None:
        field_name = params.get("field")
        value = params.get("value")
        if field_name and hasattr(entity, field_name):
            setattr(entity, field_name, value)
            return {"type": action_type, "field": field_name, "value": value}
        return {"type": action_type, "field": field_name, "reason": "field not settable on entity"}

    if action_type == "create_task":
        task_type = db.query(ActivityType).filter(ActivityType.name == "Task").first()
        if task_type is not None:
            due_in_days = int(params.get("due_in_days", 1))
            kwargs = {"lead_id": entity_id} if entity_type == "leads" else {"opportunity_id": entity_id}
            task = Activity(
                type_id=task_type.id, logged_by=None, notes=params.get("notes", "Workflow-generated task"),
                due_at=datetime.now(timezone.utc) + timedelta(days=due_in_days), **kwargs,
            )
            db.add(task)
            db.flush()
            return {"type": action_type, "task_id": str(task.id)}
        return {"type": action_type, "reason": "Task activity type not configured"}

    if action_type == "trigger_webhook":
        # FR-60: explicitly stubbed -- log the payload, no outbound HTTP call.
        return {"type": action_type, "stub": True, "payload": params}

    return {"type": action_type, "reason": "unsupported action type"}


def dispatch_event(
    db: Session, *, event: str, entity_type: str, entity_id: uuid.UUID, context: dict[str, Any],
) -> None:
    """FR-58/FR-59: evaluate every active rule registered for `event`."""
    rules = db.query(WorkflowRule).filter(WorkflowRule.trigger_event == event, WorkflowRule.is_active.is_(True)).all()

    for rule in rules:
        matched = all(_condition_matches(context, c) for c in (rule.conditions or []))
        actions_taken = []
        if matched:
            for action in rule.actions or []:
                actions_taken.append(
                    _execute_action(db, action, entity_type=entity_type, entity_id=entity_id, context=context)
                )

        db.add(
            WorkflowExecutionLog(
                workflow_rule_id=rule.id, triggering_event=event, entity_type=entity_type,
                entity_id=entity_id, matched=matched, actions_taken=actions_taken or None,
            )
        )
