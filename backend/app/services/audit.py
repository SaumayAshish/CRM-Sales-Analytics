"""
Cross-cutting audit log writer.

Traces to: BR-14 (every create/update/delete on core entities produces an
immutable audit entry), BR-15 (no route ever exposes update/delete on
audit_logs), FR-40, FR-41, FR-36 (system/automated actions record a null
actor_id, distinguishing them from human actions), FR-55 (ip_address/
user_agent captured from request context where available).
"""
import datetime
import decimal
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.request_context import get_request_ip, get_request_user_agent
from app.models.audit import AuditLog


def json_safe(value: Any) -> Any:
    """Coerce a single field value into something the before/after_state
    JSONB columns can actually store -- UUID/Decimal/date/datetime aren't
    JSON-serializable as-is. Used by generic PATCH handlers to build
    before/after snapshots without each one reinventing this conversion."""
    if isinstance(value, (uuid.UUID, decimal.Decimal, datetime.date, datetime.datetime)):
        return str(value)
    return value


def field_snapshot(entity: Any, field_names: list[str]) -> dict:
    return {name: json_safe(getattr(entity, name)) for name in field_names}


def write_audit_log(
    db: Session,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    before_state: dict | None = None,
    after_state: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=get_request_ip(),
        user_agent=get_request_user_agent(),
    )
    db.add(entry)
    return entry
