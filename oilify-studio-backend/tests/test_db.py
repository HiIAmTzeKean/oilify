"""Tests for the Oilify database layer."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from oilify_studio_backend.db.connection import DatabaseManager, get_database_manager


def test_get_database_manager_returns_singleton() -> None:
    import oilify_studio_backend.db.connection as connection_module

    original_manager = connection_module._db_manager
    connection_module._db_manager = None

    try:
        manager_one = get_database_manager()
        manager_two = get_database_manager()

        assert manager_one is manager_two
    finally:
        connection_module._db_manager = original_manager


def test_get_db_session_closes_the_session() -> None:
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    manager = object.__new__(DatabaseManager)
    manager.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    generator = manager.get_db_session()
    session = next(generator)

    close_called = False
    original_close = session.close

    def _close() -> None:
        nonlocal close_called
        close_called = True
        original_close()

    session.close = _close

    try:
        next(generator)
    except StopIteration:
        pass

    assert close_called is True


def test_create_tables_renames_legacy_prices_columns() -> None:
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    legacy_manager = object.__new__(DatabaseManager)
    legacy_manager.engine = engine
    legacy_manager.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker_id INTEGER NOT NULL,
                    date DATETIME NOT NULL,
                    price_usd FLOAT NOT NULL,
                    currency VARCHAR(8) NOT NULL,
                    source VARCHAR(64) NOT NULL,
                    fetched_at DATETIME NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )

    legacy_manager.create_tables()

    from sqlalchemy import inspect

    columns = {column["name"] for column in inspect(engine).get_columns("prices")}

    assert "price_at" in columns
    assert "price" in columns
    assert "date" not in columns
    assert "price_usd" not in columns