"""Tests for router/algorithm_router.py.

Covers the recnexteval registry boundary: ALGORITHM_REGISTRY.get raises
KeyError when a name is missing (real library behaviour), and the broad
except-block must convert any exception into HTTP 500.
"""

from unittest.mock import MagicMock

import pytest

_PREFIX = "/api/v1/algorithm"


def _patch_registry(mocker, mock_reg):
    mocker.patch(
        "recnexteval_studio_backend.router.algorithm_router.ALGORITHM_REGISTRY",
        mock_reg,
    )


# ── list ─────────────────────────────────────────────────────────────────────


class TestListAlgorithms:
    def test_returns_registered_algorithms(self, client, mocker):
        class FakeAlgo:
            """Alternating Least Squares."""

        mock_reg = MagicMock()
        mock_reg.registered_items.return_value = [("als", FakeAlgo)]
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/list")

        assert resp.status_code == 200
        data = resp.json()
        assert data == [{"name": "als", "description": "Alternating Least Squares."}]

    def test_returns_empty_list_when_registry_is_empty(self, client, mocker):
        mock_reg = MagicMock()
        mock_reg.registered_items.return_value = []
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/list")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_falls_back_to_default_description_when_docstring_missing(self, client, mocker):
        class NoDocAlgo:
            pass

        NoDocAlgo.__doc__ = None

        mock_reg = MagicMock()
        mock_reg.registered_items.return_value = [("nodoc", NoDocAlgo)]
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/list")

        assert resp.status_code == 200
        assert resp.json()[0]["description"] == "No description provided."

    def test_multiple_algorithms_returned(self, client, mocker):
        class A:
            """AlgoA."""

        class B:
            """AlgoB."""

        mock_reg = MagicMock()
        mock_reg.registered_items.return_value = [("a", A), ("b", B)]
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/list")

        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()]
        assert names == ["a", "b"]


# ── get_params ────────────────────────────────────────────────────────────────


class TestGetAlgorithmParams:
    def test_happy_path_returns_params(self, client, mocker):
        mock_algo_cls = MagicMock()
        mock_algo_cls.get_default_params.return_value = {"num_factors": 10, "lr": 0.01}

        mock_reg = MagicMock()
        mock_reg.get.return_value = mock_algo_cls
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_params/als")

        assert resp.status_code == 200
        assert resp.json() == {"num_factors": 10, "lr": 0.01}

    def test_none_return_from_registry_gives_500(self, client, mocker):
        # The router raises HTTPException(404) for a None return, but that
        # HTTPException is immediately caught by the broad `except Exception`
        # block and re-raised as 500. This documents the current (buggy) behaviour;
        # if the router is fixed to exclude HTTPException from the broad catch,
        # update the expected status to 404.
        mock_reg = MagicMock()
        mock_reg.get.return_value = None
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_params/unknown")

        assert resp.status_code == 500

    def test_keyerror_from_registry_gives_500(self, client, mocker):
        # Real recnexteval behaviour: Registry.get raises KeyError for unknown names
        mock_reg = MagicMock()
        mock_reg.get.side_effect = KeyError("unknown_algo")
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_params/unknown_algo")

        assert resp.status_code == 500
        assert "failed" in resp.json()["detail"].lower()

    def test_get_default_params_runtime_error_gives_500(self, client, mocker):
        mock_algo_cls = MagicMock()
        mock_algo_cls.get_default_params.side_effect = RuntimeError("recnexteval internal error")

        mock_reg = MagicMock()
        mock_reg.get.return_value = mock_algo_cls
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_params/als")

        assert resp.status_code == 500

    def test_get_default_params_attribute_error_gives_500(self, client, mocker):
        mock_algo_cls = MagicMock()
        del mock_algo_cls.get_default_params

        mock_reg = MagicMock()
        mock_reg.get.return_value = mock_algo_cls
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_params/als")

        assert resp.status_code == 500
