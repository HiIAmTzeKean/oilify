"""Tests for the Oilify configuration layer."""

from oilify_studio_backend.config.setting import Settings, get_settings


def test_settings_use_oilify_defaults(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)

    get_settings.cache_clear()

    settings = Settings()

    assert settings.APP_NAME == "Oilify API"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.APP_ENVIRONMENT == "development"
    assert settings.API_PORT == 9000
    assert settings.API_DEBUG is True
    assert settings.RELOAD_APP_ON_CHANGE is True
    assert settings.CORS_ORIGINS == [
        "http://localhost",
        "http://localhost:80",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
    ]
    assert settings.LOG_LEVEL == "INFO"
    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")
    assert settings.PRICE_SCHEDULE_HOURS == "0,8,16"
    assert settings.SCHEDULER_ENABLED is True


def test_settings_read_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Oilify Test API")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("API_PORT", "8080")
    monkeypatch.setenv("API_DEBUG", "false")
    monkeypatch.setenv("RELOAD_APP_ON_CHANGE", "false")
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com, http://localhost")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./oilify_custom.db")
    monkeypatch.setenv("PRICE_SCHEDULE_HOURS", "1, 5, 9")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    settings = Settings()

    assert settings.APP_NAME == "Oilify Test API"
    assert settings.APP_VERSION == "9.9.9"
    assert settings.APP_ENVIRONMENT == "test"
    assert settings.API_PORT == 8080
    assert settings.API_DEBUG is False
    assert settings.RELOAD_APP_ON_CHANGE is False
    assert settings.CORS_ORIGINS == ["https://example.com", "http://localhost"]
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.DATABASE_URL == "sqlite:///./oilify_custom.db"
    assert settings.PRICE_SCHEDULE_HOURS == "1, 5, 9"
    assert settings.SCHEDULER_ENABLED is False


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second


def test_get_database_config_returns_url() -> None:
    settings = Settings()

    assert settings.get_database_config() == {
        "url": settings.DATABASE_URL,
        "execution_options": {"postgresql_fast_executemanypostgresql_fast_executemany": True},
    }