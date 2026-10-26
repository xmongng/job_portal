"""No production/development database writes: opt-in only to a *_test database."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("JWT_SECRET", "test-only-secret-with-at-least-thirty-two-characters")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@localhost/unused_test")

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.persistence.database import get_db_session
from app.main import app


@pytest.fixture(scope="session")
def integration_engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL pointing to a dedicated *_test database")
    if not (make_url(url).database or "").endswith("_test"):
        raise ValueError("TEST_DATABASE_URL database must end with _test")
    engine = create_engine(url)
    # Apply migrations through an explicitly supplied connection; never rewrite .env.
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option(
        "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
    )
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def integration_client(integration_engine, tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "file_storage_path", tmp_path / "private")
    monkeypatch.setattr(settings, "ai_provider", "none")
    monkeypatch.setattr(settings, "auth_rate_limit_per_minute", 10000)
    with integration_engine.connect() as connection:
        transaction = connection.begin()

        def override():
            with Session(
                bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
            ) as db:
                try:
                    yield db
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db_session] = override
        try:
            with TestClient(app) as client:
                yield client, connection
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
            if transaction.is_active:
                transaction.rollback()
