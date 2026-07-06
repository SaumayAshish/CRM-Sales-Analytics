"""
Deterministic seed data generator.

Traces to: BRD.md SS6.1 (10,000+ synthetic, clearly-demo records), Phase 2
plan agreement (lead-heavy funnel: 20 users, 100 accounts, 500 contacts,
3,000 leads, 1,500 opportunities, remainder as activities to clear
10,000+), Phase 3 kickoff decision (re-seed from scratch through the real
scoring/assignment engines rather than a hand-faked formula, least-loaded
as the default assignment strategy).

Run via: python -m app.scripts.seed
All demo users share the password "DemoPass123!" (documented here, not a
production credential -- this is synthetic seed data, per CLAUDE.md rule 7).
"""
import random
from datetime import datetime, timedelta, timezone

from faker import Faker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.account import Account, Contact
from app.models.activity import Activity
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.reference import ActivityType, LeadSource, LossReason, PipelineStage, Role, Team
from app.models.user import User
from app.models.workflow import AssignmentRule, ScoringCriteria, ScoringRule, WorkflowRule
from app.services.assignment_engine import assign_lead_to_rep
from app.services.scoring_engine import evaluate_lead_score

SEED = 42
DEMO_PASSWORD = "DemoPass123!"
ADMIN_PASSWORD = "Caesar@0&"

random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

ROLE_NAMES = ["Admin", "Manager", "Rep", "Viewer"]
TEAMS = [("West Region Sales", "West"), ("East Region Sales", "East"), ("North Region Sales", "North"), ("South Region Sales", "South")]
LEAD_SOURCES = ["Web Form", "Trade Show", "Referral", "Cold Outreach", "Partner"]
PIPELINE_STAGES = [
    ("Qualification", 1, 0.100),
    ("Needs Analysis", 2, 0.300),
    ("Proposal", 3, 0.500),
    ("Negotiation", 4, 0.700),
    ("Closed Won", 5, 1.000),
    ("Closed Lost", 6, 0.000),
]
LOSS_REASONS = ["Budget constraints", "Chose competitor", "No decision made", "Timing not right", "Lost to internal build"]
ACTIVITY_TYPES = ["Call", "Email", "Meeting", "Task", "Note", "Status Change"]


def utcnow_minus(days_max: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_max))


