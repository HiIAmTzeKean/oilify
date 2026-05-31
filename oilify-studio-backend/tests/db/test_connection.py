"""Tests for db/connection.py.

Tests use a fresh in-memory SQLite engine rather than the global DatabaseManager
singleton, so they never touch the real database configuration.
"""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock, patch


# ── DatabaseManager ───────────────────────────────────────────────────────────


class TestDatabaseManagerSingleton:
    def test_get_database_manager_returns_same_instance_on_repeated_calls(self, mocker):
        from recnexteval_studio_backend.db.connection import get_database_manager

        mocker.patch(
            "recnexteval_studio_backend.db.connection.DatabaseManager._initialize_engine"
        )

        # Reset the global _db_manager for isolation
        import recnexteval_studio_backend.db.connection as conn_module
        original = conn_module._db_manager
        conn_module._db_manager = None
        try:
            mgr1 = get_database_manager()
            mgr2 = get_database_manager()
            assert mgr1 is mgr2
        finally:
            conn_module._db_manager = original

    def test_database_manager_initialises_engine_on_construction(self, mocker):
        init_spy = mocker.patch(
            "recnexteval_studio_backend.db.connection.DatabaseManager._initialize_engine"
        )

        from recnexteval_studio_backend.db.connection import DatabaseManager

        DatabaseManager()

        init_spy.assert_called_once()


# ── create_tables / drop_tables ───────────────────────────────────────────────


class TestCreateDropTables:
    def _make_sqlite_manager(self):
        """Return a DatabaseManager backed by an in-memory SQLite engine."""
        from recnexteval_studio_backend.db.connection import DatabaseManager
        from recnexteval_studio_backend.db.schema import Base

        eng = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        mgr = object.__new__(DatabaseManager)
        mgr.engine = eng
        mgr.SessionLocal = sessionmaker(bind=eng, autocommit=False, autoflush=False)
        mgr.settings = MagicMock()
        return mgr, eng

    def test_create_tables_produces_expected_table_names(self):
        mgr, eng = self._make_sqlite_manager()
        mgr.create_tables()

        table_names = inspect(eng).get_table_names()
        for expected in ("stream_user", "stream_job", "stream_algorithm"):
            assert expected in table_names, f"Table '{expected}' not found after create_tables()"

    def test_drop_tables_removes_all_tables(self):
        mgr, eng = self._make_sqlite_manager()
        mgr.create_tables()
        mgr.drop_tables()

        table_names = inspect(eng).get_table_names()
        assert table_names == []


# ── get_db_session (generator / dependency) ───────────────────────────────────


class TestGetDbSession:
    def _make_session_manager(self):
        eng = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        factory = sessionmaker(bind=eng, autocommit=False, autoflush=False)
        return factory

    def test_session_is_closed_after_normal_use(self):
        from recnexteval_studio_backend.db.connection import DatabaseManager

        factory = self._make_session_manager()
        mgr = object.__new__(DatabaseManager)
        mgr.SessionLocal = factory
        mgr.settings = MagicMock()

        gen = mgr.get_db_session()
        sess = next(gen)

        close_called = False
        original_close = sess.close

        def _spy():
            nonlocal close_called
            close_called = True
            original_close()

        sess.close = _spy

        try:
            next(gen)
        except StopIteration:
            pass

        assert close_called, "Session.close() must be called after normal use"

    def test_session_is_closed_even_when_exception_occurs(self):
        from recnexteval_studio_backend.db.connection import DatabaseManager

        factory = self._make_session_manager()
        mgr = object.__new__(DatabaseManager)
        mgr.SessionLocal = factory
        mgr.settings = MagicMock()

        gen = mgr.get_db_session()
        sess = next(gen)

        close_called = False
        original_close = sess.close

        def _spy():
            nonlocal close_called
            close_called = True
            original_close()

        sess.close = _spy

        try:
            gen.throw(RuntimeError("simulated error"))
        except (RuntimeError, StopIteration):
            pass

        assert close_called, "Session.close() must be called even when an exception occurs"
