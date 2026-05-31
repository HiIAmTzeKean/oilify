"""Additional error-path tests for services/evaluator.py.

Supplements test_evaluator.py with recnexteval-specific exception types and
edge cases not covered there:
  - FileNotFoundError from dataset.load()
  - EOWSettingError from setting.split()
  - TimestampAttributeMissingError from setting.split()
  - ValueError from SlidingWindowSetting (t_upper < training_t)
  - RuntimeError from EvaluatorPipelineBuilder.build()
  - ValueError from EvaluatorPipeline.run()
  - KeyError from ALGORITHM_REGISTRY.get() (real library behaviour)
  - JSONDecodeError from json.loads() on malformed parameters
"""

import json
import uuid
from unittest.mock import MagicMock

import pytest


# ── helpers (same pattern as test_evaluator.py) ───────────────────────────────


def _make_mock_job(
    *,
    job_id: int = 1,
    dataset: str = "ml-1m",
    has_algorithms: bool = True,
    parameters: str | None = '{"num_factors": 10}',
) -> MagicMock:
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
    sess = MagicMock()
    sess.query.return_value.filter.return_value.first.return_value = job

    mgr = MagicMock()
    mgr.get_session.return_value = sess

    mocker.patch(
        "recnexteval_studio_backend.services.evaluator.get_database_manager",
        return_value=mgr,
    )
    return sess


def _patch_recnexteval_up_to_dataset(mocker):
    """Stub dataset loading only; returns the mock dataset registry."""
    dataset_cls = MagicMock()
    dataset_cls.return_value.load.return_value = MagicMock()
    mock_dataset_reg = MagicMock()
    mock_dataset_reg.get.return_value = dataset_cls
    mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_dataset_reg)
    return mock_dataset_reg


def _patch_full_recnexteval(mocker):
    """Stub everything; return (evaluator, builder)."""
    _patch_recnexteval_up_to_dataset(mocker)
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


# ── dataset layer ─────────────────────────────────────────────────────────────


class TestDatasetLayerErrors:
    def test_load_filenotfounderror_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        dataset_instance = MagicMock()
        dataset_instance.load.side_effect = FileNotFoundError("data.csv not found")
        dataset_cls = MagicMock(return_value=dataset_instance)
        mock_reg = MagicMock()
        mock_reg.get.return_value = dataset_cls
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_reg)

        run_evaluation(job.id)

        assert "data.csv not found" in job.error_message
        assert job.completed_at is not None

    def test_load_oserror_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        dataset_instance = MagicMock()
        dataset_instance.load.side_effect = OSError("disk read failure")
        dataset_cls = MagicMock(return_value=dataset_instance)
        mock_reg = MagicMock()
        mock_reg.get.return_value = dataset_cls
        mocker.patch("recnexteval.registries.DATASET_REGISTRY", mock_reg)

        run_evaluation(job.id)

        assert job.error_message is not None
        assert job.completed_at is not None


# ── window / setting layer ────────────────────────────────────────────────────


class TestWindowSettingErrors:
    def test_t_upper_valueerror_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)
        mocker.patch(
            "recnexteval.settings.SlidingWindowSetting",
            side_effect=ValueError("t_upper must be greater than training_t"),
        )

        run_evaluation(job.id)

        assert "t_upper must be greater than training_t" in job.error_message
        assert job.completed_at is not None

    def test_eow_setting_error_writes_error_message(self, mocker):
        from recnexteval.settings import EOWSettingError

        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)

        mock_setting = MagicMock()
        mock_setting.split.side_effect = EOWSettingError("End of Window reached")
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=mock_setting)

        run_evaluation(job.id)

        assert job.error_message is not None
        assert job.completed_at is not None

    def test_timestamp_attribute_missing_error_writes_error_message(self, mocker):
        from recnexteval.matrix import TimestampAttributeMissingError

        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)

        mock_setting = MagicMock()
        mock_setting.split.side_effect = TimestampAttributeMissingError(
            "InteractionMatrix is missing timestamps."
        )
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=mock_setting)

        run_evaluation(job.id)

        assert job.error_message is not None
        assert job.completed_at is not None


# ── pipeline builder layer ────────────────────────────────────────────────────


class TestBuilderErrors:
    def test_build_runtimeerror_no_metrics_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

        builder = MagicMock()
        builder.build.side_effect = RuntimeError("No metrics specified")
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.return_value = MagicMock()
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )

        run_evaluation(job.id)

        assert "No metrics specified" in job.error_message
        assert job.completed_at is not None

    def test_add_metric_valueerror_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

        builder = MagicMock()
        builder.add_metric.side_effect = ValueError("Metric ndcg could not be resolved.")
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.return_value = MagicMock()
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )

        run_evaluation(job.id)

        assert job.error_message is not None
        assert job.completed_at is not None


# ── pipeline run layer ────────────────────────────────────────────────────────


class TestPipelineRunErrors:
    def test_run_valueerror_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)

        evaluator = MagicMock()
        evaluator.run.side_effect = ValueError("Cannot run 5 steps, only 2 steps left")
        _, builder = _patch_full_recnexteval(mocker)
        builder.build.return_value = evaluator

        run_evaluation(job.id)

        assert "Cannot run" in job.error_message
        assert job.completed_at is not None


# ── algorithm registry layer ──────────────────────────────────────────────────


class TestAlgorithmRegistryErrors:
    def test_algorithm_registry_keyerror_writes_error_message(self, mocker):
        """Real recnexteval Registry.get raises KeyError for unknown names.

        services/evaluator.py:70-73 has a falsy check (`if not algorithm_cls: continue`)
        that is dead code against real recnexteval since .get raises instead of
        returning None. A KeyError propagates to the outer except and sets error_message.
        """
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job()
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())

        builder = MagicMock()
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=builder)

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.side_effect = KeyError("als")
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )

        run_evaluation(job.id)

        assert job.error_message is not None
        assert job.completed_at is not None


# ── JSON decode errors ────────────────────────────────────────────────────────


class TestMalformedParameters:
    def test_malformed_json_parameters_writes_error_message(self, mocker):
        from recnexteval_studio_backend.services.evaluator import run_evaluation

        job = _make_mock_job(parameters="{not valid json")
        _patch_db(mocker, job)
        _patch_recnexteval_up_to_dataset(mocker)
        mocker.patch("recnexteval.settings.SlidingWindowSetting", return_value=MagicMock())
        mocker.patch("recnexteval.evaluators.EvaluatorPipelineBuilder", return_value=MagicMock())

        mock_algo_reg = MagicMock()
        mock_algo_reg.get.return_value = MagicMock()
        mocker.patch(
            "recnexteval_studio_backend.services.evaluator.ALGORITHM_REGISTRY",
            mock_algo_reg,
        )

        run_evaluation(job.id)

        assert job.error_message is not None
        assert job.completed_at is not None