def seed_reference_data(db) -> dict:
    roles = {name: Role(name=name, description=f"{name} role") for name in ROLE_NAMES}
    db.add_all(roles.values())

    teams = [Team(name=name, region=region) for name, region in TEAMS]
    db.add_all(teams)

    sources = [LeadSource(name=name) for name in LEAD_SOURCES]
    db.add_all(sources)

    stage_objs = {n: PipelineStage(name=n, sort_order=o, default_probability=p) for n, o, p in PIPELINE_STAGES}
    db.add_all(stage_objs.values())
    db.flush()

    # FR-46/BR-21: data-driven transition graph -- the linear funnel plus a
    # direct-to-Closed-Lost shortcut from every open stage (deals can die
    # at any point), Admin-configurable without a code change.
    stage_objs["Qualification"].allowed_next_stage_ids = [str(stage_objs["Needs Analysis"].id), str(stage_objs["Closed Lost"].id)]
    stage_objs["Needs Analysis"].allowed_next_stage_ids = [str(stage_objs["Proposal"].id), str(stage_objs["Closed Lost"].id)]
    stage_objs["Proposal"].allowed_next_stage_ids = [str(stage_objs["Negotiation"].id), str(stage_objs["Closed Lost"].id)]
    stage_objs["Negotiation"].allowed_next_stage_ids = [str(stage_objs["Closed Won"].id), str(stage_objs["Closed Lost"].id)]
    stages = list(stage_objs.values())

    reasons = [LossReason(name=name) for name in LOSS_REASONS]
    db.add_all(reasons)

    activity_types = [ActivityType(name=name) for name in ACTIVITY_TYPES]
    db.add_all(activity_types)

    scoring_rule = ScoringRule(name="Q3 2026 Scoring Model v1", is_active=True, hot_threshold=70, warm_threshold=40)
    db.add(scoring_rule)
    db.flush()
    db.add_all(
        [
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="source", operator="equals", comparison_value="Referral", weight=20),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="source", operator="equals", comparison_value="Trade Show", weight=12),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="company_size", operator="greater_than", comparison_value="500", weight=25),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="activity_recency_days", operator="less_than_or_equal", comparison_value="7", weight=15),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="activity_type_exists", operator="equals", comparison_value="Meeting", weight=20),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="no_response_days", operator="greater_than_or_equal", comparison_value="30", weight=-20),
        ]
    )

    # Phase 3 kickoff decision: least-loaded is the default assignment strategy.
    assignment_rule = AssignmentRule(name="Least Loaded - All Regions", strategy="least_loaded", is_active=True)
    db.add(assignment_rule)

    db.add_all(
        [
            WorkflowRule(
                name="Notify on Hot Lead", trigger_event="lead_scored", is_active=True,
                conditions=[{"field": "score_band", "operator": "equals", "value": "Hot"}],
                actions=[{"type": "send_notification", "params": {"message": "A lead just scored Hot and needs follow-up."}}],
            ),
            WorkflowRule(
                name="Task on Won Deal", trigger_event="opportunity_won", is_active=True,
                conditions=[],
                actions=[{"type": "create_task", "params": {"notes": "Kick off onboarding for the newly won deal.", "due_in_days": 2}}],
            ),
        ]
    )

    db.flush()
    return {
        "roles": roles, "teams": teams, "sources": sources, "stages": stages,
        "reasons": reasons, "activity_types": activity_types, "scoring_rule": scoring_rule,
    }


def seed_users(db, ref: dict) -> list[User]:
    """20 users: 1 Admin, 4 Managers (one per team), 14 Reps, 1 Viewer."""
    users: list[User] = []
    password_hash = hash_password(DEMO_PASSWORD)

    admin = User(
        email="admin@northwindsales.com", password_hash=hash_password(ADMIN_PASSWORD),
        first_name="Saumay", last_name="Ashish", role_id=ref["roles"]["Admin"].id, team_id=None,
    )
    users.append(admin)

    for team in ref["teams"]:
        manager = User(
            email=f"manager.{team.region.lower()}@northwindsales.com", password_hash=password_hash,
            first_name=fake.first_name(), last_name=fake.last_name(),
            role_id=ref["roles"]["Manager"].id, team_id=team.id,
            quota=random.choice([300_000, 350_000, 400_000]),  # BR-23
        )
        users.append(manager)

    for i in range(14):
        team = ref["teams"][i % len(ref["teams"])]
        rep = User(
            email=f"rep{i+1}@northwindsales.com", password_hash=password_hash,
            first_name=fake.first_name(), last_name=fake.last_name(),
            role_id=ref["roles"]["Rep"].id, team_id=team.id,
            quota=random.choice([150_000, 200_000, 250_000, 300_000]),  # BR-23
        )
        users.append(rep)

    viewer = User(
        email="viewer@northwindsales.com", password_hash=password_hash,
        first_name="Sam", last_name="Ostrowski", role_id=ref["roles"]["Viewer"].id, team_id=None,
    )
    users.append(viewer)

    db.add_all(users)
    db.flush()
    return users


