"""
Contact endpoints.

Traces to: FR-18 (single primary contact per account), FR-22 (search/filter).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, ROLE_REP, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.account import Contact
from app.schemas.account import ContactCreate, ContactRead, ContactUpdate
from app.services.audit import field_snapshot, write_audit_log

router = APIRouter()


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Contact:
    """FR-18: setting is_primary=true un-flags the account's previous primary contact."""
    if payload.is_primary:
        db.query(Contact).filter(
            Contact.account_id == payload.account_id, Contact.is_primary.is_(True)
        ).update({"is_primary": False})

    contact = Contact(**payload.model_dump())
    db.add(contact)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="contacts", entity_id=contact.id)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("", response_model=list[ContactRead])
def list_contacts(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    account_id: uuid.UUID | None = Query(None),
    email: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[Contact]:
    """FR-22: paginated, filterable by account and email."""
    query = db.query(Contact).filter(Contact.deleted_at.is_(None))
    if account_id:
        query = query.filter(Contact.account_id == account_id)
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> Contact:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: uuid.UUID,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Contact:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    if payload.is_primary:
        db.query(Contact).filter(
            Contact.account_id == contact.account_id, Contact.is_primary.is_(True), Contact.id != contact.id
        ).update({"is_primary": False})

    changed_fields = list(payload.model_dump(exclude_unset=True).keys())
    before_state = field_snapshot(contact, changed_fields)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)

    write_audit_log(
        db, actor_id=current_user.id, action="UPDATE", entity_type="contacts", entity_id=contact.id,
        before_state=before_state, after_state=field_snapshot(contact, changed_fields),
    )
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> None:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at.is_(None)).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    contact.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, actor_id=current_user.id, action="DELETE", entity_type="contacts", entity_id=contact.id)
    db.commit()
    return None
