"""Tests for router/metric_router.py.

Single endpoint backed by METRIC_REGISTRY from recnexteval. Errors from the
registry propagate uncaught as HTTP 500.
"""

from unittest.mock import MagicMock

import pytest

_PREFIX = "/api/v1/metric"


def _patch_registry(mocker, mock_reg):
    mocker.patch(
        "recnexteval_studio_backend.router.metric_router.METRIC_REGISTRY",
        mock_reg,
    )


class TestGetMetric:
    def test_returns_registered_metric_keys(self, client, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.return_value = ["ndcg", "recall", "precision"]
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_metric")

        assert resp.status_code == 200
        assert resp.json() == ["ndcg", "recall", "precision"]

    def test_returns_empty_list_when_no_metrics(self, client, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.return_value = []
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_metric")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_registry_runtimeerror_propagates_as_500(self, client_no_raise, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.side_effect = RuntimeError("registry unavailable")
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/get_metric")

        assert resp.status_code == 500

    def test_registry_attributeerror_propagates_as_500(self, client_no_raise, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.side_effect = AttributeError("no such attribute")
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/get_metric")

        assert resp.status_code == 500
