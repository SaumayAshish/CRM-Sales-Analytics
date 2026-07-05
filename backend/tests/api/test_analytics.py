"""
Analytics endpoint accuracy tests -- dashboard figures vs. an independently
computed value, mirroring UAT-28's dashboard-vs-SQL parity check.

Traces to: FR-64, KPI_Catalog.md.
"""
from app.models.account import Account
from app.models.opportunity import Opportunity
from tests.conftest import auth_header, make_user


def test_pipeline_summary_matches_raw_query(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Admin"].id, email="admin@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()

    stage = next(s for s in reference_data["stages"] if s.name == "Qualification")
    db.add(
        Opportunity(
            name="Deal 1", account_id=account.id, owner_id=owner.id, stage_id=stage.id,
            amount=10000, probability=0.1, expected_close_date="2026-12-01",
        )
    )
    db.add(
        Opportunity(
            name="Deal 2", account_id=account.id, owner_id=owner.id, stage_id=stage.id,
            amount=20000, probability=0.1, expected_close_date="2026-12-01",
        )
    )
    db.commit()

    headers = auth_header(client, "admin@example.com")
    response = client.get("/api/v1/analytics/pipeline-summary", headers=headers)
    assert response.status_code == 200

    qualification_row = next(r for r in response.json() if r["stage_name"] == "Qualification")
    assert qualification_row["opportunity_count"] == 2
    assert float(qualification_row["total_value"]) == 30000.0
    assert float(qualification_row["weighted_value"]) == 3000.0


def test_rep_performance_endpoint_forbidden_for_rep(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.get("/api/v1/analytics/rep-performance", headers=headers)

    assert response.status_code == 403
