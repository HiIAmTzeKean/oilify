from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oilify_backend.config import Settings, get_settings, setup_logging
from oilify_backend.db import create_tables
from oilify_backend.router import create_oil_price_router
from oilify_backend.services.scheduler import start_scheduler, stop_scheduler


def create_app() -> FastAPI:
    """Create the Oilify API application."""

    settings = get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        create_tables()
        start_scheduler()
        yield
        stop_scheduler()

    app = FastAPI(
        title="Oilify API",
        description="Oilify backend API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.API_DEBUG else None,
        redoc_url="/redoc" if settings.API_DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["Root"])
    async def root() -> dict[str, str]:
        return {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT,
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(create_oil_price_router(), prefix="/api/v1")

    return app
