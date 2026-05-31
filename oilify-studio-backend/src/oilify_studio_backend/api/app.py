from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oilify_studio_backend.config import Settings, get_settings, setup_logging
from oilify_studio_backend.db import create_tables
from oilify_studio_backend.db.seed import seed_initial_tickers
from oilify_studio_backend.router import create_oil_price_router
from oilify_studio_backend.services.scheduler import start_scheduler, stop_scheduler


def create_app() -> FastAPI:
    """Create the Oilify API application."""

    settings = get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        create_tables()
        seed_initial_tickers()
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

    _add_middleware(app, settings)
    _add_routes(app, settings)

    return app


def _add_middleware(app: FastAPI, settings: Settings) -> None:
    """Add middleware to the application."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _add_routes(app: FastAPI, settings: Settings) -> None:
    """Add routes to the application."""

    api_prefix = "/api/v1"

    @app.get(
        "/",
        summary="Get application info",
        description="Return details for the Oilify backend application.",
        tags=["Root"],
    )
    async def root() -> dict[str, str]:
        """Root endpoint - Get application basic information."""
        return {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT,
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(create_oil_price_router(), prefix=api_prefix)
