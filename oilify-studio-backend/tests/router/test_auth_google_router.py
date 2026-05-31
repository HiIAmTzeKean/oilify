"""Tests for router/auth_google_router.py.

The OAuth callback flow: on success redirects to FRONTEND_URL/login?token=...;
on any exception (OAuth failure, missing email, DB error) returns HTTP 401.
The outer except catches ALL exceptions including inner HTTPExceptions, so a
400 "Email not provided" is masked into a 401 response.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from recnexteval_studio_backend.db.schema import StreamUser

_PREFIX = "/api/v1/auth/google"


def _patch_oauth(mocker, token_payload=None, side_effect=None):
    """Patch oauth.google.authorize_access_token to return token_payload or raise."""
    mock_google = MagicMock()
    if side_effect is not None:
        mock_google.authorize_access_token = AsyncMock(side_effect=side_effect)
    else:
        mock_google.authorize_access_token = AsyncMock(return_value=token_payload or {})

    mock_oauth = MagicMock()
    mock_oauth.google = mock_google
    mocker.patch(
        "recnexteval_studio_backend.router.auth_google_router.oauth",
        mock_oauth,
    )
    return mock_oauth


# ── callback ──────────────────────────────────────────────────────────────────


class TestGoogleCallback:
    def test_existing_user_redirects_with_token(self, client, session_factory, mocker):
        # Insert a user whose email we will return from OAuth.
        email = f"existing-{uuid.uuid4().hex[:8]}@test.example"
        sess = session_factory()
        user = StreamUser(
            username=email,
            email=email,
            password="hashed_dummy",
        )
        sess.add(user)
        sess.commit()
        sess.close()

        _patch_oauth(mocker, {"userinfo": {"email": email}})

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code in (302, 307)
        assert "token=" in resp.headers["location"]
        assert "login" in resp.headers["location"]

    def test_new_user_is_created_and_redirected(self, client, session_factory, mocker):
        email = f"newuser-{uuid.uuid4().hex[:8]}@test.example"
        _patch_oauth(mocker, {"userinfo": {"email": email}})

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code in (302, 307)
        sess = session_factory()
        created = sess.query(StreamUser).filter(StreamUser.email == email).first()
        sess.close()
        assert created is not None
        assert created.username == email

    def test_missing_email_returns_401(self, client, mocker):
        # userinfo without email → HTTPException(400) is raised inside try,
        # which is caught by outer except Exception → re-raised as 401.
        _patch_oauth(mocker, {"userinfo": {}})

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code == 401

    def test_userinfo_absent_returns_401(self, client, mocker):
        # token has no userinfo key at all
        _patch_oauth(mocker, {})

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code == 401

    def test_oauth_exception_returns_401(self, client, mocker):
        _patch_oauth(mocker, side_effect=Exception("invalid_grant"))

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code == 401

    def test_oauth_valueerror_returns_401(self, client, mocker):
        _patch_oauth(mocker, side_effect=ValueError("token expired"))

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code == 401

    def test_callback_error_detail_contains_message(self, client, mocker):
        _patch_oauth(mocker, side_effect=Exception("oauth_error_detail"))

        resp = client.get(f"{_PREFIX}/callback", follow_redirects=False)

        assert resp.status_code == 401
        assert "oauth_error_detail" in resp.json()["detail"]
