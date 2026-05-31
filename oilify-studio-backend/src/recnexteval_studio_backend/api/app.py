from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from recnexteval_studio_backend.config import Settings, get_settings, setup_logging
from recnexteval_studio_backend.db.connection import create_tables
from recnexteval_studio_backend.db.seed import seed_inital_stream_jobs, seed_initial_users
from recnexteval_studio_backend.router import (
    create_algorithm_router,
    create_auth_google_router,
    create_auth_router,
    create_dataset_router,
    create_evaluator_router,
    create_metric_router,
    create_stream_router,
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    # Set up logging to capture all logs including recnexteval library
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        """Lifespan handler: run startup tasks before app serves requests."""
        # create tables (no-op if already present)
        create_tables()
        # seed initial users (idempotent)
        seed_initial_users()
        seed_inital_stream_jobs()
        yield

    app = FastAPI(
        title="recnexteval API",
        description="recnexteval Backend",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.API_DEBUG else None,
        redoc_url="/redoc" if settings.API_DEBUG else None,
        lifespan=lifespan,
    )

    _add_middleware(app, settings)

    # Mount static files directory (for favicon, other static assets)
    static_dir = Path(__file__).resolve().parent.parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    _add_routes(app, settings)

    return app


def _add_middleware(app: FastAPI, settings: Settings) -> None:
    """Add middleware to the application."""
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
    )


def _add_routes(app: FastAPI, settings: Settings) -> None:
    """Add routes to the application."""

    API_PREFIX = "/api/v1"

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> RedirectResponse:
        return RedirectResponse(url="/static/recnexteval.ico")

    @app.get(
        "/",
        summary="Get application info",
        description="Return details for recnexteval backend application.",
        tags=["Root"],
    )
    async def root() -> dict[str, str]:
        """Root endpoint - Get application basic information."""
        return {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT,
            "using_env_file": settings.USING_ENV_FILE,
        }

    app.include_router(create_auth_router(), prefix=API_PREFIX)
    app.include_router(create_auth_google_router(), prefix=API_PREFIX)
    app.include_router(create_dataset_router(), prefix=API_PREFIX)
    app.include_router(create_algorithm_router(), prefix=API_PREFIX)
    app.include_router(create_stream_router(), prefix=API_PREFIX)
    app.include_router(create_evaluator_router(), prefix=API_PREFIX)
    app.include_router(create_metric_router(), prefix=API_PREFIX)