def seed_accounts_and_contacts(db, ref: dict, users: list[User]) -> tuple[list[Account], list[Contact]]:
    owners = [u for u in users if u.role_id in (ref["roles"]["Manager"].id, ref["roles"]["Rep"].id)]
    accounts: list[Account] = []
    for _ in range(100):
        account = Account(
            name=fake.company(), domain=fake.domain_name(), industry=fake.bs().split()[0].capitalize(),
            owner_id=random.choice(owners).id, created_at=utcnow_minus(365),
        )
        accounts.append(account)
    db.add_all(accounts)
    db.flush()

    contacts: list[Contact] = []
    for account in accounts:
        contact_count = random.randint(3, 8)
        for i in range(contact_count):
            if len(contacts) >= 500:
                break
            contacts.append(
                Contact(
                    account_id=account.id, first_name=fake.first_name(), last_name=fake.last_name(),
                    email=fake.company_email(), phone=fake.phone_number()[:30], is_primary=(i == 0),
                    created_at=account.created_at,
                )
            )
        if len(contacts) >= 500:
            break
    db.add_all(contacts)
    db.flush()
    return accounts, contacts


def seed_raw_leads(db, ref: dict) -> list[Lead]:
    """3,000 leads with no score/assignment yet -- the real engine (called
    in score_and_assign_leads) computes those, not a hand-faked formula."""
    leads: list[Lead] = []
    for _ in range(3000):
        source = random.choice(ref["sources"])
        custom_fields = None
        if random.random() < 0.35:
            custom_fields = {"company_size": random.choice([50, 150, 400, 750, 1200, 3000])}

        leads.append(
            Lead(
                first_name=fake.first_name(), last_name=fake.last_name(), company=fake.company(),
                email=fake.email(), phone=fake.phone_number()[:30], source_id=source.id,
                custom_fields=custom_fields, created_at=utcnow_minus(180),
            )
        )
    db.add_all(leads)
    db.flush()
    return leads


def seed_lead_signal_activities(db, ref: dict, leads: list[Lead], users: list[User]) -> None:
    """Attach activities to a subset of leads *before* scoring, so the
    recency/behavior/negative-signal criteria have real data to evaluate
    against (not just attribute fields) -- otherwise those three of the
    four rule-type families would never fire in seed data."""
    meeting_type = next(t for t in ref["activity_types"] if t.name == "Meeting")
    call_type = next(t for t in ref["activity_types"] if t.name == "Call")
    loggers = users

    for lead in leads:
        roll = random.random()
        if roll < 0.15:
            # Recent engagement + a demo meeting: pushes toward Hot.
            db.add(
                Activity(
                    type_id=meeting_type.id, logged_by=random.choice(loggers).id, lead_id=lead.id,
                    notes="Demo meeting held.", created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 6)),
                )
            )
        elif roll < 0.30:
            # Recent call only (smaller recency signal, no behavior bonus).
            db.add(
                Activity(
                    type_id=call_type.id, logged_by=random.choice(loggers).id, lead_id=lead.id,
                    notes="Discovery call.", created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 6)),
                )
            )
        elif roll < 0.45:
            # Gone quiet: last activity was over a month ago -- negative signal.
            db.add(
                Activity(
                    type_id=call_type.id, logged_by=random.choice(loggers).id, lead_id=lead.id,
                    notes="Initial outreach, no follow-up since.",
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(31, 90)),
                )
            )
        # else: no activity yet -- no_response_days falls back to lead.created_at.
    db.flush()


def score_and_assign_leads(db, leads: list[Lead]) -> None:
    """FR-49/FR-52 via the real engines, not a stand-in formula."""
    for lead in leads:
        score, band, _matched, rule_id = evaluate_lead_score(db, lead)
        lead.score = score
        lead.score_band = band
        lead.scoring_rule_id = rule_id

        if band == "Hot":
            rep = assign_lead_to_rep(db)
            if rep is not None:
                lead.assigned_to = rep.id
        elif band == "Warm" and random.random() < 0.4:
            # Simulates a Manager manually triaging some Warm leads from the unassigned queue (BR-13).
            rep = assign_lead_to_rep(db)
            if rep is not None:
                lead.assigned_to = rep.id

        if lead.assigned_to is not None:
            conv_chance = {"Hot": 0.45, "Warm": 0.20, "Cold": 0.05}[band]
            lead.is_converted = random.random() < conv_chance
    db.flush()


