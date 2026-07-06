"""
Company target endpoint tests -- RBAC (Admin-only write) and the
get-or-create-current-quarter behavior.

Traces to: BR-24, FR-66.
"""
from tests.conftest import auth_header, make_user


def test_get_current_target_returns_the_current_quarter_row(client, db, reference_data):
    """Migration 0011 seeds a row for the quarter it runs in, so every test
    DB (built from real migrations, not just Base.metadata.create_all())
    already has a current-quarter row -- this just confirms the endpoint
    surfaces it rather than erroring or returning a blank default."""
    make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    headers = auth_header(client, "rep@example.com")

    response = client.get("/api/v1/company-targets/current", headers=headers)
    assert response.status_code == 200
    assert response.json()["target_amount"] > 0


def test_non_admin_cannot_update_target(client, db, reference_data):
    make_user(db, reference_data["roles"]["Manager"].id, email="manager@example.com")
    headers = auth_header(client, "manager@example.com")

    response = client.patch(
        "/api/v1/company-targets/current", json={"target_amount": 5_000_000}, headers=headers
    )
    assert response.status_code == 403


def test_admin_can_update_target(client, db, reference_data):
    make_user(db, reference_data["roles"]["Admin"].id, email="admin@example.com")
    headers = auth_header(client, "admin@example.com")

    response = client.patch(
        "/api/v1/company-targets/current", json={"target_amount": 5_000_000}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["target_amount"] == 5_000_000.0

    get_response = client.get("/api/v1/company-targets/current", headers=headers)
    assert get_response.json()["target_amount"] == 5_000_000.0
