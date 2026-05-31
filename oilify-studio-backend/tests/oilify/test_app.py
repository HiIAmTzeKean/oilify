import os

from fastapi.testclient import TestClient

from oilify_backend.api.app import create_app
from oilify_backend.config.setting import get_settings
from oilify_backend.db import connection as db_connection


def _configure_test_env() -> None:
    os.environ["DATABASE_URL"] = "sqlite:///./oilify_test.db"
    os.environ["SCHEDULER_ENABLED"] = "false"
    get_settings.cache_clear()
    db_connection._db_manager = None


def test_root_returns_oilify_metadata() -> None:
    _configure_test_env()

    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["app_name"] == "Oilify API"


def test_health_returns_ok() -> None:
    _configure_test_env()

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_oil_prices_endpoint_returns_list() -> None:
    _configure_test_env()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/oil-prices/latest")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