def seed_lead_conversions(
    db, ref: dict, leads: list[Lead]
) -> tuple[list[Account], list[Contact], list[Opportunity]]:
    """Mirrors the real FR-06 conversion flow (Account+Contact+Opportunity,
    linked via converted_from_lead_id) for every lead flagged is_converted
    during scoring -- without this, is_converted is just a cosmetic flag
    with no backing data, and vw_lead_source_roi / vw_sales_funnel would
    show zero attributed revenue for every source (caught by querying the
    seeded database directly, not assumed correct from the code)."""
    accounts: list[Account] = []
    contacts: list[Contact] = []
    opportunities: list[Opportunity] = []

    for lead in leads:
        if not lead.is_converted:
            continue
        owner_id = lead.assigned_to
        if owner_id is None:
            continue

        account = Account(
            name=lead.company, owner_id=owner_id, converted_from_lead_id=lead.id,
            created_at=lead.created_at + timedelta(days=random.randint(1, 14)),
        )
        db.add(account)
        db.flush()
        accounts.append(account)

        contact = Contact(
            account_id=account.id, first_name=lead.first_name, last_name=lead.last_name,
            email=lead.email, phone=lead.phone, is_primary=True, created_at=account.created_at,
        )
        db.add(contact)
        contacts.append(contact)

        stage = random.choices(
            ref["stages"], weights=[0.30, 0.22, 0.18, 0.12, 0.12, 0.06], k=1
        )[0]
        closed_at = None
        loss_reason_id = None
        if stage.name in ("Closed Won", "Closed Lost"):
            closed_at = account.created_at + timedelta(days=random.randint(10, 60))
            if stage.name == "Closed Lost":
                loss_reason_id = random.choice(ref["reasons"]).id

        opportunity = Opportunity(
            name=f"{lead.company} - New Business", account_id=account.id, owner_id=owner_id,
            stage_id=stage.id, amount=round(random.uniform(5_000, 150_000), 2),
            probability=stage.default_probability,
            expected_close_date=(account.created_at + timedelta(days=random.randint(30, 120))).date(),
            loss_reason_id=loss_reason_id, closed_at=closed_at, created_at=account.created_at,
        )
        db.add(opportunity)
        opportunities.append(opportunity)

    db.flush()
    return accounts, contacts, opportunities


def seed_opportunities(db, ref: dict, accounts: list[Account], users: list[User]) -> list[Opportunity]:
    owners = [u for u in users if u.role_id in (ref["roles"]["Manager"].id, ref["roles"]["Rep"].id)]
    stage_weights = [0.30, 0.22, 0.18, 0.12, 0.12, 0.06]  # funnel-shaped: fewer deals survive to close
    lost_stage = next(s for s in ref["stages"] if s.name == "Closed Lost")

    opportunities: list[Opportunity] = []
    for _ in range(1500):
        account = random.choice(accounts)
        stage = random.choices(ref["stages"], weights=stage_weights, k=1)[0]
        amount = round(random.uniform(5_000, 250_000), 2)
        created_at = utcnow_minus(270)
        closed_at = None
        loss_reason_id = None
        if stage.name in ("Closed Won", "Closed Lost"):
            closed_at = created_at + timedelta(days=random.randint(10, 90))
            if stage.id == lost_stage.id:
                loss_reason_id = random.choice(ref["reasons"]).id

        # FR-65: a rep can override probability above a stage's default to flag
        # a high-confidence deal (e.g. a verbal commitment). Simulate ~30% of
        # open Negotiation deals having had this done, so Commit Forecast
        # (probability >= 0.75) reflects genuine feature usage rather than
        # sitting at $0 because no seeded deal ever exercises the override.
        probability = stage.default_probability
        if stage.name == "Negotiation" and closed_at is None and random.random() < 0.30:
            probability = round(random.uniform(0.75, 0.95), 3)

        opportunities.append(
            Opportunity(
                name=f"{account.name} - {fake.bs().capitalize()}", account_id=account.id,
                owner_id=account.owner_id if random.random() < 0.7 else random.choice(owners).id,
                stage_id=stage.id, amount=amount, probability=probability,
                expected_close_date=(created_at + timedelta(days=random.randint(30, 180))).date(),
                loss_reason_id=loss_reason_id, closed_at=closed_at, created_at=created_at,
            )
        )
    db.add_all(opportunities)
    db.flush()
    return opportunities


