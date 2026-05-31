import logging
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd
from recnexteval.evaluators import MetricLevelEnum
from sqlalchemy.orm import Session

from ...db.schema import (
    MacroEvaluationResult,
    MicroEvaluationResult,
    StreamAlgorithm,
    UserEvaluationResult,
    WindowEvaluationResult,
)
from .protocols import PipelineProtocol

logger = logging.getLogger(__name__)

ColumnExtractor = Callable[[Any], Any]


class AlgorithmNotFoundError(Exception):
    """Raised when a required StreamAlgorithm UUID cannot be resolved."""


@dataclass(frozen=True)
class LevelSpec:
    level: MetricLevelEnum
    model: type[Any]
    columns: dict[str, ColumnExtractor]


def _parse_uuid(algorithm_str: str) -> uuid.UUID | None:
    """Extract the UUID suffix from a `name_<uuid>` string."""
    if not algorithm_str:
        return None
    raw = algorithm_str.split("_")[-1]
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


LEVEL_SPECS: tuple[LevelSpec, ...] = (
    LevelSpec(
        level=MetricLevelEnum.MACRO,
        model=MacroEvaluationResult,
        columns={
            "metric": lambda r: r.metric,
            "macro_score": lambda r: float(r.macro_score),
            "num_window": lambda r: int(r.num_window),
        },
    ),
    LevelSpec(
        level=MetricLevelEnum.MICRO,
        model=MicroEvaluationResult,
        columns={
            "metric": lambda r: r.metric,
            "micro_score": lambda r: float(r.micro_score),
            "num_user": lambda r: int(r.num_user),
        },
    ),
    LevelSpec(
        level=MetricLevelEnum.WINDOW,
        model=WindowEvaluationResult,
        columns={
            "metric": lambda r: r.metric,
            "window_score": lambda r: float(getattr(r, "window_score", 0)),
            "num_user": lambda r: int(getattr(r, "num_user", 0)),
            "timestamp": lambda r: str(getattr(r, "timestamp", "")),
        },
    ),
    LevelSpec(
        level=MetricLevelEnum.USER,
        model=UserEvaluationResult,
        columns={
            "metric": lambda r: r.metric,
            "user_score": lambda r: float(getattr(r, "user_score", 0)),
            "user_id": lambda r: int(getattr(r, "user_id", 0)),
            "timestamp": lambda r: str(getattr(r, "timestamp", "")),
        },
    ),
)


class AlgorithmResolver:
    """Resolves StreamAlgorithm rows from `name_<uuid>` strings. Caches per instance."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._cache: dict[str, StreamAlgorithm | None] = {}

    def resolve(self, algorithm_str: str) -> StreamAlgorithm:
        """Return the matching StreamAlgorithm or raise AlgorithmNotFoundError."""
        if algorithm_str not in self._cache:
            algo_uuid = _parse_uuid(algorithm_str)
            if algo_uuid is None:
                self._cache[algorithm_str] = None
            else:
                self._cache[algorithm_str] = (
                    self._db.query(StreamAlgorithm)
                    .filter(StreamAlgorithm.algorithm_uuid == algo_uuid)
                    .first()
                )
        result = self._cache[algorithm_str]
        if result is None:
            raise AlgorithmNotFoundError(
                f"StreamAlgorithm with UUID suffix of {algorithm_str!r} not found"
            )
        return result


class ResultPersister:
    """Config-driven persistence of metric-level DataFrames.

    Does NOT commit; the orchestrator owns transaction boundaries.
    Exceptions propagate; no silent swallowing.
    """

    def __init__(self, db: Session, *, algorithm_resolver: AlgorithmResolver | None = None) -> None:
        self._db = db
        self._algos = algorithm_resolver or AlgorithmResolver(db)

    def persist(self, spec: LevelSpec, df: pd.DataFrame, stream_job_id: int) -> int:
        """Add ORM rows for one metric level. Returns count added. Does not commit."""
        count = 0
        for row in df.itertuples():
            algorithm_str = getattr(row, "algorithm", "")
            stream_algorithm = self._algos.resolve(algorithm_str)
            fields = {
                "stream_job_id": stream_job_id,
                "stream_algorithm_id": stream_algorithm.id,
            }
            for field, extractor in spec.columns.items():
                fields[field] = extractor(row)
            self._db.add(spec.model(**fields))
            count += 1
        logger.info("Persisted %d %s rows", count, spec.level)
        return count

    def persist_all(
        self,
        pipeline: PipelineProtocol,
        stream_job_id: int,
        specs: Iterable[LevelSpec] = LEVEL_SPECS,
    ) -> dict[MetricLevelEnum, int]:
        """For each spec fetch the DataFrame from the pipeline and persist rows."""
        counts: dict[MetricLevelEnum, int] = {}
        for spec in specs:
            try:
                df = pipeline.metric_results(spec.level).reset_index()
                logger.info("Processing %s results, shape: %s", spec.level, df.shape)
                counts[spec.level] = self.persist(spec, df, stream_job_id)
            except AlgorithmNotFoundError:
                raise
            except Exception as exc:
                logger.warning("No %s results available: %s", spec.level, exc)
                counts[spec.level] = 0
        return counts
