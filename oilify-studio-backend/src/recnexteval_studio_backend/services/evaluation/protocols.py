from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DatasetRegistryProtocol(Protocol):
    def get(self, name: str) -> type[Any] | None: ...


@runtime_checkable
class AlgorithmRegistryProtocol(Protocol):
    def get(self, name: str) -> type[Any] | None: ...


@runtime_checkable
class PipelineProtocol(Protocol):
    def run(self) -> None: ...
    def metric_results(self, level: Any) -> pd.DataFrame: ...


@runtime_checkable
class PipelineBuilderProtocol(Protocol):
    def add_setting(self, setting: Any) -> Any: ...
    def set_metric_k(self, k: int) -> Any: ...
    def add_metric(self, name: str) -> Any: ...
    def add_algorithm(self, *, algorithm: type[Any], params: dict[str, Any], algo_uuid: Any) -> Any: ...
    def build(self) -> PipelineProtocol: ...


def default_dataset_registry() -> DatasetRegistryProtocol:
    import recnexteval.registries
    return recnexteval.registries.DATASET_REGISTRY  # type: ignore[return-value]


def default_algorithm_registry() -> AlgorithmRegistryProtocol:
    import recnexteval.registries
    return recnexteval.registries.ALGORITHM_REGISTRY  # type: ignore[return-value]


def default_pipeline_builder_class() -> type[PipelineBuilderProtocol]:
    import recnexteval.evaluators
    return recnexteval.evaluators.EvaluatorPipelineBuilder  # type: ignore[return-value]


def default_window_setting_class() -> type[Any]:
    import recnexteval.settings
    return recnexteval.settings.SlidingWindowSetting