def seed_bulk_activities(
    db, ref: dict, users: list[User], leads: list[Lead], accounts: list[Account],
    contacts: list[Contact], opportunities: list[Opportunity], count: int,
) -> int:
    """Additional activities beyond the lead-signal ones, spread across all
    entity types, to reach the 10,000+ total record target."""
    activities: list[Activity] = []
    written = 0
    for _ in range(count):
        activity_type = random.choice(ref["activity_types"])
        logger = random.choice(users)
        target_roll = random.random()

        lead_id = account_id = contact_id = opportunity_id = None
        if target_roll < 0.25 and leads:
            lead_id = random.choice(leads).id
        elif target_roll < 0.55 and accounts:
            account_id = random.choice(accounts).id
        elif target_roll < 0.80 and contacts:
            contact_id = random.choice(contacts).id
        elif opportunities:
            opportunity_id = random.choice(opportunities).id
        else:
            account_id = random.choice(accounts).id

        is_task = activity_type.name == "Task"
        due_at = None
        if is_task:
            due_at = datetime.now(timezone.utc) + timedelta(days=random.randint(-20, 20))

        activities.append(
            Activity(
                type_id=activity_type.id, logged_by=logger.id, lead_id=lead_id, account_id=account_id,
                contact_id=contact_id, opportunity_id=opportunity_id, notes=fake.sentence(nb_words=10),
                is_complete=(random.random() < 0.6) if is_task else True,
                due_at=due_at, created_at=utcnow_minus(120),
            )
        )
        written += 1
        if len(activities) >= 1000:
            db.add_all(activities)
            db.flush()
            activities = []
    if activities:
        db.add_all(activities)
        db.flush()
    return written


def main() -> None:
    Base.metadata.create_all(bind=engine, checkfirst=True)
    db = SessionLocal()
    try:
        existing = db.query(Role).count()
        if existing > 0:
            print("Seed data already present (roles table is non-empty) -- aborting to avoid duplicates.")
            return

        ref = seed_reference_data(db)
        users = seed_users(db, ref)
        direct_accounts, direct_contacts = seed_accounts_and_contacts(db, ref, users)
        leads = seed_raw_leads(db, ref)
        seed_lead_signal_activities(db, ref, leads, users)
        score_and_assign_leads(db, leads)
        converted_accounts, converted_contacts, converted_opportunities = seed_lead_conversions(db, ref, leads)
        direct_opportunities = seed_opportunities(db, ref, direct_accounts, users)

        accounts = direct_accounts + converted_accounts
        contacts = direct_contacts + converted_contacts
        opportunities = direct_opportunities + converted_opportunities

        seed_bulk_activities(db, ref, users, leads, accounts, contacts, opportunities, count=4500)

        db.commit()

        activity_count = db.query(Activity).count()
        total = len(users) + len(accounts) + len(contacts) + len(leads) + len(opportunities) + activity_count
        band_counts = {b: sum(1 for lead in leads if lead.score_band == b) for b in ("Hot", "Warm", "Cold")}

        print(
            f"Seed complete: {len(users)} users, {len(accounts)} accounts, {len(contacts)} contacts, "
            f"{len(leads)} leads, {len(opportunities)} opportunities, "
            f"{activity_count} activities. Total business records: {total}."
        )
        print(f"Lead score bands: {band_counts}")
        print(f"All demo users share password: {DEMO_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
