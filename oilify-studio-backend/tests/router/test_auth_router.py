"""Integration tests for router/auth_router.py."""

from recnexteval_studio_backend.services.auth import create_access_token

_PREFIX = "/api/v1/auth"

# ── POST /auth/token ──────────────────────────────────────────────────────────


class TestLoginEndpoint:
    def test_valid_credentials_return_bearer_token(self, auth_client, router_user):
        resp = auth_client.post(
            f"{_PREFIX}/token",
            data={"username": router_user["username"], "password": router_user["password"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_wrong_username_returns_401(self, auth_client, router_user):
        resp = auth_client.post(
            f"{_PREFIX}/token",
            data={"username": "no_such_user", "password": router_user["password"]},
        )
        assert resp.status_code == 401

    def test_wrong_password_returns_401(self, auth_client, router_user):
        resp = auth_client.post(
            f"{_PREFIX}/token",
            data={"username": router_user["username"], "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_missing_credentials_returns_422(self, auth_client):
        resp = auth_client.post(f"{_PREFIX}/token", data={})
        assert resp.status_code == 422


# ── GET /auth/me ──────────────────────────────────────────────────────────────


class TestMeEndpoint:
    def _token(self, router_user: dict) -> str:
        return create_access_token(user_id=router_user["id"], username=router_user["username"])

    def test_valid_token_returns_user_info(self, auth_client, router_user):
        token = self._token(router_user)
        resp = auth_client.get(
            f"{_PREFIX}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == router_user["username"]
        assert body["user_id"] == router_user["id"]

    def test_missing_token_returns_401(self, auth_client):
        resp = auth_client.get(f"{_PREFIX}/me")
        assert resp.status_code == 401

    def test_malformed_token_returns_401(self, auth_client):
        resp = auth_client.get(
            f"{_PREFIX}/me",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert resp.status_code == 401


# ── GET /auth/users ───────────────────────────────────────────────────────────


class TestUsersEndpoint:
    def _auth_headers(self, router_user: dict) -> dict:
        token = create_access_token(user_id=router_user["id"], username=router_user["username"])
        return {"Authorization": f"Bearer {token}"}

    def test_authenticated_request_returns_list(self, auth_client, router_user):
        resp = auth_client.get(
            f"{_PREFIX}/users",
            headers=self._auth_headers(router_user),
        )
        assert resp.status_code == 200
        users = resp.json()
        assert isinstance(users, list)
        assert any(u["username"] == router_user["username"] for u in users)

    def test_response_items_contain_id_and_username(self, auth_client, router_user):
        resp = auth_client.get(
            f"{_PREFIX}/users",
            headers=self._auth_headers(router_user),
        )
        body = resp.json()
        for item in body:
            assert "id" in item
            assert "username" in item

    def test_unauthenticated_request_returns_401(self, auth_client):
        resp = auth_client.get(f"{_PREFIX}/users")
        assert resp.status_code == 401
