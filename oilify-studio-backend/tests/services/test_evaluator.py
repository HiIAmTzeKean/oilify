"""Tests for services/evaluator.py — run_evaluation orchestration.

All external I/O (database, recnexteval library, ResultPersister) is mocked so
that each test exercises exactly one failure mode or success path.
"""

import uuid
from unittest.mock import MagicMock

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_mock_job(
    *,
    job_id: int = 1,
    dataset: str = "ml-1m",
    has_algorithms: bool = True,
    parameters: str | None = '{"num_factors": 10}',
) -> MagicMock:
    """Return a mock StreamJob with sensible defaults."""
    job = MagicMock()
    job.id = job_id
    job.dataset = dataset
    job.timestamp_split_start.timestamp.return_value = 1_704_067_200.0
    job.window_size = 7
    job.top_k = 10
    job.metrics = ["ndcg"]
    job.completed_at = None
    job.error_message = None

    if has_algorithms:
        algo = MagicMock()
        algo.algorithm_name = "als"
        algo.algorithm_uuid = uuid.uuid4()
        algo.parameters = parameters
        job.stream_algorithms = [algo]
    else:
        job.stream_algorithms = []

    return job


def _patch_db(mocker, job: MagicMock) -> MagicMock:
    """Mock get_database_manager so the evaluator uses `job` as the StreamJob."""
    sess = MagicMock()
    sess.query.return_value.filter.return_value.first.return_value = job

    mgr = MagicMock()
    mgr.get_session.return_value = sess

    mocker.patch(
        "recnexteval_studio_backend.services.evaluator.get_database_manager",
        return_value=mgr,
    )
    return sess


def _patch_recnexteval(mocker) -> tuple[MagicMock, MagicMock]:
    """Stub all recnexteval calls; return (evaluator_mock, builder_mock)."""
    dataset_cls = MagicMock()
    dataset_cls.return_value.load.return_value = MagicMock()
    mock_dataset_reg = MagicMock()
    mock_dataset_reg.get.return_value = dataset_cls
    mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)

    mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

    evaluator = MagicMock()
    builder = MagicMock()
    builder.build.return_value = evaluator
    mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

    mock_algo_reg = MagicMock()
    mock_algo_reg.get.return_value = MagicMock()
    mocker.patch(
        "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
        mock_algo_reg,
    )

    mocker.patch("recnexteval_studio_backend.services.evaluator.ResultPersister")

    return evaluator, builder


# ── tests ─────────────────────────────────────────────────────────────────────


class TestRunEvaluation:
    def test_happy_path_sets_completed_at(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval(mocker)

        run_evaluation(job.id)

        assert job.completed_at is not None
        assert job.error_message is None

    def test_happy_path_commits_session(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        sess = _patch_db(mocker, job)
        _patch_recnexteval(mocker)

        run_evaluation(job.id)

        sess.commit.assert_called()

    def test_happy_path_calls_evaluator_run(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        evaluator, _ = _patch_recnexteval(mocker)

        run_evaluation(job.id)

        evaluator.run.assert_called_once()

    def test_session_is_always_closed_on_success(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        sess = _patch_db(mocker, job)
        _patch_recnexteval(mocker)

        run_evaluation(job.id)

        sess.close.assert_called_once()

    def test_session_is_always_closed_on_error(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        sess = _patch_db(mocker, job)

        mock_dataset_reg = MagicMock()
        mock_dataset_reg.get.side_effect = RuntimeError("boom")
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)

        run_evaluation(job.id)

        sess.close.assert_called_once()

    def test_job_not_found_does_not_commit(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        sess = MagicMock()
        sess.query.return_value.filter.return_value.first.return_value = None
        mgr = MagicMock()
        mgr.get_session.return_value = sess
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.get_database_manager",
            return_value=mgr,
        )

        run_evaluation(99_999)

        sess.commit.assert_not_called()

    def test_dataset_load_error_records_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        mock_dataset_reg = MagicMock()
        mock_dataset_reg.get.side_effect = RuntimeError("dataset unavailable")
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)

        run_evaluation(job.id)

        assert job.error_message == "dataset unavailable"
        assert job.completed_at is not None

    def test_window_setup_error_records_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        dataset_cls = MagicMock()
        dataset_cls.return_value.load.return_value = MagicMock()
        mock_dataset_reg = MagicMock()
        mock_dataset_reg.get.return_value = dataset_cls
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)
        mocker.patch(
            "recnexteval.settings.SlidingWindowSetting",
            side_effect=ValueError("bad window config"),
        )

        run_evaluation(job.id)

        assert job.error_message == "bad window config"
        assert job.completed_at is not None

    def test_evaluator_run_error_records_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        dataset_cls = MagicMock()
        dataset_cls.return_value.load.return_value = MagicMock()
        mock_dataset_reg = MagicMock()
        mock_dataset_reg.get.return_value = dataset_cls
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

        failing_evaluator = MagicMock()
        failing_evaluator.run.side_effect = RuntimeError("evaluation crashed")
        builder = MagicMock()
        builder.build.return_value = failing_evaluator
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.return_value = MagicMock()
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )

        run_evaluation(job.id)

        assert job.error_message == "evaluation crashed"
        assert job.completed_at is not None

    def test_algorithm_with_null_parameters_uses_empty_dict(self, mocker):
        """parameters=None must be treated as {} when building the pipeline."""
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job(parameters=None)
        _patch_db(mocker, job)

        dataset_cls = MagicMock()
        dataset_cls.return_value.load.return_value = MagicMock()
        mock_dataset_reg = MagicMock()
        mock_dataset_reg.get.return_value = dataset_cls
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

        evaluator = MagicMock()
        builder = MagicMock()
        builder.build.return_value = evaluator
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.return_value = MagicMock()
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )
        mocker.patch("recnexteval_studio_backend.services.evaluator.ResultPersister")

        run_evaluation(job.id)

        # builder.add_algorithm must have been called with params={}
        calls = builder.add_algorithm.call_args_list
        assert calls, "add_algorithm should have been called"
        assert all(c.kwargs.get("params") == {} for c in calls)

    def test_unknown_algorithm_is_skipped_in_pipeline(self, mocker):
        """If ALGORITHM_REGISTRY.get returns None, that algorithm is skipped (not added)."""
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        dataset_cls = MagicMock()
        dataset_cls.return_value.load.return_value = MagicMock()
        mock_dataset_reg = MagicMock()
        mock_dataset_reg.get.return_value = dataset_cls
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

        evaluator = MagicMock()
        builder = MagicMock()
        builder.build.return_value = evaluator
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.return_value = None  # algorithm not found in registry
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )
        mocker.patch("recnexteval_studio_backend.services.evaluator.ResultPersister")

        run_evaluation(job.id)

        builder.add_algorithm.assert_not_called()
        assert job.completed_at is not None
