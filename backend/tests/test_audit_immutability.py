"""
Audit log DB-level immutability test.

Traces to: BR-15, FR-56. The Postgres trigger (migration 0002) must reject
UPDATE/DELETE even when issued directly via SQL, bypassing the API/ORM
layer entirely -- this is the whole point of a DB-level, not just
app-level, guarantee.
"""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import InternalError

from app.models.audit import AuditLog


def test_direct_sql_update_rejected_by_trigger(db):
    entry = AuditLog(actor_id=None, action="CREATE", entity_type="leads", entity_id=uuid.uuid4())
    db.add(entry)
    db.flush()

    with pytest.raises(InternalError):
        db.execute(text("UPDATE audit_logs SET action = 'HACKED' WHERE id = :id"), {"id": str(entry.id)})
        db.flush()


def test_direct_sql_delete_rejected_by_trigger(db):
    entry = AuditLog(actor_id=None, action="CREATE", entity_type="leads", entity_id=uuid.uuid4())
    db.add(entry)
    db.flush()

    with pytest.raises(InternalError):
        db.execute(text("DELETE FROM audit_logs WHERE id = :id"), {"id": str(entry.id)})
        db.flush()
