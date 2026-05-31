import logging

import yfinance as yf
from sqlalchemy import select

from oilify_studio_backend.db.connection import get_database_manager
from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.analytics import rebuild_market_analytics
from oilify_studio_backend.services.price import fetch_historical_prices, upsert_daily_prices


logger = logging.getLogger(__name__)

DEFAULT_TICKERS: tuple[str, ...] = ("CL=F", "BZ=F", "NG=F", "HO=F", "RB=F")


def _resolve_seed_metadata(ticker: str) -> tuple[str, str | None, str | None]:
    info = yf.Ticker(ticker).info
    symbol = info.get("symbol") or ticker
    short_name = info.get("shortName")
    long_name = info.get("longName")
    return symbol, short_name, long_name


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
    existing_rows = {
        row.ticker: row
        for row in session.scalars(select(Tickers).where(Tickers.ticker.in_(DEFAULT_TICKERS))).all()
    }
    created_count = 0
    updated_count = 0

    for ticker in DEFAULT_TICKERS:
        symbol, short_name, long_name = _resolve_seed_metadata(ticker)
        row = existing_rows.get(ticker)
        if row is None:
            session.add(
                Tickers(
                    symbol=symbol,
                    ticker=ticker,
                    short_name=short_name,
                    long_name=long_name,
                )
            )
            created_count += 1
            continue

        if row.symbol != symbol:
            row.symbol = symbol
            updated_count += 1
        if row.short_name != short_name:
            row.short_name = short_name
            updated_count += 1
        if row.long_name != long_name:
            row.long_name = long_name
            updated_count += 1

    if created_count == 0 and updated_count == 0:
        logger.debug("Ticker seed already present")
        return

    logger.info("Seeded %s tickers updated=%s", created_count, updated_count)
    session.commit()


def _seed_historical_prices(session) -> None:
    existing_price = session.execute(select(Price.id).limit(1)).first()
    if existing_price:
        logger.debug("Historical price seed already present")
    else:
        logger.info("Seeding initial historical prices")
        points = fetch_historical_prices(session, days=30)
        upsert_daily_prices(session, points)

    rebuild_market_analytics(session)