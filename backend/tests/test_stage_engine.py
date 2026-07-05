"""
Pipeline stage transition engine unit tests.

Traces to: BR-21, FR-46, FR-47.
"""
import pytest
from fastapi import HTTPException

from app.models.reference import PipelineStage
from app.services.stage_engine import validate_transition


def _make_stage(db, name, sort_order, allowed_next=None):
    stage = PipelineStage(
        name=name, sort_order=sort_order, default_probability=0.1,
        allowed_next_stage_ids=allowed_next or [],
    )
    db.add(stage)
    db.flush()
    return stage


def test_valid_transition_passes(db):
    stage_a = _make_stage(db, "A", 1)
    stage_b = _make_stage(db, "B", 2)
    stage_a.allowed_next_stage_ids = [str(stage_b.id)]
    db.flush()

    validate_transition(db, current_stage=stage_a, target_stage=stage_b, is_privileged_actor=False, override_reason=None)


def test_invalid_transition_rejected_for_rep(db):
    stage_a = _make_stage(db, "A", 1)
    stage_c = _make_stage(db, "C", 3)

    with pytest.raises(HTTPException) as exc:
        validate_transition(db, current_stage=stage_a, target_stage=stage_c, is_privileged_actor=False, override_reason=None)
    assert exc.value.status_code == 422


def test_invalid_transition_manager_without_reason_rejected(db):
    stage_a = _make_stage(db, "A", 1)
    stage_c = _make_stage(db, "C", 3)

    with pytest.raises(HTTPException) as exc:
        validate_transition(db, current_stage=stage_a, target_stage=stage_c, is_privileged_actor=True, override_reason=None)
    assert exc.value.status_code == 422


def test_invalid_transition_manager_with_reason_succeeds(db):
    stage_a = _make_stage(db, "A", 1)
    stage_c = _make_stage(db, "C", 3)

    validate_transition(
        db, current_stage=stage_a, target_stage=stage_c, is_privileged_actor=True, override_reason="Deal moved fast",
    )
