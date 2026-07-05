"""
Lead scoring engine unit tests, one per rule-type family (FR-50).
"""
from datetime import datetime, timedelta, timezone

from app.models.activity import Activity
from app.models.lead import Lead
from app.models.reference import LeadSource
from app.models.workflow import ScoringCriteria, ScoringRule
from app.services.scoring_engine import evaluate_lead_score


def _make_rule(db, hot=70, warm=40):
    rule = ScoringRule(name="Test Rule", is_active=True, hot_threshold=hot, warm_threshold=warm)
    db.add(rule)
    db.flush()
    return rule


def test_attribute_based_source_criterion(db):
    source = LeadSource(name="Referral")
    db.add(source)
    db.flush()
    rule = _make_rule(db)
    db.add(ScoringCriteria(scoring_rule_id=rule.id, field_name="source", operator="equals", comparison_value="Referral", weight=15))
    db.flush()

    lead = Lead(first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id)
    db.add(lead)
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == 15
    assert band == "Cold"
    assert len(matched) == 1


def test_attribute_based_company_size_criterion(db):
    source = LeadSource(name="Web Form")
    db.add(source)
    db.flush()
    rule = _make_rule(db)
    db.add(ScoringCriteria(scoring_rule_id=rule.id, field_name="company_size", operator="greater_than", comparison_value="500", weight=20))
    db.flush()

    lead = Lead(
        first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id,
        custom_fields={"company_size": 1000},
    )
    db.add(lead)
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == 20
    assert matched[0]["field_name"] == "company_size"


def test_behavior_based_activity_type_criterion(db, reference_data):
    source = LeadSource(name="Web Form 2")
    db.add(source)
    db.flush()
    rule = _make_rule(db)
    db.add(ScoringCriteria(scoring_rule_id=rule.id, field_name="activity_type_exists", operator="equals", comparison_value="Call", weight=25))
    db.flush()

    lead = Lead(first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id)
    db.add(lead)
    db.flush()
    db.add(Activity(type_id=reference_data["activity_type"].id, lead_id=lead.id, notes="Demo call"))
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == 25


def test_recency_based_criterion(db, reference_data):
    source = LeadSource(name="Web Form 3")
    db.add(source)
    db.flush()
    rule = _make_rule(db)
    db.add(
        ScoringCriteria(
            scoring_rule_id=rule.id, field_name="activity_recency_days", operator="less_than_or_equal",
            comparison_value="7", weight=10,
        )
    )
    db.flush()

    lead = Lead(first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id)
    db.add(lead)
    db.flush()
    recent_activity = Activity(
        type_id=reference_data["activity_type"].id, lead_id=lead.id, notes="recent",
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    db.add(recent_activity)
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == 10


def test_negative_signal_no_response_criterion(db):
    source = LeadSource(name="Web Form 4")
    db.add(source)
    db.flush()
    rule = _make_rule(db)
    db.add(
        ScoringCriteria(
            scoring_rule_id=rule.id, field_name="no_response_days", operator="greater_than_or_equal",
            comparison_value="30", weight=-20,
        )
    )
    db.flush()

    lead = Lead(
        first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id,
        created_at=datetime.now(timezone.utc) - timedelta(days=45),
    )
    db.add(lead)
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == -20


def test_score_band_thresholds(db):
    source = LeadSource(name="Web Form 5")
    db.add(source)
    db.flush()
    rule = _make_rule(db, hot=70, warm=40)
    db.add(ScoringCriteria(scoring_rule_id=rule.id, field_name="source", operator="equals", comparison_value="Web Form 5", weight=80))
    db.flush()

    lead = Lead(first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id)
    db.add(lead)
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == 80
    assert band == "Hot"


def test_no_active_rule_returns_zero_cold(db):
    source = LeadSource(name="Web Form 6")
    db.add(source)
    db.flush()
    lead = Lead(first_name="A", last_name="B", company="C", email="a@b.com", source_id=source.id)
    db.add(lead)
    db.flush()

    score, band, matched, rule_id = evaluate_lead_score(db, lead)
    assert score == 0
    assert band == "Cold"
    assert rule_id is None
