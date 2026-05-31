"""Tests for config/setting.py.

Covers lru_cache singleton behaviour, environment variable parsing, and the
shape of the database config dictionary returned by get_database_config().
"""

import os

import pytest


class TestGetSettingsLruCache:
    def test_returns_same_instance_on_repeated_calls(self):
        from recnexteval_studio_backend.config.setting import get_settings

        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_returns_new_instance_after_cache_clear(self):
        from recnexteval_studio_backend.config.setting import get_settings

        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        assert s1 is not s2


class TestSettingsEnvVarParsing:
    def test_access_token_expire_minutes_read_from_env(self, monkeypatch):
        from recnexteval_studio_backend.config.setting import Settings

        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "42")
        s = Settings()
        assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 42

    def test_api_port_read_from_env(self, monkeypatch):
        from recnexteval_studio_backend.config.setting import Settings

        monkeypatch.setenv("API_PORT", "8080")
        s = Settings()
        assert s.API_PORT == 8080

    def test_api_debug_true_from_env(self, monkeypatch):
        from recnexteval_studio_backend.config.setting import Settings

        monkeypatch.setenv("API_DEBUG", "true")
        s = Settings()
        assert s.API_DEBUG is True

    def test_api_debug_false_from_env(self, monkeypatch):
        from recnexteval_studio_backend.config.setting import Settings

        monkeypatch.setenv("API_DEBUG", "false")
        s = Settings()
        assert s.API_DEBUG is False

    def test_defaults_are_applied_when_env_vars_absent(self, monkeypatch):
        from recnexteval_studio_backend.config.setting import Settings

        for key in ("ACCESS_TOKEN_EXPIRE_MINUTES", "API_PORT", "API_DEBUG"):
            monkeypatch.delenv(key, raising=False)

        s = Settings()
        assert s.API_PORT == 9000
        assert s.API_DEBUG is True


class TestGetDatabaseConfig:
    def test_returns_dict_with_url_key(self):
        from recnexteval_studio_backend.config.setting import get_settings

        get_settings.cache_clear()
        config = get_settings().get_database_config()
        assert "url" in config
        assert isinstance(config["url"], str)

    def test_database_url_falls_back_to_default_when_env_absent(self, monkeypatch):
        from recnexteval_studio_backend.config.setting import Settings

        monkeypatch.delenv("DATABASE_URL", raising=False)
        s = Settings()
        assert "postgresql" in s.DATABASE_URL.lower() or "sqlite" in s.DATABASE_URL.lower()
