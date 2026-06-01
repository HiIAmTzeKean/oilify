import os
from functools import lru_cache
from pathlib import Path


def _get_project_root() -> str:
    """Get project root directory path.

    Layout assumption: this file is at repo_root/recnexteval-studio-backend/src/recnexteval_studio_backend/config/settings.py
    We walk up 4 levels to reach repo_root.
    """
    repo_root = Path(__file__).parent.parent.parent.parent.resolve().as_posix()
    return repo_root


def _default_db_path() -> str:
    """Get default database path."""
    # repo_root = _get_project_root()
    # return f"postgres:///{os.path.join(repo_root, 'recnexteval.db')}"
    database_url = os.getenv("DATABASE_URL")
    return database_url if database_url else "postgresql+psycopg://postgres:password@localhost:5432/oilify_db"


def _default_datalake_path() -> str:
    """Get default datalake path."""
    repo_root = _get_project_root()
    return os.path.join(repo_root, "datalake")

class Settings:
    """Runtime configuration for the Oilify backend."""

    def __init__(self) -> None:
        self.USING_ENV_FILE = os.getenv("USING_ENV_FILE", "true").lower()
        # Application Configuration
        self.APP_NAME = os.getenv("APP_NAME", "Oilify API")
        self.APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
        self.APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")

        # API Configuration
        self.API_HOST = os.getenv("API_HOST", "127.0.0.1")
        self.API_PORT = int(os.getenv("API_PORT", "9000"))
        self.API_DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"

        self.RELOAD_APP_ON_CHANGE = os.getenv("RELOAD_APP_ON_CHANGE", "true").lower() == "true"
        
        # Middleware Configuration
        cors_origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost,http://localhost:80,http://127.0.0.1,http://127.0.0.1:80",
        )
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        
        # Frontend URL
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:80")

        # File Paths
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

        # Database Configuration
        self.DATABASE_URL = _default_db_path()
        self.SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    
    def get_database_config(self) -> dict:
        """Get database configuration."""
        return {
            "url": self.DATABASE_URL,
            "execution_options": {"postgresql_fast_executemanypostgresql_fast_executemany": True},
        }



@lru_cache
def get_settings() -> Settings:
    return Settings()
