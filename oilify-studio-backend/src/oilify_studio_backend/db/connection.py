import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from oilify_studio_backend.config import get_settings
from .schema import Base


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.engine: Engine
        self.SessionLocal: sessionmaker
        logger.debug("Initializing Oilify DatabaseManager")
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        database_config = self.settings.get_database_config()
        logger.info("Creating Oilify database engine")
        logger.debug("Oilify database configuration resolved")
        self.engine = create_engine(database_config["url"], pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_engine(self) -> Engine:
        return self.engine

    def create_tables(self) -> None:
        logger.info("Creating Oilify database tables")
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        logger.debug("Opening Oilify database session")
        return self.SessionLocal()

    def get_db_session(self) -> Generator[Session]:
        logger.debug("Yielding Oilify database session dependency")
        db = self.SessionLocal()
        try:
            yield db
        finally:
            logger.debug("Closing Oilify database session")
            db.close()


_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        logger.debug("Creating singleton Oilify database manager")
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session]:
    db_manager = get_database_manager()
    yield from db_manager.get_db_session()


def create_tables() -> None:
    logger.debug("Request received to create Oilify tables")
    get_database_manager().create_tables()
