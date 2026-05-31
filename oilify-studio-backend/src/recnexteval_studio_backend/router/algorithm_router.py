import logging as logger

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from recnexteval.registries import ALGORITHM_REGISTRY

logger = logger.getLogger(__name__)


def create_algorithm_router() -> APIRouter:
    router = APIRouter(prefix="/algorithm", tags=["algorithm"])

    @router.get("/list")
    async def list_algorithms() -> list[dict]:
        """Get list of available algorithms from recnexteval registry."""
        items = await run_in_threadpool(ALGORITHM_REGISTRY.registered_items)
        return [
            {
                "name": key,
                "description": value.__doc__ or "No description provided."
            }
            for key, value in items
        ]

    @router.get("/get_params/{algorithm_name}")
    async def get_algorithm_params(algorithm_name: str) -> dict:
        """Get default parameters for a specific algorithm."""
        try:
            algo_class = await run_in_threadpool(ALGORITHM_REGISTRY.get, algorithm_name)
            if not algo_class:
                raise HTTPException(status_code=404, detail="Algorithm not found")
            params = await run_in_threadpool(algo_class.get_default_params)
            return params
        except Exception as e:
            logger.error(f"Error getting params for {algorithm_name}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get algorithm parameters")

    return router
