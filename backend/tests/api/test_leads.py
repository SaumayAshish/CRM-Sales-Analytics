"""
Lead endpoint integration tests.

Traces to: FR-01, FR-05, FR-06, FR-07, FR-08, BR-10, BR-13, FR-40 (audit log).
"""
from app.models.audit import AuditLog
from app.models.lead import Lead
from tests.conftest import auth_header, make_user


def _lead_payload(source_id, email="lead@example.com"):
    return {
        "first_name": "Dana", "last_name": "Whitfield", "company": "Ferrocore Manufacturing",
        "email": email, "source_id": str(source_id),
    }


def test_create_lead_success(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.post("/api/v1/leads", json=_lead_payload(reference_data["source"].id), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["company"] == "Ferrocore Manufacturing"
    assert body["is_converted"] is False


def test_create_lead_writes_audit_log(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep_audit@example.com")
    db.commit()
    headers = auth_header(client, "rep_audit@example.com")

    response = client.post("/api/v1/leads", json=_lead_payload(reference_data["source"].id, "audit@example.com"), headers=headers)
    lead_id = response.json()["id"]

    entry = db.query(AuditLog).filter(AuditLog.entity_type == "leads", AuditLog.entity_id == lead_id).first()
    assert entry is not None
    assert entry.action == "CREATE"


def test_viewer_cannot_create_lead(client, db, reference_data):
    make_user(db, reference_data["roles"]["Viewer"].id, email="viewer@example.com")
    db.commit()
    headers = auth_header(client, "viewer@example.com")

    response = client.post("/api/v1/leads", json=_lead_payload(reference_data["source"].id), headers=headers)

    assert response.status_code == 403


def test_rep_cannot_reassign_lead(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep3@example.com")
    other_rep = make_user(db, reference_data["roles"]["Rep"].id, email="rep4@example.com")
    lead = Lead(first_name="A", last_name="B", company="C", email="c@d.com", source_id=reference_data["source"].id)
    db.add(lead)
    db.commit()
    headers = auth_header(client, "rep3@example.com")

    response = client.post(f"/api/v1/leads/{lead.id}/assign", json={"assigned_to": str(other_rep.id)}, headers=headers)

    assert response.status_code == 403


def test_manager_can_reassign_lead(client, db, reference_data):
    make_user(db, reference_data["roles"]["Manager"].id, email="mgr@example.com")
    rep = make_user(db, reference_data["roles"]["Rep"].id, email="rep5@example.com")
    lead = Lead(first_name="A", last_name="B", company="C", email="e@f.com", source_id=reference_data["source"].id)
    db.add(lead)
    db.commit()
    headers = auth_header(client, "mgr@example.com")

    response = client.post(f"/api/v1/leads/{lead.id}/assign", json={"assigned_to": str(rep.id)}, headers=headers)

    assert response.status_code == 200
    assert response.json()["assigned_to"] == str(rep.id)


def test_unassigned_queue_forbidden_for_rep(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep6@example.com")
    db.commit()
    headers = auth_header(client, "rep6@example.com")

    response = client.get("/api/v1/leads?status_unassigned=true", headers=headers)

    assert response.status_code == 403


def test_unassigned_queue_visible_to_manager(client, db, reference_data):
    make_user(db, reference_data["roles"]["Manager"].id, email="mgr2@example.com")
    lead = Lead(first_name="A", last_name="B", company="C", email="g@h.com", source_id=reference_data["source"].id)
    db.add(lead)
    db.commit()
    headers = auth_header(client, "mgr2@example.com")

    response = client.get("/api/v1/leads?status_unassigned=true", headers=headers)

    assert response.status_code == 200
    assert any(item["id"] == str(lead.id) for item in response.json())


def test_convert_lead_creates_account_contact_opportunity(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep7@example.com")
    lead = Lead(first_name="Dana", last_name="Whitfield", company="Ferrocore", email="dana@ferrocore.com", source_id=reference_data["source"].id)
    db.add(lead)
    db.commit()
    headers = auth_header(client, "rep7@example.com")

    response = client.post(f"/api/v1/leads/{lead.id}/convert", headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["account_id"] and body["contact_id"] and body["opportunity_id"]

    db.refresh(lead)
    assert lead.is_converted is True


def test_convert_already_converted_lead_returns_409(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep8@example.com")
    lead = Lead(
        first_name="Dana", last_name="Whitfield", company="Ferrocore", email="dana2@ferrocore.com",
        source_id=reference_data["source"].id, is_converted=True,
    )
    db.add(lead)
    db.commit()
    headers = auth_header(client, "rep8@example.com")

    response = client.post(f"/api/v1/leads/{lead.id}/convert", headers=headers)

    assert response.status_code == 409
