"""Shared fixtures for router integration tests.

Uses a minimal FastAPI app wired against the in-memory SQLite engine so that
endpoints execute real SQL without touching a live PostgreSQL instance.
"""

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from recnexteval_studio_backend.db.connection import get_db
from recnexteval_studio_backend.db.schema import StreamAlgorithm, StreamJob, StreamUser
from recnexteval_studio_backend.router.algorithm_router import create_algorithm_router
from recnexteval_studio_backend.router.auth_google_router import create_auth_google_router
from recnexteval_studio_backend.router.auth_router import create_auth_router
from recnexteval_studio_backend.router.dataset_router import create_dataset_router
from recnexteval_studio_backend.router.evaluator_router import create_evaluator_router
from recnexteval_studio_backend.router.metric_router import create_metric_router
from recnexteval_studio_backend.router.stream_router import create_stream_router
from recnexteval_studio_backend.services.auth import get_current_username, hash_password

_API_PREFIX = "/api/v1"

_TEST_USERNAME = "routertestuser"
_TEST_PASSWORD = "testpass123"


# ── application ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Minimal FastAPI app that includes all routers under test."""
    app = FastAPI()
    app.include_router(create_auth_router(), prefix=_API_PREFIX)
    app.include_router(create_stream_router(), prefix=_API_PREFIX)
    app.include_router(create_evaluator_router(), prefix=_API_PREFIX)
    app.include_router(create_algorithm_router(), prefix=_API_PREFIX)
    app.include_router(create_dataset_router(), prefix=_API_PREFIX)
    app.include_router(create_metric_router(), prefix=_API_PREFIX)
    app.include_router(create_auth_google_router(), prefix=_API_PREFIX)
    return app


# ── persistent test user ──────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def router_user(session_factory) -> dict:
    """Create one test user with a known password; persists for the whole session."""
    sess = session_factory()
    user = StreamUser(
        username=_TEST_USERNAME,
        password=hash_password(_TEST_PASSWORD),
        email="router@test.example",
    )
    sess.add(user)
    sess.commit()
    data = {"id": user.id, "username": user.username, "password": _TEST_PASSWORD}
    sess.close()
    return data


# ── TestClient factories ──────────────────────────────────────────────────────


@pytest.fixture
def client(test_app, session_factory, router_user) -> TestClient:
    """TestClient with both DB and auth dependencies overridden.

    Suitable for all stream/evaluator endpoint tests; auth is bypassed so that
    every request is treated as coming from router_user.
    """

    def _get_db_override():
        sess = session_factory()
        try:
            yield sess
        finally:
            sess.close()

    test_app.dependency_overrides[get_db] = _get_db_override
    test_app.dependency_overrides[get_current_username] = lambda: router_user["username"]

    with TestClient(test_app, raise_server_exceptions=True) as c:
        yield c

    test_app.dependency_overrides.clear()


@pytest.fixture
def client_no_raise(test_app, session_factory, router_user) -> TestClient:
    """Like `client` but with raise_server_exceptions=False.

    Use only in tests that assert on 5xx responses so that server errors are
    returned as HTTP responses rather than propagated as Python exceptions.
    """

    def _get_db_override():
        sess = session_factory()
        try:
            yield sess
        finally:
            sess.close()

    test_app.dependency_overrides[get_db] = _get_db_override
    test_app.dependency_overrides[get_current_username] = lambda: router_user["username"]

    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c

    test_app.dependency_overrides.clear()


@pytest.fixture
def auth_client(test_app, session_factory, router_user) -> TestClient:
    """TestClient with only the DB overridden; uses real JWT auth.

    Suitable for auth-router tests where the login/token flow matters.
    """

    def _get_db_override():
        sess = session_factory()
        try:
            yield sess
        finally:
            sess.close()

    test_app.dependency_overrides[get_db] = _get_db_override

    with TestClient(test_app, raise_server_exceptions=True) as c:
        yield c

    test_app.dependency_overrides.clear()


# ── helper: create a stream job owned by router_user ─────────────────────────


@pytest.fixture
def router_stream_job(session_factory, router_user):
    """Factory that inserts a StreamJob (and optional algorithm) for router_user.

    Returns a callable that accepts keyword arguments and returns the job ID.
    """

    created_ids: list[int] = []

    def _make(
        *,
        has_algorithms: bool = False,
        started: bool = False,
        completed: bool = False,
        failed: bool = False,
    ) -> int:
        sess = session_factory()
        job = StreamJob(
            name=f"rjob-{uuid.uuid4().hex}",
            dataset="movielens",
            top_k=10,
            metrics=json.dumps(["ndcg"]),
            timestamp_split_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            window_size=7,
            user_id=router_user["id"],
        )
        if started or completed or failed:
            job.started_at = datetime.now(timezone.utc)
        if completed:
            job.completed_at = datetime.now(timezone.utc)
        if failed:
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = "test failure"
        sess.add(job)
        sess.flush()

        if has_algorithms:
            sess.add(
                StreamAlgorithm(
                    stream_job_id=job.id,
                    algorithm_name="als",
                    algorithm_uuid=uuid.uuid4(),
                    parameters=json.dumps({"num_factors": 10}),
                )
            )

        sess.commit()
        job_id = job.id
        sess.close()
        created_ids.append(job_id)
        return job_id

    return _make
