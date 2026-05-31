"""Tests for services/auth.py — password hashing, JWT, and the get_current_username dependency."""

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from recnexteval_studio_backend.config.setting import get_settings
from recnexteval_studio_backend.services.auth import (
    create_access_token,
    decode_token,
    get_current_username,
    hash_password,
    verify_password,
)


# ── password hashing ─────────────────────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_differs_from_plaintext(self):
        assert hash_password("secret") != "secret"

    def test_bcrypt_hash_prefix(self):
        hashed = hash_password("test")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_correct_password_returns_true(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_two_hashes_of_same_password_are_different(self):
        h1, h2 = hash_password("same"), hash_password("same")
        assert h1 != h2

    def test_both_hashes_verify_against_original(self):
        pwd = "shared"
        assert verify_password(pwd, hash_password(pwd))
        assert verify_password(pwd, hash_password(pwd))


# ── token creation / decoding ─────────────────────────────────────────────────


class TestTokenCreation:
    def test_create_returns_non_empty_string(self):
        token = create_access_token(user_id=1, username="alice")
        assert isinstance(token, str) and token

    def test_decode_recovers_user_id_and_username(self):
        token = create_access_token(user_id=42, username="bob")
        payload = decode_token(token)
        assert payload["user_id"] == 42
        assert payload["username"] == "bob"

    def test_default_auth_method_is_password(self):
        payload = decode_token(create_access_token(user_id=1, username="carol"))
        assert payload["auth_method"] == "password"

    def test_google_auth_method_preserved(self):
        token = create_access_token(user_id=1, username="carol", auth_method="google")
        assert decode_token(token)["auth_method"] == "google"

    def test_exp_and_iat_claims_present(self):
        payload = decode_token(create_access_token(user_id=1, username="alice"))
        assert "exp" in payload
        assert "iat" in payload

    def test_custom_expiry_delta_reflected_in_exp(self):
        delta = timedelta(minutes=5)
        token = create_access_token(user_id=1, username="alice", expires_delta=delta)
        payload = decode_token(token)
        expected_exp = (datetime.now(timezone.utc) + delta).timestamp()
        assert abs(payload["exp"] - expected_exp) < 5  # within 5 s clock drift

    def test_expired_token_raises_expired_signature_error(self):
        token = create_access_token(user_id=1, username="alice", expires_delta=timedelta(seconds=-1))
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)

    def test_tampered_token_raises(self):
        token = create_access_token(user_id=1, username="alice")
        corrupted = token[:-4] + "XXXX"
        with pytest.raises(Exception):
            decode_token(corrupted)

    def test_garbage_token_raises(self):
        with pytest.raises(Exception):
            decode_token("not.a.jwt.at.all")


# ── get_current_username dependency ───────────────────────────────────────────


class TestGetCurrentUsername:
    """get_current_username can be called directly (FastAPI Depends is just metadata)."""

    def test_returns_username_for_valid_token(self):
        token = create_access_token(user_id=1, username="alice")
        assert get_current_username(token) == "alice"

    def test_raises_http_401_for_expired_token(self):
        token = create_access_token(user_id=1, username="alice", expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc:
            get_current_username(token)
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()

    def test_raises_http_401_for_invalid_token_string(self):
        with pytest.raises(HTTPException) as exc:
            get_current_username("garbage.token.value")
        assert exc.value.status_code == 401

    def test_raises_http_401_when_username_missing_from_payload(self):
        settings = get_settings()
        payload = {
            "user_id": 99,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        token = pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc:
            get_current_username(token)
        assert exc.value.status_code == 401
        assert "username" in exc.value.detail.lower()
