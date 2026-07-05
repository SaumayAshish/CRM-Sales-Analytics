"""
Account and nested Contact/Opportunity endpoints.

Traces to: FR-17 (unified 360 view via nested reads), FR-18 (single primary
contact), FR-19 (duplicate-domain warning), FR-20 (custom fields), FR-22
(search/filter).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, ROLE_REP, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.account import Account, Contact
from app.models.opportunity import Opportunity
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate, ContactRead
from app.schemas.opportunity import OpportunityRead
from app.services.audit import write_audit_log

router = APIRouter()


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Account:
    """FR-19: warn on likely duplicate by domain unless explicitly overridden."""
    if payload.domain:
        duplicate = (
            db.query(Account)
            .filter(Account.domain == payload.domain, Account.deleted_at.is_(None))
            .first()
        )
        if duplicate and not payload.override_duplicate_warning:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with domain '{payload.domain}' already exists "
                "(id={0}). Set override_duplicate_warning=true with a reason to proceed.".format(duplicate.id),
            )
        if duplicate and payload.override_duplicate_warning and not payload.override_reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="override_reason is required when overriding a duplicate-account warning.",
            )

    account = Account(
        name=payload.name, domain=payload.domain, industry=payload.industry,
        owner_id=payload.owner_id, custom_fields=payload.custom_fields,
    )
    db.add(account)
    db.flush()
    write_audit_log(
        db, actor_id=current_user.id, action="CREATE", entity_type="accounts", entity_id=account.id,
        after_state={"override_reason": payload.override_reason} if payload.override_reason else None,
    )
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[AccountRead])
def list_accounts(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    name: str | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[Account]:
    """FR-22: search/filter by name and owner, server-side paginated."""
    query = db.query(Account).filter(Account.deleted_at.is_(None))
    if current_user.role == ROLE_REP:
        query = query.filter(Account.owner_id == current_user.id)
    if name:
        query = query.filter(Account.name.ilike(f"%{name}%"))
    if owner_id:
        query = query.filter(Account.owner_id == owner_id)
    return query.offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Account:
    account = db.query(Account).filter(Account.id == account_id, Account.deleted_at.is_(None)).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if current_user.role == ROLE_REP and account.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your account")
    return account


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Account:
    account = db.query(Account).filter(Account.id == account_id, Account.deleted_at.is_(None)).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if current_user.role == ROLE_REP and account.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your account")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)

    write_audit_log(db, actor_id=current_user.id, action="UPDATE", entity_type="accounts", entity_id=account.id)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> None:
    account = db.query(Account).filter(Account.id == account_id, Account.deleted_at.is_(None)).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    account.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, actor_id=current_user.id, action="DELETE", entity_type="accounts", entity_id=account.id)
    db.commit()
    return None


@router.get("/{account_id}/contacts", response_model=list[ContactRead])
def list_account_contacts(
    account_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[Contact]:
    """FR-17: part of the unified Account 360 view."""
    return (
        db.query(Contact)
        .filter(Contact.account_id == account_id, Contact.deleted_at.is_(None))
        .all()
    )


@router.get("/{account_id}/opportunities", response_model=list[OpportunityRead])
def list_account_opportunities(
    account_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict]:
    """FR-17: part of the unified Account 360 view; weighted_value computed per FR-15."""
    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.account_id == account_id, Opportunity.deleted_at.is_(None))
        .all()
    )
    return [
        {**o.__dict__, "weighted_value": float(o.amount) * float(o.probability)} for o in opportunities
    ]
