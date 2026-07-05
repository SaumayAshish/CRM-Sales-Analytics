"""
Deterministic seed data generator.

Traces to: BRD.md SS6.1 (10,000+ synthetic, clearly-demo records), Phase 2
plan agreement (lead-heavy funnel: 20 users, 100 accounts, 500 contacts,
3,000 leads, 1,500 opportunities, remainder as activities to clear 10,000+).

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
from app.models.workflow import AssignmentRule, ScoringCriteria, ScoringRule

SEED = 42
DEMO_PASSWORD = "DemoPass123!"

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
ACTIVITY_TYPES = ["Call", "Email", "Meeting", "Task"]


def utcnow_minus(days_max: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_max))


def seed_reference_data(db) -> dict:
    roles = {name: Role(name=name, description=f"{name} role") for name in ROLE_NAMES}
    db.add_all(roles.values())

    teams = [Team(name=name, region=region) for name, region in TEAMS]
    db.add_all(teams)

    sources = [LeadSource(name=name) for name in LEAD_SOURCES]
    db.add_all(sources)

    stages = [PipelineStage(name=n, sort_order=o, default_probability=p) for n, o, p in PIPELINE_STAGES]
    db.add_all(stages)

    reasons = [LossReason(name=name) for name in LOSS_REASONS]
    db.add_all(reasons)

    activity_types = [ActivityType(name=name) for name in ACTIVITY_TYPES]
    db.add_all(activity_types)

    scoring_rule = ScoringRule(name="Q3 2026 Scoring Model v1", is_active=True, hot_threshold=70, warm_threshold=40)
    db.add(scoring_rule)
    db.flush()
    db.add_all(
        [
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="source", operator="equals", comparison_value="Referral", weight=15),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="source", operator="equals", comparison_value="Trade Show", weight=10),
            ScoringCriteria(scoring_rule_id=scoring_rule.id, field_name="company_size", operator="greater_than", comparison_value="500", weight=20),
        ]
    )

    assignment_rule = AssignmentRule(name="Round Robin - All Regions", strategy="round_robin", is_active=True)
    db.add(assignment_rule)

    db.flush()
    return {
        "roles": roles,
        "teams": teams,
        "sources": sources,
        "stages": stages,
        "reasons": reasons,
        "activity_types": activity_types,
        "scoring_rule": scoring_rule,
    }


def seed_users(db, ref: dict) -> list[User]:
    """20 users: 1 Admin, 4 Managers (one per team), 14 Reps, 1 Viewer."""
    users: list[User] = []
    password_hash = hash_password(DEMO_PASSWORD)

    admin = User(
        email="admin@northwindsales.com", password_hash=password_hash,
        first_name="Priya", last_name="Nandakumar", role_id=ref["roles"]["Admin"].id, team_id=None,
    )
    users.append(admin)

    for i, team in enumerate(ref["teams"]):
        manager = User(
            email=f"manager.{team.region.lower()}@northwindsales.com", password_hash=password_hash,
            first_name=fake.first_name(), last_name=fake.last_name(),
            role_id=ref["roles"]["Manager"].id, team_id=team.id,
        )
        users.append(manager)

    for i in range(14):
        team = ref["teams"][i % len(ref["teams"])]
        rep = User(
            email=f"rep{i+1}@northwindsales.com", password_hash=password_hash,
            first_name=fake.first_name(), last_name=fake.last_name(),
            role_id=ref["roles"]["Rep"].id, team_id=team.id,
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


def _score_lead(source_name: str) -> tuple[int, str]:
    score = 0
    if source_name == "Referral":
        score += 15
    if source_name == "Trade Show":
        score += 10
    if random.random() < 0.35:
        score += 20  # simulates the company_size > 500 criterion firing
    score += random.randint(0, 45)

    if score >= 70:
        band = "Hot"
    elif score >= 40:
        band = "Warm"
    else:
        band = "Cold"
    return score, band


def seed_leads(db, ref: dict, users: list[User]) -> list[Lead]:
    reps = [u for u in users if u.role_id == ref["roles"]["Rep"].id]
    leads: list[Lead] = []
    for _ in range(3000):
        source = random.choice(ref["sources"])
        score, band = _score_lead(source.name)

        # Lead-heavy funnel: most Hot/Warm leads get assigned; most Cold leads sit unassigned.
        assigned_to = None
        if band == "Hot" or (band == "Warm" and random.random() < 0.7):
            assigned_to = random.choice(reps).id
        elif band == "Cold" and random.random() < 0.15:
            assigned_to = random.choice(reps).id

        # ~20% overall conversion rate, weighted toward Hot leads (realistic funnel shape).
        is_converted = False
        if assigned_to is not None:
            conv_chance = {"Hot": 0.45, "Warm": 0.20, "Cold": 0.05}[band]
            is_converted = random.random() < conv_chance

        leads.append(
            Lead(
                first_name=fake.first_name(), last_name=fake.last_name(), company=fake.company(),
                email=fake.email(), phone=fake.phone_number()[:30], source_id=source.id,
                score=score, score_band=band, assigned_to=assigned_to,
                scoring_rule_id=ref["scoring_rule"].id, is_converted=is_converted,
                created_at=utcnow_minus(180),
            )
        )
    db.add_all(leads)
    db.flush()
    return leads


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

        opportunities.append(
            Opportunity(
                name=f"{account.name} - {fake.bs().capitalize()}", account_id=account.id,
                owner_id=account.owner_id if random.random() < 0.7 else random.choice(owners).id,
                stage_id=stage.id, amount=amount, probability=stage.default_probability,
                expected_close_date=(created_at + timedelta(days=random.randint(30, 180))).date(),
                loss_reason_id=loss_reason_id, closed_at=closed_at, created_at=created_at,
            )
        )
    db.add_all(opportunities)
    db.flush()
    return opportunities


def seed_activities(
    db, ref: dict, users: list[User], leads: list[Lead], accounts: list[Account],
    contacts: list[Contact], opportunities: list[Opportunity], count: int = 5000,
) -> None:
    activities: list[Activity] = []
    for _ in range(count):
        activity_type = random.choice(ref["activity_types"])
        logger = random.choice(users)
        target_roll = random.random()

        lead_id = account_id = contact_id = opportunity_id = None
        if target_roll < 0.35 and leads:
            lead_id = random.choice(leads).id
        elif target_roll < 0.60 and accounts:
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
            # Some tasks due in the future, some overdue (FR-26 overdue-flag scenario).
            due_at = datetime.now(timezone.utc) + timedelta(days=random.randint(-20, 20))

        activities.append(
            Activity(
                type_id=activity_type.id, logged_by=logger.id, lead_id=lead_id, account_id=account_id,
                contact_id=contact_id, opportunity_id=opportunity_id, notes=fake.sentence(nb_words=10),
                is_complete=(random.random() < 0.6) if is_task else True,
                due_at=due_at, created_at=utcnow_minus(120),
            )
        )
        if len(activities) >= 1000:
            db.add_all(activities)
            db.flush()
            activities = []
    if activities:
        db.add_all(activities)
        db.flush()


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
        accounts, contacts = seed_accounts_and_contacts(db, ref, users)
        leads = seed_leads(db, ref, users)
        opportunities = seed_opportunities(db, ref, accounts, users)
        seed_activities(db, ref, users, leads, accounts, contacts, opportunities, count=5000)

        db.commit()

        total = (
            len(users) + len(accounts) + len(contacts) + len(leads) + len(opportunities) + 5000
        )
        print(f"Seed complete: {len(users)} users, {len(accounts)} accounts, {len(contacts)} contacts, "
              f"{len(leads)} leads, {len(opportunities)} opportunities, 5000 activities. "
              f"Total business records: {total}.")
        print(f"All demo users share password: {DEMO_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
