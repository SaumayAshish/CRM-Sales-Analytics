"""
Company-wide quarterly revenue target endpoints.

Traces to: BR-24, FR-66 (Pipeline Coverage Ratio). Distinct from
per-rep `users.quota` (BR-23) -- this is a single company-wide figure
per quarter, Admin-editable, feeding vw_pipeline_coverage.
"""
from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.reference import CompanyTarget
from app.schemas.company_target import CompanyTargetRead, CompanyTargetUpdate

router = APIRouter()


def _current_quarter_start() -> date:
    today = date.today()
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    return date(today.year, quarter_month, 1)


def _get_or_create_current(db: Session) -> CompanyTarget:
    """No row for a brand-new quarter yet is a real state (not an error) --
    carry the prior quarter's target forward rather than defaulting to 0,
    since a $0 target would make the coverage ratio nonsensical."""
    quarter_start = _current_quarter_start()
    target = db.query(CompanyTarget).filter(CompanyTarget.quarter_start == quarter_start).first()
    if target is not None:
        return target

    latest = db.query(CompanyTarget).order_by(CompanyTarget.quarter_start.desc()).first()
    target = CompanyTarget(
        quarter_start=quarter_start,
        target_amount=latest.target_amount if latest else 0,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.get("/current", response_model=CompanyTargetRead)
def get_current_target(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CompanyTarget:
    return _get_or_create_current(db)


@router.patch("/current", response_model=CompanyTargetRead, status_code=status.HTTP_200_OK)
def update_current_target(
    payload: CompanyTargetUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> CompanyTarget:
    target = _get_or_create_current(db)
    target.target_amount = payload.target_amount
    db.commit()
    db.refresh(target)
    return target
