from functools import lru_cache
import os


class Settings:
    """Runtime configuration for the Oilify backend."""

    def __init__(self) -> None:
        self.APP_NAME = os.getenv("APP_NAME", "Oilify API")
        self.APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
        self.APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "development")
        self.API_HOST = os.getenv("API_HOST", "127.0.0.1")
        self.API_PORT = int(os.getenv("API_PORT", "9000"))
        self.API_DEBUG = os.getenv("API_DEBUG", "true").lower() == "true"
        self.RELOAD_APP_ON_CHANGE = os.getenv("RELOAD_APP_ON_CHANGE", "true").lower() == "true"
        cors_origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost,http://localhost:80,http://127.0.0.1,http://127.0.0.1:80",
        )
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5432/oilify_db"
        )
        self.OIL_PRICE_SCHEDULE_HOURS = os.getenv("OIL_PRICE_SCHEDULE_HOURS", "0,8,16")
        self.SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

    def get_database_config(self) -> dict[str, str]:
        return {
            "url": self.DATABASE_URL,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
