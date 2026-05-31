"""Tests for router/dataset_router.py.

The dataset router has no try/except blocks — errors from recnexteval (FileNotFoundError,
OSError, AttributeError, RuntimeError) propagate directly as HTTP 500.
There is also a latent bug: when a dataset name is not registered, the router
raises a bare ValueError (not HTTPException), which becomes 500 instead of 404.
These tests document that behaviour so any future fix is caught by a test change.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

_PREFIX = "/api/v1/dataset"


def _patch_registry(mocker, mock_reg):
    mocker.patch(
        "recnexteval_studio_backend.router.dataset_router.DATASET_REGISTRY",
        mock_reg,
    )


# ── get_dataset ───────────────────────────────────────────────────────────────


class TestGetDataset:
    def test_returns_registered_keys(self, client, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.return_value = ["movielens", "amazon"]
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_dataset")

        assert resp.status_code == 200
        assert resp.json() == ["movielens", "amazon"]

    def test_returns_empty_list_when_no_datasets(self, client, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.return_value = []
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/get_dataset")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_registry_error_propagates_as_500(self, client_no_raise, mocker):
        mock_reg = MagicMock()
        mock_reg.get_registered_keys.side_effect = RuntimeError("registry broken")
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/get_dataset")

        assert resp.status_code == 500


# ── get_timestamp_range ───────────────────────────────────────────────────────


class TestGetTimestampRange:
    def _make_dataset_instance(self, start, end):
        instance = MagicMock()
        instance.load.return_value = None
        instance.get_timestamp_range_in_datetime.return_value = (start, end)
        return instance

    def _make_registry(self, instance):
        cls = MagicMock(return_value=instance)
        mock_reg = MagicMock()
        mock_reg.get.return_value = cls
        return mock_reg

    def test_happy_path_returns_iso_timestamps(self, client, mocker):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 6, 1, tzinfo=timezone.utc)
        instance = self._make_dataset_instance(start, end)
        mock_reg = self._make_registry(instance)
        _patch_registry(mocker, mock_reg)

        resp = client.get(f"{_PREFIX}/movielens/get_timestamp_range")

        assert resp.status_code == 200
        body = resp.json()
        assert body["start_timestamp"] == start.isoformat()
        assert body["end_timestamp"] == end.isoformat()

    def test_unknown_dataset_none_return_gives_500(self, client_no_raise, mocker):
        # Bug: router raises bare ValueError (not HTTPException) → 500, not 404.
        # This test pins that behaviour; if a fix converts to 404, update here.
        mock_reg = MagicMock()
        mock_reg.get.return_value = None
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/not_registered/get_timestamp_range")

        assert resp.status_code == 500

    def test_unknown_dataset_keyerror_gives_500(self, client_no_raise, mocker):
        # Real recnexteval Registry.get raises KeyError for unknown names.
        mock_reg = MagicMock()
        mock_reg.get.side_effect = KeyError("not_registered")
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/not_registered/get_timestamp_range")

        assert resp.status_code == 500

    def test_load_filenotfounderror_gives_500(self, client_no_raise, mocker):
        instance = MagicMock()
        instance.load.side_effect = FileNotFoundError("data.csv not found")
        mock_reg = self._make_registry(instance)
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/movielens/get_timestamp_range")

        assert resp.status_code == 500

    def test_load_oserror_gives_500(self, client_no_raise, mocker):
        instance = MagicMock()
        instance.load.side_effect = OSError("disk error")
        mock_reg = self._make_registry(instance)
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/movielens/get_timestamp_range")

        assert resp.status_code == 500

    def test_load_runtimeerror_gives_500(self, client_no_raise, mocker):
        instance = MagicMock()
        instance.load.side_effect = RuntimeError("recnexteval dataset error")
        mock_reg = self._make_registry(instance)
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/movielens/get_timestamp_range")

        assert resp.status_code == 500

    def test_missing_get_timestamp_range_method_gives_500(self, client_no_raise, mocker):
        instance = MagicMock(spec=[])  # no attributes
        mock_reg = self._make_registry(instance)
        _patch_registry(mocker, mock_reg)

        resp = client_no_raise.get(f"{_PREFIX}/movielens/get_timestamp_range")

        assert resp.status_code == 500
