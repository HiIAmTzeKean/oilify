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
    return database_url if database_url else "postgresql+psycopg://postgres:password@localhost:5432/recnexteval_db"


def _default_datalake_path() -> str:
    """Get default datalake path."""
    repo_root = _get_project_root()
    return os.path.join(repo_root, "datalake")


class Settings:
    """Server configuration settings."""

    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        self.USING_ENV_FILE = os.getenv("USING_ENV_FILE", "false").lower()
        # Application Configuration
        self.APP_NAME = os.getenv("APP_NAME", "recnexteval Server")
        self.APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
        self.APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")

        # API Configuration
        self.API_HOST = os.getenv("API_HOST", "127.0.0.1")
        self.API_PORT = int(os.getenv("API_PORT", "9000"))
        self.API_DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"

        self.RELOAD_APP_ON_CHANGE = os.getenv("RELOAD_APP_ON_CHANGE", "true").lower() == "true"

        # Middleware Configuration
        cors_origins = "https://localhost:80,https://127.0.0.1:80,http://localhost:80,https://localhost,http://127.0.0.1,http://localhost"
        self.CORS_ORIGINS = cors_origins.split(",") if cors_origins != "*" else ["*"]
        self.SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-session-secret-change-me")

        # Google OAuth
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "dev_client_id")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "dev_client_secret")

        # Frontend URL
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:80")

        # Database Configuration
        self.DATABASE_URL = _default_db_path()

        # File Paths
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.LOGS_DIR.mkdir(exist_ok=True)

        # I18n Configuration
        self.LOCALE_DIR = self.BASE_DIR / "configs/locales"

        # Auth / JWT
        self.SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-auth-secret-change-me")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))

    def get_database_config(self) -> dict:
        """Get database configuration."""
        return {
            "url": self.DATABASE_URL,
            "execution_options": {"postgresql_fast_executemanypostgresql_fast_executemany": True},
        }

    def get_datalake_config(self) -> dict:
        """Get datalake configuration."""
        base_path = _default_datalake_path()
        return {
            "base_path": base_path,
            "raw_data_path": os.path.join(base_path, "raw"),
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
