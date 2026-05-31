"""Tests for db/seed.py.

Each test creates its own isolated in-memory SQLite DB so that the shared
test DB's existing rows do not interfere with seed idempotency checks.

Note: seed_inital_stream_jobs (typo: 'inital') does NOT call db.commit(),
so rows inserted by that function are never persisted. This is a known bug,
documented as an xfail test.
"""

import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

# Need the SQLite compile shims for ARRAY / UUID columns
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, UUID as PG_UUID
from sqlalchemy import ARRAY as SA_ARRAY, event as sa_event
from sqlalchemy.ext.compiler import compiles


@compiles(SA_ARRAY, "sqlite")
def _sa_array_sqlite(elem, compiler, **kw):
    return "TEXT"


@compiles(PG_ARRAY, "sqlite")
def _pg_array_sqlite(elem, compiler, **kw):
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _pg_uuid_sqlite(elem, compiler, **kw):
    return "TEXT"


from recnexteval_studio_backend.db.schema import Base, StreamJob, StreamUser


def _make_isolated_manager():
    """Create a DatabaseManager backed by a fresh, isolated in-memory SQLite DB."""
    from recnexteval_studio_backend.db.connection import DatabaseManager

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @sa_event.listens_for(eng, "before_cursor_execute", retval=True)
    def _json_lists(conn, cursor, stmt, params, ctx, executemany):
        if params:
            params = tuple(
                json.dumps(p) if isinstance(p, list) else p for p in params
            )
        return stmt, params

    Base.metadata.create_all(eng)
    factory = sessionmaker(bind=eng, autocommit=False, autoflush=False)

    mgr = object.__new__(DatabaseManager)
    mgr.settings = MagicMock()
    mgr.engine = eng
    mgr.SessionLocal = factory
    return mgr, factory


# ── seed_initial_users ────────────────────────────────────────────────────────


class TestSeedInitialUsers:
    def test_inserts_users_when_table_is_empty(self, mocker):
        from recnexteval_studio_backend.db.seed import seed_initial_users

        mgr, factory = _make_isolated_manager()
        mocker.patch(
            "recnexteval_studio_backend.db.seed.get_database_manager",
            return_value=mgr,
        )

        seed_initial_users()

        sess = factory()
        rows = sess.execute(
            select(StreamUser).where(
                StreamUser.username.in_(["admin", "alice", "bob", "carol"])
            )
        ).all()
        sess.close()
        assert len(rows) == 4

    def test_is_idempotent_when_called_twice(self, mocker):
        from recnexteval_studio_backend.db.seed import seed_initial_users

        mgr, factory = _make_isolated_manager()
        mocker.patch(
            "recnexteval_studio_backend.db.seed.get_database_manager",
            return_value=mgr,
        )

        seed_initial_users()
        seed_initial_users()

        sess = factory()
        count = sess.query(StreamUser).filter(
            StreamUser.username.in_(["admin", "alice", "bob", "carol"])
        ).count()
        sess.close()
        assert count == 4


# ── seed_inital_stream_jobs ───────────────────────────────────────────────────


class TestSeedInitalStreamJobs:
    @pytest.mark.xfail(
        reason="seed_inital_stream_jobs does not call db.commit(), so inserted "
               "rows are never persisted. This is a known bug.",
        strict=True,
    )
    def test_inserts_stream_job_when_table_is_empty(self, mocker):
        from recnexteval_studio_backend.db.seed import seed_inital_stream_jobs, seed_initial_users

        mgr, factory = _make_isolated_manager()
        mocker.patch(
            "recnexteval_studio_backend.db.seed.get_database_manager",
            return_value=mgr,
        )

        seed_initial_users()
        seed_inital_stream_jobs()

        sess = factory()
        count = sess.query(StreamJob).filter(
            StreamJob.name == "Test Stream Job 1"
        ).count()
        sess.close()
        assert count == 1
