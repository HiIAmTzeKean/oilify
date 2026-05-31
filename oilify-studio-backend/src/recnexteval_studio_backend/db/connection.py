from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from recnexteval_studio_backend.config.setting import get_settings

from .schema import Base


class DatabaseManager:
    """Database connection and session manager."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self.settings = get_settings()
        self.engine: Engine
        self.SessionLocal: sessionmaker
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize database engine."""
        database_config = self.settings.get_database_config()

        self.engine: Engine = create_engine(**database_config)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_engine(self) -> Engine:
        """Get database engine."""
        return self.engine

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def get_db_session(self) -> Generator[Session]:
        """Get database session for dependency injection."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# Global database manager instance
_db_manager: DatabaseManager = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session]:
    """Get database session for FastAPI dependency injection."""
    db_manager = get_database_manager()
    yield from db_manager.get_db_session()


def get_engine() -> Engine:
    """Get database engine."""
    return get_database_manager().get_engine()


def create_tables() -> None:
    """Create all database tables."""
    get_database_manager().create_tables()


def drop_tables() -> None:
    """Drop all database tables."""
    get_database_manager().drop_tables()
