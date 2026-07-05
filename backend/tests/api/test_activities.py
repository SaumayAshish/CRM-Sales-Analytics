"""
Activity endpoint integration tests.

Traces to: FR-23 (orphan prevention), FR-27 (ownership enforcement).
"""
from app.models.lead import Lead
from tests.conftest import auth_header, make_user


def test_create_activity_without_related_entity_returns_422(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.post(
        "/api/v1/activities", json={"type_id": str(reference_data["activity_type"].id), "notes": "orphan"}, headers=headers
    )

    assert response.status_code == 422


def test_create_activity_against_own_lead_succeeds(client, db, reference_data):
    rep = make_user(db, reference_data["roles"]["Rep"].id, email="rep2@example.com")
    lead = Lead(
        first_name="A", last_name="B", company="C", email="a@b.com",
        source_id=reference_data["source"].id, assigned_to=rep.id,
    )
    db.add(lead)
    db.commit()
    headers = auth_header(client, "rep2@example.com")

    response = client.post(
        "/api/v1/activities",
        json={"type_id": str(reference_data["activity_type"].id), "lead_id": str(lead.id), "notes": "Called"},
        headers=headers,
    )

    assert response.status_code == 201


def test_rep_cannot_log_activity_against_others_lead(client, db, reference_data):
    owner_rep = make_user(db, reference_data["roles"]["Rep"].id, email="owner@example.com")
    make_user(db, reference_data["roles"]["Rep"].id, email="other@example.com")
    lead = Lead(
        first_name="A", last_name="B", company="C", email="c@d.com",
        source_id=reference_data["source"].id, assigned_to=owner_rep.id,
    )
    db.add(lead)
    db.commit()
    headers = auth_header(client, "other@example.com")

    response = client.post(
        "/api/v1/activities",
        json={"type_id": str(reference_data["activity_type"].id), "lead_id": str(lead.id), "notes": "Called"},
        headers=headers,
    )

    assert response.status_code == 403
