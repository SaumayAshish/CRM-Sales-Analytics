"""
Shared pytest fixtures: isolated test database, per-test transactional
rollback, and a FastAPI TestClient wired to the test session.

Traces to: FRD.md NFR-07 (70%+ backend coverage), Phase 2 plan (isolated
test-DB fixture per test).
"""
import os
import uuid

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://crm_user:crm_password@localhost:5433/crm_sales_analytics_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.limiter import limiter
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.reference import ActivityType, LeadSource, LossReason, PipelineStage, Role, Team
from app.models.user import User

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Each test runs inside an outer transaction + SAVEPOINT so that the
    endpoint code's own db.commit() calls only release the savepoint --
    the outer rollback discards everything, giving true per-test isolation
    without truncating tables between tests."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    limiter.reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def reference_data(db):
    roles = {name: Role(name=name) for name in ["Admin", "Manager", "Rep", "Viewer"]}
    db.add_all(roles.values())
    team = Team(name="West Region Sales", region="West")
    db.add(team)
    source = LeadSource(name="Web Form")
    db.add(source)
    stages = [
        PipelineStage(name="Qualification", sort_order=1, default_probability=0.1),
        PipelineStage(name="Needs Analysis", sort_order=2, default_probability=0.3),
        PipelineStage(name="Closed Won", sort_order=5, default_probability=1.0),
        PipelineStage(name="Closed Lost", sort_order=6, default_probability=0.0),
    ]
    db.add_all(stages)
    loss_reason = LossReason(name="Budget constraints")
    db.add(loss_reason)
    activity_type = ActivityType(name="Call")
    db.add(activity_type)
    db.flush()
    return {
        "roles": roles, "team": team, "source": source, "stages": stages,
        "loss_reason": loss_reason, "activity_type": activity_type,
    }


def make_user(db, role_id: uuid.UUID, team_id: uuid.UUID | None = None, email: str | None = None) -> User:
    user = User(
        email=email or f"{uuid.uuid4()}@example.com", password_hash=hash_password("TestPass123!"),
        first_name="Test", last_name="User", role_id=role_id, team_id=team_id,
    )
    db.add(user)
    db.flush()
    return user


def auth_header(client: TestClient, email: str, password: str = "TestPass123!") -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
