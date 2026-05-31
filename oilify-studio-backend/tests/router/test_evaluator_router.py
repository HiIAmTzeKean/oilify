"""Integration tests for router/evaluator_router.py.

`run_evaluation` is mocked in every test so the background task never touches
recnexteval or PostgreSQL. Database state is set up via `router_stream_job`.
"""

import json
import uuid
from datetime import datetime, timezone

import pytest

from recnexteval_studio_backend.db.schema import (
    MacroEvaluationResult,
    MicroEvaluationResult,
    StreamAlgorithm,
)

_PREFIX = "/api/v1/evaluator"


def _patch_run_eval(mocker):
    return mocker.patch(
        "recnexteval_studio_backend.router.evaluator_router.run_evaluation",
        return_value=None,
    )


# ── POST /{stream_job_id}/run ─────────────────────────────────────────────────


class TestRunStreamJob:
    def test_starts_job_with_algorithms(self, client, mocker, router_stream_job):
        _patch_run_eval(mocker)
        job_id = router_stream_job(has_algorithms=True)

        resp = client.post(f"{_PREFIX}/{job_id}/run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_run_enqueues_background_task(self, client, mocker, router_stream_job):
        mock_fn = _patch_run_eval(mocker)
        job_id = router_stream_job(has_algorithms=True)

        client.post(f"{_PREFIX}/{job_id}/run")

        mock_fn.assert_called_once_with(job_id)

    def test_job_without_algorithms_returns_400(self, client, mocker, router_stream_job):
        _patch_run_eval(mocker)
        job_id = router_stream_job(has_algorithms=False)

        resp = client.post(f"{_PREFIX}/{job_id}/run")
        assert resp.status_code == 400
        assert "no algorithms" in resp.json()["detail"].lower()

    def test_already_started_job_returns_400(self, client, mocker, router_stream_job):
        _patch_run_eval(mocker)
        job_id = router_stream_job(has_algorithms=True, started=True)

        resp = client.post(f"{_PREFIX}/{job_id}/run")
        assert resp.status_code == 400
        assert "already started" in resp.json()["detail"].lower()

    def test_nonexistent_job_returns_404(self, client, mocker):
        _patch_run_eval(mocker)
        resp = client.post(f"{_PREFIX}/999999/run")
        assert resp.status_code == 404


# ── POST /{stream_job_id}/rerun ───────────────────────────────────────────────


class TestRerunStreamJob:
    def test_rerun_completed_job_succeeds(self, client, mocker, router_stream_job):
        _patch_run_eval(mocker)
        job_id = router_stream_job(has_algorithms=True, completed=True)

        resp = client.post(f"{_PREFIX}/{job_id}/rerun")
        assert resp.status_code == 200
        assert "rerun" in resp.json()["message"].lower()

    def test_rerun_clears_previous_results(self, client, mocker, router_stream_job, session_factory):
        _patch_run_eval(mocker)
        job_id = router_stream_job(has_algorithms=True, completed=True)

        # Insert a macro result so we can verify it's removed on rerun
        sess = session_factory()
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        if algo:
            result = MacroEvaluationResult(
                stream_job_id=job_id,
                stream_algorithm_id=algo.id,
                metric="ndcg",
                macro_score=0.5,
                num_window=3,
            )
            sess.add(result)
            sess.commit()
        sess.close()

        client.post(f"{_PREFIX}/{job_id}/rerun")

        # Verify the result was deleted
        verify = session_factory()
        remaining = verify.query(MacroEvaluationResult).filter_by(stream_job_id=job_id).count()
        verify.close()
        assert remaining == 0

    def test_rerun_not_completed_job_returns_400(self, client, mocker, router_stream_job):
        _patch_run_eval(mocker)
        # A job that was started but not completed
        job_id = router_stream_job(has_algorithms=True, started=True)

        resp = client.post(f"{_PREFIX}/{job_id}/rerun")
        assert resp.status_code == 400
        assert "not completed" in resp.json()["detail"].lower()

    def test_rerun_nonexistent_job_returns_404(self, client, mocker):
        _patch_run_eval(mocker)
        resp = client.post(f"{_PREFIX}/999999/rerun")
        assert resp.status_code == 404


# ── GET /{stream_job_id}/results ─────────────────────────────────────────────


class TestGetEvaluationResults:
    def test_returns_empty_result_structure_for_new_job(self, client, router_stream_job):
        job_id = router_stream_job()
        resp = client.get(f"{_PREFIX}/{job_id}/results")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"macro", "micro", "window", "user"}
        assert body["macro"] == []
        assert body["micro"] == []
        assert body["window"] == []
        assert body["user"] == []

    def test_returns_macro_results_after_evaluation(self, client, router_stream_job, session_factory):
        job_id = router_stream_job(has_algorithms=True, completed=True)

        # Directly insert a macro result
        sess = session_factory()
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        sess.add(
            MacroEvaluationResult(
                stream_job_id=job_id,
                stream_algorithm_id=algo.id,
                metric="ndcg",
                macro_score=0.72,
                num_window=5,
            )
        )
        sess.commit()
        sess.close()

        resp = client.get(f"{_PREFIX}/{job_id}/results")
        assert resp.status_code == 200
        macro = resp.json()["macro"]
        assert len(macro) == 1
        assert macro[0]["metric"] == "ndcg"
        assert macro[0]["score"] == pytest.approx(0.72)
        assert macro[0]["num_window"] == 5
        assert macro[0]["algorithm"] == "als"

    def test_returns_micro_results_after_evaluation(self, client, router_stream_job, session_factory):
        job_id = router_stream_job(has_algorithms=True, completed=True)

        sess = session_factory()
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        sess.add(
            MicroEvaluationResult(
                stream_job_id=job_id,
                stream_algorithm_id=algo.id,
                metric="precision",
                micro_score=0.45,
                num_user=200,
            )
        )
        sess.commit()
        sess.close()

        resp = client.get(f"{_PREFIX}/{job_id}/results")
        micro = resp.json()["micro"]
        assert len(micro) == 1
        assert micro[0]["metric"] == "precision"
        assert micro[0]["score"] == pytest.approx(0.45)

    def test_result_items_have_required_fields(self, client, router_stream_job, session_factory):
        job_id = router_stream_job(has_algorithms=True, completed=True)

        sess = session_factory()
        algo = sess.query(StreamAlgorithm).filter_by(stream_job_id=job_id).first()
        sess.add(
            MacroEvaluationResult(
                stream_job_id=job_id,
                stream_algorithm_id=algo.id,
                metric="ndcg",
                macro_score=0.5,
                num_window=2,
            )
        )
        sess.commit()
        sess.close()

        resp = client.get(f"{_PREFIX}/{job_id}/results")
        item = resp.json()["macro"][0]
        for field in ("id", "algorithm", "metric", "score", "num_window"):
            assert field in item

    def test_nonexistent_job_returns_404(self, client):
        resp = client.get(f"{_PREFIX}/999999/results")
        assert resp.status_code == 404
