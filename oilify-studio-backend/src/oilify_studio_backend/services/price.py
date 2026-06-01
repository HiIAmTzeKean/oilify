import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

import yfinance as yf
from sqlalchemy.orm import Session

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.analytics import rebuild_market_analytics


logger = logging.getLogger(__name__)


def _round_to_30min(dt: datetime) -> datetime:
    """Round ``dt`` down to the nearest half-hour mark (``xx:00`` or ``xx:30``)."""
    minute = (dt.minute // 30) * 30
    return dt.replace(minute=minute, second=0, microsecond=0)


@dataclass(frozen=True)
class PricePoint:
    symbol: str
    ticker: str
    price: float
    currency: str
    timestamp: datetime
    fetched_at: datetime


@dataclass(frozen=True)
class LatestPricePoint:
    current: Price
    previous: Price | None


def _extract_last_price(ticker_symbol: str) -> float:
    logger.debug("Extracting latest market price for ticker=%s", ticker_symbol)
    ticker = yf.Ticker(ticker_symbol)
    fast_info = getattr(ticker, "fast_info", None)
    if fast_info and getattr(fast_info, "get", None):
        last_price = fast_info.get("lastPrice")
        if last_price is not None:
            logger.debug("Using fast_info lastPrice for ticker=%s", ticker_symbol)
            return float(last_price)

    logger.debug("Fast info unavailable for ticker=%s; falling back to history", ticker_symbol)
    history = ticker.history(period="1d", interval="1m", auto_adjust=False)
    if history.empty:
        logger.error("No market price available for ticker=%s", ticker_symbol)
        raise ValueError(f"No market price available for ticker {ticker_symbol}")
    logger.debug("Using historical close price for ticker=%s", ticker_symbol)
    return float(history["Close"].iloc[-1])


def _extract_currency(ticker_symbol: str) -> str:
    logger.debug("Extracting currency for ticker=%s", ticker_symbol)
    ticker = yf.Ticker(ticker_symbol)
    fast_info = getattr(ticker, "fast_info", None)
    if fast_info and getattr(fast_info, "get", None):
        currency = fast_info.get("currency")
        if currency:
            logger.debug("Using fast_info currency for ticker=%s", ticker_symbol)
            return str(currency)

    logger.debug(
        "Fast info currency unavailable for ticker=%s; falling back to history metadata",
        ticker_symbol,
    )
    history = ticker.history(period="1d", interval="1d", auto_adjust=False)
    metadata = getattr(history, "_history_metadata", None)
    if isinstance(metadata, dict):
        currency = metadata.get("currency")
        if currency:
            logger.debug("Using history metadata currency for ticker=%s", ticker_symbol)
            return str(currency)

    info = getattr(ticker, "info", None)
    if isinstance(info, dict):
        currency = info.get("currency")
        if currency:
            logger.debug("Using info currency for ticker=%s", ticker_symbol)
            return str(currency)

    logger.error("No currency available for ticker=%s", ticker_symbol)
    raise ValueError(f"No currency available for ticker {ticker_symbol}")


def _get_ticker_rows(db: Session) -> list[Tickers]:
    ticker_rows = db.query(Tickers).order_by(Tickers.id).all()
    logger.debug("Loaded %s tickers from database", len(ticker_rows))
    return ticker_rows


def fetch_current_prices(db: Session) -> list[PricePoint]:
    ticker_rows = _get_ticker_rows(db)
    logger.info("Fetching current prices for %s symbols", len(ticker_rows))
    now = datetime.now(UTC)
    timestamp = _round_to_30min(now)
    points: list[PricePoint] = []
    for ticker_row in ticker_rows:
        symbol = ticker_row.symbol
        ticker = ticker_row.ticker
        price = _extract_last_price(ticker)
        currency = _extract_currency(ticker)
        points.append(
            PricePoint(
                symbol=symbol,
                ticker=ticker,
                price=price,
                currency=currency,
                timestamp=timestamp,
                fetched_at=now,
            )
        )
        logger.debug(
            "Fetched price symbol=%s ticker=%s price=%s currency=%s price_at=%s",
            symbol,
            ticker,
            price,
            currency,
            timestamp,
        )
    logger.info("Fetched %s current prices", len(points))
    return points


def fetch_historical_prices(db: Session, days: int = 30) -> list[PricePoint]:
    ticker_rows = _get_ticker_rows(db)
    logger.info("Fetching historical prices for %s symbols days=%s", len(ticker_rows), days)
    fetched_at = datetime.now(UTC)
    history_window = "6mo"
    points: list[PricePoint] = []

    for ticker_row in ticker_rows:
        symbol = ticker_row.symbol
        ticker = ticker_row.ticker
        logger.debug("Fetching historical prices symbol=%s ticker=%s", symbol, ticker)
        currency = _extract_currency(ticker)
        history = yf.Ticker(ticker).history(period=history_window, interval="1d", auto_adjust=False)
        if history.empty:
            logger.error("No historical market data available for ticker=%s", ticker)
            raise ValueError(f"No historical market data available for ticker {ticker}")

        recent_history = history.tail(days)
        if recent_history.empty:
            logger.error("No historical rows available for ticker=%s", ticker)
            raise ValueError(f"No historical rows available for ticker {ticker}")
        recent_rows = list(recent_history.iterrows())
        if len(recent_rows) < days:
            logger.warning(
                "Only %s historical rows available for ticker=%s requested_days=%s",
                len(recent_rows),
                ticker,
                days,
            )

        for price_timestamp, row in recent_rows:
            close_price = row["Close"]
            if close_price is None or close_price != close_price:
                continue

            price_timestamp = cast(datetime, price_timestamp)
            points.append(
                PricePoint(
                    symbol=symbol,
                    ticker=ticker,
                    price=float(close_price),
                    currency=currency,
                    timestamp=price_timestamp,
                    fetched_at=fetched_at,
                )
            )

    logger.info("Fetched %s historical price rows", len(points))
    return points


def _get_or_create_ticker(db: Session, symbol: str, ticker: str) -> Tickers:
    existing_ticker = db.query(Tickers).filter(Tickers.symbol == symbol).one_or_none()
    if existing_ticker is None:
        existing_ticker = Tickers(symbol=symbol, ticker=ticker)
        db.add(existing_ticker)
        db.flush()
        return existing_ticker

    if existing_ticker.ticker != ticker:
        existing_ticker.ticker = ticker
        db.flush()

    return existing_ticker


def upsert_prices(db: Session, prices: list[PricePoint]) -> list[Price]:
    logger.info("Upserting %s price rows", len(prices))
    saved_rows: list[Price] = []
    for point in prices:
        logger.debug(
            "Upserting price symbol=%s ticker=%s timestamp=%s price=%s currency=%s",
            point.symbol,
            point.ticker,
            point.timestamp,
            point.price,
            point.currency,
        )
        ticker_row = _get_or_create_ticker(db, point.symbol, point.ticker)
        existing = (
            db.query(Price)
            .filter(Price.ticker_id == ticker_row.id, Price.timestamp == point.timestamp)
            .first()
        )
        if existing:
            existing.price = point.price
            existing.currency = point.currency
            existing.fetched_at = point.fetched_at
            existing.source = "yahoo_finance"
            saved_rows.append(existing)
        else:
            row = Price(
                ticker_id=ticker_row.id,
                timestamp=point.timestamp,
                price=point.price,
                currency=point.currency,
                source="yahoo_finance",
                fetched_at=point.fetched_at,
            )
            db.add(row)
            saved_rows.append(row)

    db.commit()
    logger.info("Committed %s price rows", len(saved_rows))
    for row in saved_rows:
        db.refresh(row)
    logger.debug("Refreshed %s persisted price rows", len(saved_rows))
    return saved_rows


def ingest_prices(db: Session) -> list[Price]:
    logger.info("Starting price ingestion")
    prices = fetch_current_prices(db)
    rows = upsert_prices(db, prices)
    rebuild_market_analytics(db)
    logger.info("Completed price ingestion rows=%s", len(rows))
    return rows


def get_latest_prices(db: Session) -> list[LatestPricePoint]:
    logger.debug("Fetching latest prices")
    results: list[LatestPricePoint] = []
    for ticker_row in _get_ticker_rows(db):
        rows = (
            db.query(Price)
            .filter(Price.ticker_id == ticker_row.id)
            .order_by(Price.timestamp.desc(), Price.id.desc())
            .limit(2)
            .all()
        )
        if rows:
            current_row = rows[0]
            previous_row = rows[1] if len(rows) > 1 else None
            results.append(LatestPricePoint(current=current_row, previous=previous_row))
    logger.info("Fetched latest prices for %s symbols", len(results))
    return results
