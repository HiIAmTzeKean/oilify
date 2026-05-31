"""Additional error-path tests for services/evaluation/persisters.py.

Supplements test_result_persister.py with:
  - persist_all swallows non-AlgorithmNotFoundError exceptions per level and continues
  - persist_all re-raises AlgorithmNotFoundError and stops
  - Error in one level does not block other levels from persisting
"""

import uuid
from unittest.mock import MagicMock

import pandas as pd
import pytest
from recnexteval.evaluators import MetricLevelEnum

from recnexteval_studio_backend.services.evaluation.persisters import (
    LEVEL_SPECS,
    AlgorithmNotFoundError,
    ResultPersister,
)


def _spec(level_name: str):
    target = MetricLevelEnum[level_name.upper()]
    return next(s for s in LEVEL_SPECS if s.level == target)


# ── persist_all error handling ────────────────────────────────────────────────


class TestPersistAllErrorHandling:
    def test_swallows_runtimeerror_for_one_level_and_continues(self, db, stream_job_factory):
        algo_uuid = str(uuid.uuid4())
        job = stream_job_factory(algorithms=[{"name": "als", "uuid": algo_uuid}])

        micro_df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "ndcg",
            "micro_score": 0.3,
            "num_user": 10,
        }])

        pipeline = MagicMock()
        def _results(level):
            if level == MetricLevelEnum.MACRO:
                raise RuntimeError("no macro results from recnexteval")
            if level == MetricLevelEnum.MICRO:
                return micro_df
            return pd.DataFrame()

        pipeline.metric_results.side_effect = _results

        persister = ResultPersister(db)
        counts = persister.persist_all(pipeline, job.id)

        assert counts[MetricLevelEnum.MACRO] == 0
        assert counts[MetricLevelEnum.MICRO] == 1

    def test_swallows_valueerror_for_one_level_and_continues(self, db, stream_job_factory):
        algo_uuid = str(uuid.uuid4())
        job = stream_job_factory(algorithms=[{"name": "als", "uuid": algo_uuid}])

        macro_df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "ndcg",
            "macro_score": 0.5,
            "num_window": 2,
        }])

        pipeline = MagicMock()
        def _results(level):
            if level == MetricLevelEnum.MICRO:
                raise ValueError("no micro-level data available")
            if level == MetricLevelEnum.MACRO:
                return macro_df
            return pd.DataFrame()

        pipeline.metric_results.side_effect = _results

        persister = ResultPersister(db)
        counts = persister.persist_all(pipeline, job.id)

        assert counts[MetricLevelEnum.MICRO] == 0
        assert counts[MetricLevelEnum.MACRO] == 1

    def test_reraises_algorithm_not_found_error(self, db, stream_job_factory):
        job = stream_job_factory()
        bad_uuid = str(uuid.uuid4())

        df = pd.DataFrame([{
            "algorithm": f"als_{bad_uuid}",
            "metric": "ndcg",
            "macro_score": 0.5,
            "num_window": 1,
        }])

        pipeline = MagicMock()
        pipeline.metric_results.return_value = df

        persister = ResultPersister(db)
        with pytest.raises(AlgorithmNotFoundError):
            persister.persist_all(pipeline, job.id, specs=[_spec("MACRO")])

    def test_all_levels_return_zero_when_all_raise(self, db, stream_job_factory):
        job = stream_job_factory()

        pipeline = MagicMock()
        pipeline.metric_results.side_effect = RuntimeError("pipeline unavailable")

        persister = ResultPersister(db)
        counts = persister.persist_all(pipeline, job.id)

        assert all(c == 0 for c in counts.values())
        assert len(counts) == len(LEVEL_SPECS)

    def test_error_in_early_level_does_not_prevent_later_levels(self, db, stream_job_factory):
        algo_uuid = str(uuid.uuid4())
        job = stream_job_factory(algorithms=[{"name": "als", "uuid": algo_uuid}])

        window_df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "ndcg",
            "window_score": 0.6,
            "num_user": 5,
            "timestamp": "2024-01-01",
        }])

        pipeline = MagicMock()
        def _results(level):
            if level in (MetricLevelEnum.MACRO, MetricLevelEnum.MICRO):
                raise RuntimeError("not computed")
            if level == MetricLevelEnum.WINDOW:
                return window_df
            return pd.DataFrame()

        pipeline.metric_results.side_effect = _results

        persister = ResultPersister(db)
        counts = persister.persist_all(pipeline, job.id)

        assert counts[MetricLevelEnum.MACRO] == 0
        assert counts[MetricLevelEnum.MICRO] == 0
        assert counts[MetricLevelEnum.WINDOW] == 1
