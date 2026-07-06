"""
Opportunity endpoint integration tests.

Traces to: FR-09, FR-12, FR-13, FR-14, FR-15, BR-17.
"""
import uuid

from app.models.account import Account
from app.models.opportunity import Opportunity
from tests.conftest import auth_header, make_user


def _stage(reference_data, name):
    return next(s for s in reference_data["stages"] if s.name == name)


def test_create_opportunity_requires_valid_stage(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.post(
        "/api/v1/opportunities",
        json={
            "name": "Deal", "account_id": str(account.id), "owner_id": str(owner.id),
            "stage_id": str(uuid.uuid4()), "amount": 1000, "probability": 0.1,
            "expected_close_date": "2026-12-01",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_opportunity_missing_account_returns_422(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep2@example.com")
    db.commit()
    headers = auth_header(client, "rep2@example.com")

    response = client.post(
        "/api/v1/opportunities",
        json={"name": "Deal", "owner_id": str(uuid.uuid4()), "stage_id": str(_stage(reference_data, "Qualification").id),
              "amount": 1000, "probability": 0.1, "expected_close_date": "2026-12-01"},
        headers=headers,
    )

    assert response.status_code == 422


def test_closed_lost_requires_loss_reason(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep3@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()
    opp = Opportunity(
        name="Deal", account_id=account.id, owner_id=owner.id, stage_id=_stage(reference_data, "Qualification").id,
        amount=1000, probability=0.1, expected_close_date="2026-12-01",
    )
    db.add(opp)
    db.commit()
    headers = auth_header(client, "rep3@example.com")

    response = client.post(
        f"/api/v1/opportunities/{opp.id}/advance-stage",
        json={"stage_id": str(_stage(reference_data, "Closed Lost").id)},
        headers=headers,
    )

    assert response.status_code == 422


def test_closed_lost_with_reason_succeeds_and_locks_record(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep4@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()
    opp = Opportunity(
        name="Deal", account_id=account.id, owner_id=owner.id, stage_id=_stage(reference_data, "Qualification").id,
        amount=1000, probability=0.1, expected_close_date="2026-12-01",
    )
    db.add(opp)
    db.commit()
    headers = auth_header(client, "rep4@example.com")

    response = client.post(
        f"/api/v1/opportunities/{opp.id}/advance-stage",
        json={"stage_id": str(_stage(reference_data, "Closed Lost").id), "loss_reason_id": str(reference_data["loss_reason"].id)},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["closed_at"] is not None

    # Manager cannot change stage on a now-closed opportunity without Admin override.
    make_user(db, reference_data["roles"]["Manager"].id, email="mgr@example.com")
    mgr_headers = auth_header(client, "mgr@example.com")
    reopen_attempt = client.post(
        f"/api/v1/opportunities/{opp.id}/advance-stage",
        json={"stage_id": str(_stage(reference_data, "Qualification").id)},
        headers=mgr_headers,
    )
    assert reopen_attempt.status_code == 403


def test_admin_can_reopen_closed_opportunity_with_reason(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep5@example.com")
    make_user(db, reference_data["roles"]["Admin"].id, email="admin@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()
    opp = Opportunity(
        name="Deal", account_id=account.id, owner_id=owner.id, stage_id=_stage(reference_data, "Closed Won").id,
        amount=1000, probability=1.0, expected_close_date="2026-12-01", closed_at="2026-06-01T00:00:00Z",
    )
    db.add(opp)
    db.commit()
    headers = auth_header(client, "admin@example.com")

    no_reason = client.post(
        f"/api/v1/opportunities/{opp.id}/advance-stage",
        json={"stage_id": str(_stage(reference_data, "Qualification").id)}, headers=headers,
    )
    assert no_reason.status_code == 422

    with_reason = client.post(
        f"/api/v1/opportunities/{opp.id}/advance-stage",
        json={"stage_id": str(_stage(reference_data, "Qualification").id), "override_reason": "Data entry error"},
        headers=headers,
    )
    assert with_reason.status_code == 200
    assert with_reason.json()["closed_at"] is None


def test_weighted_value_computed(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep6@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()
    opp = Opportunity(
        name="Deal", account_id=account.id, owner_id=owner.id, stage_id=_stage(reference_data, "Needs Analysis").id,
        amount=50000, probability=0.3, expected_close_date="2026-12-01",
    )
    db.add(opp)
    db.commit()
    headers = auth_header(client, "rep6@example.com")

    response = client.get(f"/api/v1/opportunities/{opp.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["weighted_value"] == 15000.0


def test_page_size_above_old_200_cap_returns_everything(client, db, reference_data):
    """Regression test for a bug found via live Kanban testing (Phase 6):
    the old le=200 cap silently truncated the board's single-page fetch
    once total opportunities exceeded 200, undercounting per-stage totals.
    """
    owner = make_user(db, reference_data["roles"]["Admin"].id, email="admin2@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()
    stage = _stage(reference_data, "Qualification")
    for i in range(210):
        db.add(
            Opportunity(
                name=f"Deal {i}", account_id=account.id, owner_id=owner.id, stage_id=stage.id,
                amount=1000, probability=0.1, expected_close_date="2026-12-01",
            )
        )
    db.commit()
    headers = auth_header(client, "admin2@example.com")

    response = client.get("/api/v1/opportunities?page_size=250", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 210
