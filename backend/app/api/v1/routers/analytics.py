"""
Analytics / aggregation endpoints, Power BI-ready.

Traces to: FR-64, KPI_Catalog.md. Each endpoint is backed by a SQL view
(migration 0004) so the same query Power BI would run against the database
is exactly what the API returns -- no separate aggregation logic to drift
out of sync with the dashboard layer (mirrors UAT-28's dashboard-vs-SQL
parity check).
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, CurrentUser, require_role
from app.db.session import get_db

router = APIRouter()


def _rows_as_dicts(db: Session, query: str) -> list[dict]:
    result = db.execute(text(query))
    return [dict(row._mapping) for row in result]


@router.get("/pipeline-summary")
def pipeline_summary(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER]))
) -> list[dict]:
    return _rows_as_dicts(db, "SELECT * FROM vw_pipeline_summary")


@router.get("/rep-performance")
def rep_performance(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER]))
) -> list[dict]:
    return _rows_as_dicts(db, "SELECT * FROM vw_rep_performance")


@router.get("/lead-funnel")
def lead_funnel(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER]))
) -> list[dict]:
    return _rows_as_dicts(db, "SELECT * FROM vw_lead_funnel")


@router.get("/forecast")
def forecast(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER]))
) -> list[dict]:
    return _rows_as_dicts(db, "SELECT * FROM vw_forecast")


@router.get("/kpis")
def kpis(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER]))
) -> dict:
    """A representative subset of KPI_Catalog.md's 23 KPIs, computed
    directly from the same views/tables Power BI would query. Quota-based
    KPIs are omitted (see migration 0004 docstring)."""
    pipeline = _rows_as_dicts(db, "SELECT SUM(total_value) AS total, SUM(weighted_value) AS weighted FROM vw_pipeline_summary")[0]
    funnel = _rows_as_dicts(
        db,
        """
        SELECT
            SUM(lead_count) AS total_leads,
            SUM(converted_count) AS total_converted
        FROM vw_lead_funnel
        """,
    )[0]
    win_rate_row = _rows_as_dicts(
        db,
        """
        SELECT
            SUM(won_count) AS won, SUM(lost_count) AS lost, SUM(closed_won_revenue) AS revenue
        FROM vw_rep_performance
        """,
    )[0]

    total_leads = funnel["total_leads"] or 0
    total_converted = funnel["total_converted"] or 0
    won = win_rate_row["won"] or 0
    lost = win_rate_row["lost"] or 0
    decided = won + lost

    return {
        "total_open_pipeline_value": float(pipeline["total"] or 0),
        "weighted_pipeline_value": float(pipeline["weighted"] or 0),
        "lead_to_conversion_rate": round(total_converted / total_leads, 4) if total_leads else 0,
        "win_rate": round(won / decided, 4) if decided else 0,
        "revenue_closed_won": float(win_rate_row["revenue"] or 0),
    }
