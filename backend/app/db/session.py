"""
SQLAlchemy engine/session setup (sync).

Traces to: Phase 2 plan decision (sync SQLAlchemy 2.0 + psycopg2, ADR-002
for PostgreSQL as the datastore).
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
