"""
Workflow automation engine integration tests (event -> condition -> action).

Traces to: FR-58, FR-59, FR-60, FR-61, BR-22.
"""
from app.models.notification import Notification
from app.models.workflow import ScoringCriteria, ScoringRule, WorkflowExecutionLog, WorkflowRule
from tests.conftest import auth_header, make_user


def test_hot_lead_triggers_notification_workflow(client, db, reference_data):
    make_user(db, reference_data["roles"]["Admin"].id, email="admin@example.com")
    rep = make_user(db, reference_data["roles"]["Rep"].id, email="rep@example.com")

    scoring_rule = ScoringRule(name="Test Scoring", is_active=True, hot_threshold=70, warm_threshold=40)
    db.add(scoring_rule)
    db.flush()
    db.add(
        ScoringCriteria(
            scoring_rule_id=scoring_rule.id, field_name="source", operator="equals",
            comparison_value=reference_data["source"].name, weight=90,
        )
    )

    workflow_rule = WorkflowRule(
        name="Notify Admin on Hot Lead", trigger_event="lead_scored", is_active=True,
        conditions=[{"field": "score_band", "operator": "equals", "value": "Hot"}],
        actions=[{"type": "send_notification", "params": {"message": "A lead just went Hot!"}}],
    )
    db.add(workflow_rule)
    db.commit()

    headers = auth_header(client, "rep@example.com")
    response = client.post(
        "/api/v1/leads",
        json={
            "first_name": "Dana", "last_name": "Whitfield", "company": "Ferrocore",
            "email": "dana@ferrocore.com", "source_id": str(reference_data["source"].id),
        },
        headers=headers,
    )
    assert response.status_code == 201
    lead_body = response.json()
    assert lead_body["score_band"] == "Hot"
    assert lead_body["assigned_to"] == str(rep.id)  # only active Rep -> least-loaded picks them

    # send_notification's context.owner_id resolves to the newly-assigned rep.
    notification = db.query(Notification).filter(Notification.user_id == rep.id).first()
    assert notification is not None
    assert "Hot" in notification.message

    execution = db.query(WorkflowExecutionLog).filter(WorkflowExecutionLog.workflow_rule_id == workflow_rule.id).first()
    assert execution is not None
    assert execution.matched is True


def test_workflow_rule_toggle_disables_evaluation(client, db, reference_data):
    make_user(db, reference_data["roles"]["Admin"].id, email="admin2@example.com")
    headers = auth_header(client, "admin2@example.com")

    create_response = client.post(
        "/api/v1/workflows",
        json={
            "name": "Test Rule", "trigger_event": "lead_created", "is_active": True,
            "conditions": [], "actions": [{"type": "trigger_webhook", "params": {"url": "https://example.com"}}],
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    rule_id = create_response.json()["id"]

    toggle_response = client.patch(f"/api/v1/workflows/{rule_id}/toggle", headers=headers)
    assert toggle_response.status_code == 200
    assert toggle_response.json()["is_active"] is False


def test_non_matching_condition_logged_as_unmatched(client, db, reference_data):
    make_user(db, reference_data["roles"]["Rep"].id, email="rep2@example.com")

    workflow_rule = WorkflowRule(
        name="Never Matches", trigger_event="lead_created", is_active=True,
        conditions=[{"field": "score_band", "operator": "equals", "value": "Hot"}],
        actions=[{"type": "trigger_webhook", "params": {}}],
    )
    db.add(workflow_rule)
    db.commit()

    headers = auth_header(client, "rep2@example.com")
    response = client.post(
        "/api/v1/leads",
        json={
            "first_name": "A", "last_name": "B", "company": "C", "email": "c@d.com",
            "source_id": str(reference_data["source"].id),
        },
        headers=headers,
    )
    assert response.status_code == 201

    execution = db.query(WorkflowExecutionLog).filter(WorkflowExecutionLog.workflow_rule_id == workflow_rule.id).first()
    assert execution is not None
    assert execution.matched is False
