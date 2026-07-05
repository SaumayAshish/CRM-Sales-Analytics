"""
Automatic (system-generated) activity logging.

Traces to: FR-54 (stage changes and lead conversions automatically create
a system-logged Activity entry, distinct from user-logged activities via
a null logged_by).
"""
import uuid

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.reference import ActivityType

STATUS_CHANGE_TYPE_NAME = "Status Change"


def _get_or_create_activity_type(db: Session, name: str) -> ActivityType:
    activity_type = db.query(ActivityType).filter(ActivityType.name == name).first()
    if activity_type is None:
        activity_type = ActivityType(name=name)
        db.add(activity_type)
        db.flush()
    return activity_type


def log_system_activity(
    db: Session, *, notes: str, lead_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None, opportunity_id: uuid.UUID | None = None,
) -> Activity:
    """FR-54: logged_by is left null to mark this as system-generated."""
    activity_type = _get_or_create_activity_type(db, STATUS_CHANGE_TYPE_NAME)
    activity = Activity(
        type_id=activity_type.id, logged_by=None, lead_id=lead_id,
        account_id=account_id, opportunity_id=opportunity_id, notes=notes, is_complete=True,
    )
    db.add(activity)
    db.flush()
    return activity
