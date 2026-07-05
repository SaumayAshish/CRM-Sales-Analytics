"""
Lead auto-assignment engine.

Traces to: BR-03, FR-04, FR-52, FR-35, FR-59. Runs when a lead's score
crosses into the Hot band. Plain-English summary: pick an active Rep and
assign the lead to them, using whichever strategy the active
assignment_rule names. "least_loaded" (the Phase 3 default, per the
Phase 3 kickoff decision) picks the Rep with the fewest currently-open
assigned leads; "round_robin" cycles through Reps in a fixed order. Both
are deterministic given the same roster and lead queue (FR-35's
reproducibility requirement).
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.models.reference import Role
from app.models.user import User
from app.models.workflow import AssignmentRule


def _active_reps(db: Session) -> list[User]:
    rep_role = db.query(Role).filter(Role.name == "Rep").first()
    if rep_role is None:
        return []
    return (
        db.query(User)
        .filter(User.role_id == rep_role.id, User.is_active.is_(True), User.deleted_at.is_(None))
        .order_by(User.created_at.asc())
        .all()
    )


def _least_loaded_rep(db: Session, reps: list[User]) -> User | None:
    if not reps:
        return None
    rep_ids = [r.id for r in reps]
    load_counts = dict(
        db.query(Lead.assigned_to, func.count(Lead.id))
        .filter(
            Lead.assigned_to.in_(rep_ids), Lead.is_converted.is_(False), Lead.deleted_at.is_(None),
        )
        .group_by(Lead.assigned_to)
        .all()
    )
    return min(reps, key=lambda r: load_counts.get(r.id, 0))


def _round_robin_rep(db: Session, reps: list[User]) -> User | None:
    if not reps:
        return None
    last_assigned = (
        db.query(Lead.assigned_to)
        .filter(Lead.assigned_to.in_([r.id for r in reps]))
        .order_by(Lead.created_at.desc())
        .first()
    )
    if last_assigned is None:
        return reps[0]
    ordered_ids = [r.id for r in reps]
    try:
        last_index = ordered_ids.index(last_assigned[0])
    except ValueError:
        return reps[0]
    return reps[(last_index + 1) % len(reps)]


def assign_lead_to_rep(db: Session) -> User | None:
    """Returns the Rep to assign a newly-Hot lead to, or None if no active Rep exists."""
    rule = db.query(AssignmentRule).filter(AssignmentRule.is_active.is_(True)).first()
    strategy = rule.strategy if rule else "least_loaded"

    reps = _active_reps(db)
    if strategy == "round_robin":
        return _round_robin_rep(db, reps)
    return _least_loaded_rep(db, reps)
