"""
Cross-cutting audit log writer.

Traces to: BR-14 (every create/update/delete on core entities produces an
immutable audit entry), BR-15 (no route ever exposes update/delete on
audit_logs), FR-40, FR-41, FR-36 (system/automated actions record a null
actor_id, distinguishing them from human actions -- used starting Phase 3's
workflow engine, not exercised by Phase 2's plain CRUD).
"""
import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


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
    )
    db.add(entry)
    return entry
