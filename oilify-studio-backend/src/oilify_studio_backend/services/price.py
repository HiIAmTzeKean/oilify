import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

import yfinance as yf
from sqlalchemy.orm import Session

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.analytics import rebuild_market_analytics


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PricePoint:
    symbol: str
    ticker: str
    price_usd: float
    price_date: date
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


def _get_ticker_rows(db: Session) -> list[Tickers]:
    ticker_rows = db.query(Tickers).order_by(Tickers.id).all()
    logger.debug("Loaded %s tickers from database", len(ticker_rows))
    return ticker_rows


def fetch_current_prices(db: Session) -> list[PricePoint]:
    ticker_rows = _get_ticker_rows(db)
    logger.info("Fetching current prices for %s symbols", len(ticker_rows))
    now = datetime.now(UTC)
    today = now.date()
    points: list[PricePoint] = []
    for ticker_row in ticker_rows:
        symbol = ticker_row.symbol
        ticker = ticker_row.ticker
        price = _extract_last_price(ticker)
        points.append(
            PricePoint(
                symbol=symbol,
                ticker=ticker,
                price_usd=price,
                price_date=today,
                fetched_at=now,
            )
        )
        logger.debug("Fetched price symbol=%s ticker=%s price_usd=%s", symbol, ticker, price)
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

        for price_date, row in recent_rows:
            close_price = row["Close"]
            if close_price is None or close_price != close_price:
                continue

            points.append(
                PricePoint(
                    symbol=symbol,
                    ticker=ticker,
                    price_usd=float(close_price),
                    price_date=price_date.date(),
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


def upsert_daily_prices(db: Session, prices: list[PricePoint]) -> list[Price]:
    logger.info("Upserting %s daily price rows", len(prices))
    saved_rows: list[Price] = []
    for point in prices:
        logger.debug(
            "Upserting price symbol=%s ticker=%s price_date=%s price_usd=%s",
            point.symbol,
            point.ticker,
            point.price_date,
            point.price_usd,
        )
        ticker_row = _get_or_create_ticker(db, point.symbol, point.ticker)
        existing = (
            db.query(Price)
            .filter(Price.ticker_id == ticker_row.id, Price.price_date == point.price_date)
            .first()
        )
        if existing:
            existing.price_usd = point.price_usd
            existing.fetched_at = point.fetched_at
            existing.source = "yahoo_finance"
            saved_rows.append(existing)
        else:
            row = Price(
                ticker_id=ticker_row.id,
                price_date=point.price_date,
                price_usd=point.price_usd,
                currency="USD",
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


def ingest_daily_prices(db: Session) -> list[Price]:
    logger.info("Starting price ingestion")
    prices = fetch_current_prices(db)
    rows = upsert_daily_prices(db, prices)
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
            .order_by(Price.price_date.desc(), Price.id.desc())
            .limit(2)
            .all()
        )
        if rows:
            current_row = rows[0]
            previous_row = rows[1] if len(rows) > 1 else None
            results.append(LatestPricePoint(current=current_row, previous=previous_row))
    logger.info("Fetched latest prices for %s symbols", len(results))
    return results
