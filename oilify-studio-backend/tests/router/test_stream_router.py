"""Integration tests for router/stream_router.py.

ALGORITHM_REGISTRY and recnexteval.utils calls are mocked so tests remain
independent of the recnexteval library's actual registered algorithms.
"""

import uuid
from unittest.mock import MagicMock

import pytest

_PREFIX = "/api/v1/stream"

# Names used when simulating a registered algorithm
_REGISTERED_ALGO = "als"
_UNREGISTERED_ALGO = "nonexistent_algo"


def _mock_registry(mocker, *, registered: list[str] | None = None):
    """Patch ALGORITHM_REGISTRY in stream_router and recnexteval.utils.generate_algorithm_uuid."""
    registered = registered or [_REGISTERED_ALGO]

    mock_reg = MagicMock()
    mock_reg.get_registered_keys.return_value = registered
    mock_reg.__contains__ = MagicMock(side_effect=lambda name: name in registered)
    mocker.patch(
        "recnexteval_studio_backend.router.stream_router.ALGORITHM_REGISTRY",
        mock_reg,
    )
    mocker.patch(
        "recnexteval.utils.generate_algorithm_uuid",
        return_value=uuid.uuid4(),
    )
    return mock_reg


# ── POST /stream/create_stream ────────────────────────────────────────────────


class TestCreateStream:
    _VALID_PAYLOAD = {
        "name": None,  # filled per test to avoid unique-name collisions
        "description": "test stream",
        "dataset": "movielens",
        "top_k": 10,
        "metrics": ["ndcg"],
        "timestamp_split_start": "2024-01-01T00:00:00Z",
        "window_size": 7,
    }

    def _payload(self, name: str | None = None) -> dict:
        p = dict(self._VALID_PAYLOAD)
        p["name"] = name or f"stream-{uuid.uuid4().hex}"
        return p

    def test_creates_stream_and_returns_job_id(self, client):
        resp = client.post(f"{_PREFIX}/create_stream", json=self._payload())
        assert resp.status_code == 200
        body = resp.json()
        assert "stream_job_id" in body
        assert body["status"] == "created"

    def test_invalid_iso_timestamp_returns_400(self, client):
        payload = self._payload()
        payload["timestamp_split_start"] = "not-a-date"
        resp = client.post(f"{_PREFIX}/create_stream", json=payload)
        assert resp.status_code == 400

    def test_duplicate_name_is_rejected(self, client):
        name = f"unique-{uuid.uuid4().hex}"
        r1 = client.post(f"{_PREFIX}/create_stream", json=self._payload(name))
        assert r1.status_code == 200

        r2 = client.post(f"{_PREFIX}/create_stream", json=self._payload(name))
        assert r2.status_code == 409

    def test_missing_required_field_returns_422(self, client):
        payload = self._payload()
        del payload["dataset"]
        resp = client.post(f"{_PREFIX}/create_stream", json=payload)
        assert resp.status_code == 422


# ── GET /stream/list_available ────────────────────────────────────────────────


