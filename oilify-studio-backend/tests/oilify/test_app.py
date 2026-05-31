from fastapi.testclient import TestClient

from oilify_studio_backend.api.app import create_app


def test_root_returns_oilify_metadata() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["app_name"] == "Oilify API"


def test_health_returns_ok() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_oil_prices_endpoint_returns_list() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/oil-prices/latest")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
