from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from oilify_backend.config import get_settings

from .schema import Base


class DatabaseManager:
    """Database connection and session manager."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.engine: Engine
        self.SessionLocal: sessionmaker
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        database_config = self.settings.get_database_config()
        self.engine = create_engine(database_config["url"], pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_engine(self) -> Engine:
        return self.engine

    def create_tables(self) -> None:
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def get_db_session(self) -> Generator[Session]:
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session]:
    db_manager = get_database_manager()
    yield from db_manager.get_db_session()


def create_tables() -> None:
    get_database_manager().create_tables()
