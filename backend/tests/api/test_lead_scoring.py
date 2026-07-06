"""
Lead scoring rule endpoint tests.

Traces to: FR-34. Regression test for a real gap found via live UAT-31/32
execution: create_scoring_rule's own docstring described an Admin
deactivating an old rule via PATCH, but no such endpoint existed anywhere.
"""
from app.models.workflow import ScoringRule
from tests.conftest import auth_header, make_user


def test_toggle_scoring_rule_disables_it(client, db, reference_data):
    rule = ScoringRule(name="Test Rule", hot_threshold=70, warm_threshold=40, is_active=True)
    db.add(rule)
    db.commit()
    make_user(db, reference_data["roles"]["Admin"].id, email="admin_scoring@example.com")
    headers = auth_header(client, "admin_scoring@example.com")

    response = client.patch(f"/api/v1/lead-scoring/rules/{rule.id}/toggle", headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_non_admin_cannot_toggle_scoring_rule(client, db, reference_data):
    rule = ScoringRule(name="Test Rule", hot_threshold=70, warm_threshold=40, is_active=True)
    db.add(rule)
    db.commit()
    make_user(db, reference_data["roles"]["Manager"].id, email="mgr_scoring@example.com")
    headers = auth_header(client, "mgr_scoring@example.com")

    response = client.patch(f"/api/v1/lead-scoring/rules/{rule.id}/toggle", headers=headers)

    assert response.status_code == 403
