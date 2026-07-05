"""
In-app notification creation.

Traces to: BR-22, FR-62, FR-63. Module 6 (Workflow Automation)
infrastructure -- exists to back the send_notification workflow action,
not a standalone module.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session, *, user_id: uuid.UUID, message: str,
    link_entity_type: str | None = None, link_entity_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id, message=message,
        link_entity_type=link_entity_type, link_entity_id=link_entity_id,
    )
    db.add(notification)
    db.flush()
    return notification
