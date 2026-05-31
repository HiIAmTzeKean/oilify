import uuid
from unittest.mock import MagicMock

import pandas as pd
import pytest
from recnexteval_studio_backend.db.schema import (
    MacroEvaluationResult,
    MicroEvaluationResult,
    UserEvaluationResult,
    WindowEvaluationResult,
)
from recnexteval_studio_backend.services.evaluation.persisters import (
    LEVEL_SPECS,
    AlgorithmNotFoundError,
    AlgorithmResolver,
    ResultPersister,
)


def _spec(level_name: str):
    from recnexteval.evaluators import MetricLevelEnum
    target = MetricLevelEnum[level_name.upper()]
    return next(s for s in LEVEL_SPECS if s.level == target)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def algo_uuid():
    return str(uuid.uuid4())


@pytest.fixture
def job(stream_job_factory, algo_uuid):
    return stream_job_factory(algorithms=[{"name": "als", "uuid": algo_uuid}])


# ── AlgorithmResolver ─────────────────────────────────────────────────────────

class TestAlgorithmResolver:
    def test_resolve_returns_matching_algorithm(self, db, job):
        algo = job.stream_algorithms[0]
        resolver = AlgorithmResolver(db)
        result = resolver.resolve(f"als_{algo.algorithm_uuid}")
        assert result.id == algo.id

    def test_resolve_raises_when_not_found(self, db):
        resolver = AlgorithmResolver(db)
        with pytest.raises(AlgorithmNotFoundError):
            resolver.resolve(f"als_{uuid.uuid4()}")

    def test_resolve_raises_for_empty_string(self, db):
        resolver = AlgorithmResolver(db)
        with pytest.raises(AlgorithmNotFoundError):
            resolver.resolve("")

    def test_resolve_caches_result(self, db, job):
        algo = job.stream_algorithms[0]
        key = f"als_{algo.algorithm_uuid}"
        query_count = 0

        from sqlalchemy import event as sa_event

        @sa_event.listens_for(db.bind, "before_cursor_execute")
        def count_queries(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            if "stream_algorithm" in statement.lower():
                query_count += 1

        try:
            resolver = AlgorithmResolver(db)
            resolver.resolve(key)
            resolver.resolve(key)
            assert query_count == 1
        finally:
            sa_event.remove(db.bind, "before_cursor_execute", count_queries)


# ── ResultPersister ───────────────────────────────────────────────────────────

class TestResultPersister:
    def test_persist_macro_basic(self, db, job, algo_uuid):
        algo = job.stream_algorithms[0]
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "ndcg",
            "macro_score": 0.5,
            "num_window": 3,
        }])
        persister = ResultPersister(db)
        count = persister.persist(_spec("MACRO"), df, job.id)
        assert count == 1
        row = db.query(MacroEvaluationResult).filter_by(stream_job_id=job.id).first()
        assert row is not None
        assert row.stream_algorithm_id == algo.id
        assert abs(row.macro_score - 0.5) < 1e-9
        assert row.num_window == 3

    def test_persist_micro_basic(self, db, job, algo_uuid):
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "precision",
            "micro_score": 0.3,
            "num_user": 100,
        }])
        persister = ResultPersister(db)
        count = persister.persist(_spec("MICRO"), df, job.id)
        assert count == 1
        row = db.query(MicroEvaluationResult).filter_by(stream_job_id=job.id).first()
        assert row.micro_score == pytest.approx(0.3)

    def test_persist_window_basic(self, db, job, algo_uuid):
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "recall",
            "window_score": 0.7,
            "num_user": 50,
            "timestamp": "2024-01-02",
        }])
        persister = ResultPersister(db)
        count = persister.persist(_spec("WINDOW"), df, job.id)
        assert count == 1
        row = db.query(WindowEvaluationResult).filter_by(stream_job_id=job.id).first()
        assert row.window_score == pytest.approx(0.7)

    def test_persist_user_basic(self, db, job, algo_uuid):
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "hit_rate",
            "user_score": 0.9,
            "user_id": 42,
            "timestamp": "2024-01-02",
        }])
        persister = ResultPersister(db)
        count = persister.persist(_spec("USER"), df, job.id)
        assert count == 1
        row = db.query(UserEvaluationResult).filter_by(stream_job_id=job.id).first()
        assert row.user_id == 42

    def test_persist_raises_on_unknown_algorithm(self, db, job):
        df = pd.DataFrame([{
            "algorithm": f"als_{uuid.uuid4()}",  # UUID not in DB
            "metric": "ndcg",
            "macro_score": 0.5,
            "num_window": 3,
        }])
        persister = ResultPersister(db)
        with pytest.raises(AlgorithmNotFoundError):
            persister.persist(_spec("MACRO"), df, job.id)

    def test_persist_does_not_commit(self, db, job, algo_uuid):
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "ndcg",
            "macro_score": 0.1,
            "num_window": 1,
        }])
        persister = ResultPersister(db)
        persister.persist(_spec("MACRO"), df, job.id)
        # New object should be in session.new, not yet flushed to committed state
        assert any(isinstance(obj, MacroEvaluationResult) for obj in db.new)

    def test_persist_window_defaults_missing_optional_columns(self, db, job, algo_uuid):
        # Missing num_user and timestamp — should default to 0 and ""
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "recall",
            "window_score": 0.4,
        }])
        persister = ResultPersister(db)
        count = persister.persist(_spec("WINDOW"), df, job.id)
        assert count == 1

    def test_persist_extra_columns_are_ignored(self, db, job, algo_uuid):
        df = pd.DataFrame([{
            "algorithm": f"als_{algo_uuid}",
            "metric": "ndcg",
            "macro_score": 0.5,
            "num_window": 2,
            "extra_col": "ignored",
        }])
        persister = ResultPersister(db)
        count = persister.persist(_spec("MACRO"), df, job.id)
        assert count == 1

    def test_persist_all_iterates_all_levels(self, db, job, algo_uuid):
        from recnexteval.evaluators import MetricLevelEnum

        algo_str = f"als_{algo_uuid}"
        macro_df = pd.DataFrame([{"algorithm": algo_str, "metric": "ndcg", "macro_score": 0.1, "num_window": 1}])
        micro_df = pd.DataFrame([{"algorithm": algo_str, "metric": "ndcg", "micro_score": 0.2, "num_user": 10}])

        pipeline = MagicMock()
        def _results(level):
            if level == MetricLevelEnum.MACRO:
                return macro_df
            if level == MetricLevelEnum.MICRO:
                return micro_df
            return pd.DataFrame()

        pipeline.metric_results.side_effect = _results

        persister = ResultPersister(db)
        counts = persister.persist_all(pipeline, job.id)
        assert counts[MetricLevelEnum.MACRO] == 1
        assert counts[MetricLevelEnum.MICRO] == 1
        assert counts[MetricLevelEnum.WINDOW] == 0
        assert counts[MetricLevelEnum.USER] == 0

    def test_persist_all_propagates_algorithm_not_found(self, db, job):
        from recnexteval.evaluators import MetricLevelEnum

        bad_uuid = str(uuid.uuid4())
        df = pd.DataFrame([{"algorithm": f"als_{bad_uuid}", "metric": "ndcg", "macro_score": 0.1, "num_window": 1}])

        pipeline = MagicMock()
        pipeline.metric_results.return_value = df

        persister = ResultPersister(db)
        with pytest.raises(AlgorithmNotFoundError):
            persister.persist_all(pipeline, job.id, specs=[_spec("MACRO")])
