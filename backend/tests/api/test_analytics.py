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


def test_rep_performance_scoped_to_own_row_for_rep(client, db, reference_data):
    """BR-23/KPI_Catalog.md: a Rep may see quota attainment, but only their
    own row, not the whole team's."""
    rep = make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    other_rep = make_user(db, reference_data["roles"]["Rep"].id, email="other_rep@example.com")
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.get("/api/v1/analytics/rep-performance", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user_id"] == str(rep.id)
    assert str(other_rep.id) not in [row["user_id"] for row in body]


def test_rep_performance_visible_to_manager_and_admin(client, db, reference_data):
    make_user(db, reference_data["roles"]["Manager"].id, email="mgr@example.com")
    db.commit()
    headers = auth_header(client, "mgr@example.com")

    response = client.get("/api/v1/analytics/rep-performance", headers=headers)

    assert response.status_code == 200


def test_rep_performance_scoped_to_own_team_for_manager(client, db, reference_data):
    """BR-11: a Manager sees only their own team's reps, not every region.

    Regression test for a real bug found via live UAT-30 execution: the
    endpoint previously ignored team_id entirely and returned every rep
    system-wide to any Manager, a cross-region data exposure.
    """
    from app.models.reference import Team

    other_team = Team(name="East Region Sales", region="East")
    db.add(other_team)
    db.flush()

    manager = make_user(
        db, reference_data["roles"]["Manager"].id, team_id=reference_data["team"].id, email="west_mgr@example.com"
    )
    own_team_rep = make_user(
        db, reference_data["roles"]["Rep"].id, team_id=reference_data["team"].id, email="west_rep@example.com"
    )
    other_team_rep = make_user(
        db, reference_data["roles"]["Rep"].id, team_id=other_team.id, email="east_rep@example.com"
    )
    db.commit()
    headers = auth_header(client, "west_mgr@example.com")

    response = client.get("/api/v1/analytics/rep-performance", headers=headers)

    assert response.status_code == 200
    user_ids = [row["user_id"] for row in response.json()]
    assert str(manager.id) in user_ids
    assert str(own_team_rep.id) in user_ids
    assert str(other_team_rep.id) not in user_ids
