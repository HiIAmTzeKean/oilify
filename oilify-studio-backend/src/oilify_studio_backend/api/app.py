import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oilify_studio_backend.config import Settings, get_settings, setup_logging
from oilify_studio_backend.db import create_tables
from oilify_studio_backend.db.seed import seed_initial_tickers
from oilify_studio_backend.router import create_price_router
from oilify_studio_backend.services.scheduler import start_scheduler, stop_scheduler


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create the Oilify API application."""

    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info(
        "Creating Oilify app version=%s environment=%s debug=%s",
        settings.APP_VERSION,
        settings.APP_ENVIRONMENT,
        settings.API_DEBUG,
    )
    logger.debug("Oilify API docs enabled=%s redoc enabled=%s", settings.API_DEBUG, settings.API_DEBUG)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Oilify application startup beginning")
        logger.debug("Creating database tables and seeding ticker metadata")
        create_tables()
        seed_initial_tickers()
        logger.debug("Starting price scheduler")
        start_scheduler()
        logger.info("Oilify application startup complete")
        yield
        logger.info("Oilify application shutdown beginning")
        logger.debug("Stopping price scheduler")
        stop_scheduler()
        logger.info("Oilify application shutdown complete")

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

    logger.debug("Adding CORS middleware with %s origins", len(settings.CORS_ORIGINS))
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
    logger.debug("Registering Oilify routes under prefix %s", api_prefix)

    @app.get(
        "/",
        summary="Get application info",
        description="Return details for the Oilify backend application.",
        tags=["Root"],
    )
    async def root() -> dict[str, str]:
        """Root endpoint - Get application basic information."""
        logger.debug("Oilify root endpoint requested")
        return {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT,
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        logger.debug("Oilify health endpoint requested")
        return {"status": "ok"}

    app.include_router(create_price_router(), prefix=api_prefix)
