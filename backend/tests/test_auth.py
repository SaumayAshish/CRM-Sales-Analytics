"""
Auth unit tests.

Traces to: FR-38 (login issues role-bearing JWT), FR-43 (refresh + logout
revocation), UAT-33 equivalent (unauthenticated/invalid credential handling).
"""
from tests.conftest import make_user


def test_login_success(client, db, reference_data):
    make_user(db, reference_data["roles"]["Admin"].id, email="admin@example.com")
    db.commit()

    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "TestPass123!"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body and "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, db, reference_data):
    make_user(db, reference_data["roles"]["Admin"].id, email="admin2@example.com")
    db.commit()

    response = client.post("/api/v1/auth/login", json={"email": "admin2@example.com", "password": "WrongPass!"})

    assert response.status_code == 401


def test_login_inactive_user_rejected(client, db, reference_data):
    user = make_user(db, reference_data["roles"]["Admin"].id, email="inactive@example.com")
    user.is_active = False
    db.commit()

    response = client.post("/api/v1/auth/login", json={"email": "inactive@example.com", "password": "TestPass123!"})

    assert response.status_code == 401


def test_refresh_issues_new_access_token(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")
    db.commit()
    login = client.post("/api/v1/auth/login", json={"email": "rep@example.com", "password": "TestPass123!"})
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_logout_revokes_refresh_token(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep2@example.com")
    db.commit()
    login = client.post("/api/v1/auth/login", json={"email": "rep2@example.com", "password": "TestPass123!"})
    refresh_token = login.json()["refresh_token"]

    logout_response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    reuse_response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_response.status_code == 401


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/v1/leads")
    assert response.status_code == 401