class TestListAvailableStreams:
    def test_returns_list(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        router_stream_job()  # unstarted job
        resp = client.get(f"{_PREFIX}/list_available")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_excludes_started_jobs(self, client, mocker, router_stream_job, session_factory, router_user):
        _mock_registry(mocker)
        router_stream_job(started=True)  # should be excluded
        unstarted_id = router_stream_job()

        resp = client.get(f"{_PREFIX}/list_available")
        ids = [j["id"] for j in resp.json()]
        assert unstarted_id in ids

    def test_response_items_contain_required_fields(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        router_stream_job()
        resp = client.get(f"{_PREFIX}/list_available")
        for item in resp.json():
            for field in ("id", "name", "status", "dataset", "top_k", "metrics", "algorithms"):
                assert field in item


# ── GET /stream/list_all ──────────────────────────────────────────────────────


class TestListAllStreams:
    def test_returns_all_jobs_including_started(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        unstarted = router_stream_job()
        started = router_stream_job(started=True)

        resp = client.get(f"{_PREFIX}/list_all")
        assert resp.status_code == 200
        ids = [j["id"] for j in resp.json()]
        assert unstarted in ids
        assert started in ids

    def test_response_items_have_timestamps(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        router_stream_job(completed=True)
        resp = client.get(f"{_PREFIX}/list_all")
        completed = [j for j in resp.json() if j.get("completed_at") is not None]
        assert completed  # at least one completed job with timestamp


# ── POST /{stream_job_id}/add_algorithms ──────────────────────────────────────


class TestAddAlgorithms:
    def test_adds_algorithm_to_unstarted_job(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        job_id = router_stream_job()

        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [{"name": _REGISTERED_ALGO, "params": {}}]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["stream_job_id"] == job_id
        assert "Successfully added" in body["message"]

    def test_add_to_started_job_returns_400(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        job_id = router_stream_job(started=True)

        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [{"name": _REGISTERED_ALGO, "params": {}}]},
        )
        assert resp.status_code == 400

    def test_unregistered_algorithm_returns_404(self, client, mocker, router_stream_job):
        _mock_registry(mocker, registered=[_REGISTERED_ALGO])  # _UNREGISTERED_ALGO not in list
        job_id = router_stream_job()

        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [{"name": _UNREGISTERED_ALGO, "params": {}}]},
        )
        assert resp.status_code == 404

    def test_nonexistent_job_returns_404(self, client, mocker):
        _mock_registry(mocker)
        resp = client.post(
            f"{_PREFIX}/999999/add_algorithms",
            json={"algorithms": [{"name": _REGISTERED_ALGO, "params": {}}]},
        )
        assert resp.status_code == 404

    def test_status_reflects_ready_after_adding_algorithm(self, client, mocker, router_stream_job):
        _mock_registry(mocker)
        job_id = router_stream_job()
        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [{"name": _REGISTERED_ALGO, "params": {}}]},
        )
        assert resp.json()["status"] == "ready"

    def test_update_by_id_updates_params_without_inserting_new_row(
        self, client, mocker, router_stream_job, session_factory
    ):
        _mock_registry(mocker)
        job_id = router_stream_job(has_algorithms=True)

        sess = session_factory()
        from recnexteval_studio_backend.db.schema import StreamAlgorithm
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        algo_id = algo.id
        sess.close()

        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [{"id": algo_id, "name": _REGISTERED_ALGO, "params": {"num_factors": 50}}]},
        )
        assert resp.status_code == 200

        sess = session_factory()
        rows = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).all()
        sess.close()
        assert len(rows) == 1
        import json as _json
        assert _json.loads(rows[0].parameters)["num_factors"] == 50

    def test_two_no_id_entries_with_same_name_creates_two_distinct_rows(
        self, client, mocker, router_stream_job, session_factory
    ):
        _mock_registry(mocker)
        job_id = router_stream_job()

        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [
                {"name": _REGISTERED_ALGO, "params": {"k": 5}},
                {"name": _REGISTERED_ALGO, "params": {"k": 10}},
            ]},
        )
        assert resp.status_code == 200

        sess = session_factory()
        from recnexteval_studio_backend.db.schema import StreamAlgorithm
        rows = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).all()
        uuids = [r.algorithm_uuid for r in rows]
        sess.close()
        assert len(rows) == 2
        assert uuids[0] != uuids[1]

    def test_update_with_id_not_belonging_to_stream_returns_404(
        self, client, mocker, router_stream_job
    ):
        _mock_registry(mocker)
        job_id = router_stream_job()

        resp = client.post(
            f"{_PREFIX}/{job_id}/add_algorithms",
            json={"algorithms": [{"id": 999999, "name": _REGISTERED_ALGO, "params": {}}]},
        )
        assert resp.status_code == 404


# ── DELETE /{stream_job_id} ───────────────────────────────────────────────────


class TestDeleteStream:
    def test_deletes_existing_job(self, client, router_stream_job):
        job_id = router_stream_job()
        resp = client.delete(f"{_PREFIX}/{job_id}")
        assert resp.status_code == 200
        assert str(job_id) in resp.json()["message"]

    def test_returns_404_for_unknown_job(self, client):
        resp = client.delete(f"{_PREFIX}/999999")
        assert resp.status_code == 404

    def test_second_delete_returns_404(self, client, router_stream_job):
        job_id = router_stream_job()
        client.delete(f"{_PREFIX}/{job_id}")
        resp = client.delete(f"{_PREFIX}/{job_id}")
        assert resp.status_code == 404


# ── DELETE /{stream_job_id}/remove_algorithm/{algorithm_id} ──────────────────


class TestRemoveAlgorithm:
    def test_removes_algorithm_from_unstarted_job(self, client, mocker, router_stream_job, session_factory):
        _mock_registry(mocker)
        job_id = router_stream_job(has_algorithms=True)

        # Retrieve the algorithm ID from the DB
        sess = session_factory()
        from recnexteval_studio_backend.db.schema import StreamAlgorithm
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        algo_id = algo.id
        sess.close()

        resp = client.delete(f"{_PREFIX}/{job_id}/remove_algorithm/{algo_id}")
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    def test_remove_from_started_job_returns_400(self, client, mocker, router_stream_job, session_factory):
        _mock_registry(mocker)
        job_id = router_stream_job(has_algorithms=True, started=True)

        sess = session_factory()
        from recnexteval_studio_backend.db.schema import StreamAlgorithm
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        algo_id = algo.id if algo else 999
        sess.close()

        resp = client.delete(f"{_PREFIX}/{job_id}/remove_algorithm/{algo_id}")
        assert resp.status_code == 400

    def test_remove_nonexistent_algorithm_returns_404(self, client, router_stream_job):
        job_id = router_stream_job()
        resp = client.delete(f"{_PREFIX}/{job_id}/remove_algorithm/999999")
        assert resp.status_code == 404
