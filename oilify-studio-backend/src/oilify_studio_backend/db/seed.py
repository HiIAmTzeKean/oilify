import logging

from sqlalchemy import select

from oilify_studio_backend.db.connection import get_database_manager
from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.oil_price import MARKET_TICKERS, fetch_historical_prices, upsert_daily_prices


logger = logging.getLogger(__name__)


def seed_initial_tickers() -> None:
    """Seed the database with default tickers if the tickers table is empty.

    This function is idempotent: if there are already tickers present it does nothing.
    """
    db_manager = get_database_manager()
    session = db_manager.get_session()
    try:
        _seed_tickers(session)
        _seed_historical_prices(session)
    finally:
        session.close()


def _seed_tickers(session) -> None:
    existing_symbols = set(session.scalars(select(Tickers.symbol)).all())
    missing_tickers = [
        Tickers(symbol=symbol, ticker=ticker)
        for symbol, ticker in MARKET_TICKERS.items()
        if symbol not in existing_symbols
    ]

    if not missing_tickers:
        logger.debug("Ticker seed already present")
        return

    logger.info("Seeding %s tickers", len(missing_tickers))
    session.add_all(missing_tickers)
    session.commit()


def _seed_historical_prices(session) -> None:
    existing_price = session.execute(select(Price.id).limit(1)).first()
    if existing_price:
        logger.debug("Historical oil price seed already present")
        return

    logger.info("Seeding initial historical oil prices")
    points = fetch_historical_prices(days=30)
    upsert_daily_prices(session, points)