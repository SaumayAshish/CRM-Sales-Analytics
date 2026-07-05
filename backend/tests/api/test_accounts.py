"""
Account and Contact endpoint integration tests.

Traces to: FR-18, FR-19, FR-22.
"""
from app.models.account import Account, Contact
from tests.conftest import auth_header, make_user


def test_create_account_success(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.post(
        "/api/v1/accounts",
        json={"name": "Ferrocore Manufacturing", "domain": "ferrocore.com", "owner_id": str(owner.id)},
        headers=headers,
    )

    assert response.status_code == 201


def test_duplicate_domain_warns_without_override(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep2@example.com")
    db.add(Account(name="Existing Co", domain="dupe.com", owner_id=owner.id))
    db.commit()
    headers = auth_header(client, "rep2@example.com")

    response = client.post(
        "/api/v1/accounts", json={"name": "New Co", "domain": "dupe.com", "owner_id": str(owner.id)}, headers=headers
    )

    assert response.status_code == 409


def test_duplicate_domain_override_requires_reason(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep3@example.com")
    db.add(Account(name="Existing Co", domain="dupe2.com", owner_id=owner.id))
    db.commit()
    headers = auth_header(client, "rep3@example.com")

    response = client.post(
        "/api/v1/accounts",
        json={
            "name": "New Co", "domain": "dupe2.com", "owner_id": str(owner.id),
            "override_duplicate_warning": True,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_setting_primary_contact_unflags_previous(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="rep4@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.flush()
    original_primary = Contact(
        account_id=account.id, first_name="A", last_name="B", email="a@b.com", is_primary=True
    )
    db.add(original_primary)
    db.commit()
    headers = auth_header(client, "rep4@example.com")

    response = client.post(
        "/api/v1/contacts",
        json={"account_id": str(account.id), "first_name": "C", "last_name": "D", "email": "c@d.com", "is_primary": True},
        headers=headers,
    )

    assert response.status_code == 201
    db.refresh(original_primary)
    assert original_primary.is_primary is False


def test_rep_cannot_view_other_reps_account(client, db, reference_data):
    owner = make_user(db, reference_data["roles"]["Rep"].id, email="owner@example.com")
    make_user(db, reference_data["roles"]["Rep"].id, email="other@example.com")
    account = Account(name="Ferrocore", owner_id=owner.id)
    db.add(account)
    db.commit()
    headers = auth_header(client, "other@example.com")

    response = client.get(f"/api/v1/accounts/{account.id}", headers=headers)

    assert response.status_code == 403
