"""Shared fixtures for Oilify tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from oilify_studio_backend.api.app import create_app
from oilify_studio_backend.config.setting import get_settings
from oilify_studio_backend.db import connection as db_connection
from oilify_studio_backend.db.connection import create_tables, get_database_manager, get_db


@pytest.fixture(autouse=True)
def configure_oilify_test_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    db_path = tmp_path / "oilify_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setattr(
        "oilify_studio_backend.db.seed._resolve_seed_metadata",
        lambda ticker: (ticker, f"{ticker} short", f"{ticker} long"),
    )
    get_settings.cache_clear()
    db_connection._db_manager = None
    yield
    get_settings.cache_clear()
    db_connection._db_manager = None


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    create_tables()
    session = get_database_manager().get_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI, db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    app.dependency_overrides.clear()