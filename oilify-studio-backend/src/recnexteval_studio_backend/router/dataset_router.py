import logging as logger

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from recnexteval.registries import DATASET_REGISTRY

logger = logger.getLogger(__name__)


def create_dataset_router() -> APIRouter:
    router = APIRouter(prefix="/dataset", tags=["dataset"])

    @router.get("/get_dataset")
    async def get_dataset() -> list[str]:
        return await run_in_threadpool(DATASET_REGISTRY.get_registered_keys)

    @router.get("/{dataset_name}/get_timestamp_range")
    async def get_timestamp_range(dataset_name: str) -> dict[str, str]:
        dataset_cls = await run_in_threadpool(DATASET_REGISTRY.get, dataset_name)
        if not dataset_cls:
            raise ValueError(f"Dataset '{dataset_name}' is not registered.")

        dataset_instance = await run_in_threadpool(dataset_cls)
        await run_in_threadpool(dataset_instance.load)
        timestamp_range = await run_in_threadpool(dataset_instance.get_timestamp_range_in_datetime)
        return {
            "start_timestamp": timestamp_range[0].isoformat(),
            "end_timestamp": timestamp_range[1].isoformat(),
        }

    return router
