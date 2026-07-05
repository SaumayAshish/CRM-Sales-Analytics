"""
User management endpoint integration tests.

Traces to: FR-42, FR-45.
"""
from tests.conftest import auth_header, make_user


def test_only_admin_can_create_user(client, db, reference_data):
    make_user(db, reference_data["roles"]["Manager"].id, email="mgr@example.com")
    db.commit()
    headers = auth_header(client, "mgr@example.com")

    response = client.post(
        "/api/v1/users",
        json={
            "email": "newrep@example.com", "password": "SomePass123!", "first_name": "New",
            "last_name": "Rep", "role_id": str(reference_data["roles"]["Rep"].id),
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_admin_can_create_and_deactivate_user(client, db, reference_data):
    make_user(db, reference_data["roles"]["Admin"].id, email="admin@example.com")
    db.commit()
    headers = auth_header(client, "admin@example.com")

    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "newrep2@example.com", "password": "SomePass123!", "first_name": "New",
            "last_name": "Rep", "role_id": str(reference_data["roles"]["Rep"].id),
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert delete_response.status_code == 204

    login_attempt = client.post("/api/v1/auth/login", json={"email": "newrep2@example.com", "password": "SomePass123!"})
    assert login_attempt.status_code == 401


def test_get_current_user_profile(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    db.commit()
    headers = auth_header(client, "rep@example.com")

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "rep@example.com"
