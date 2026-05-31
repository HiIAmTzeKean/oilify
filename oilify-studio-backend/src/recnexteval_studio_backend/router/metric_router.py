import logging as logger

from fastapi import APIRouter
from recnexteval.registries import METRIC_REGISTRY

logger = logger.getLogger(__name__)


def create_metric_router() -> APIRouter:
    router = APIRouter(prefix="/metric", tags=["metric"])

    @router.get("/get_metric")
    def get_metric() -> list[str]:
        return METRIC_REGISTRY.get_registered_keys()

    return router
