import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

import yfinance as yf
from sqlalchemy.orm import Session

from oilify_studio_backend.db.schema import OilPriceDaily


logger = logging.getLogger(__name__)


TICKERS: dict[str, str] = {
    "WTI": "CL=F",
    "BRENT": "BZ=F",
}


@dataclass(frozen=True)
class OilPricePoint:
    symbol: str
    ticker: str
    price_usd: float
    price_date: date
    fetched_at: datetime


def _extract_last_price(ticker_symbol: str) -> float:
    logger.debug("Extracting latest oil price for ticker=%s", ticker_symbol)
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


def fetch_current_oil_prices() -> list[OilPricePoint]:
    logger.info("Fetching current oil prices for %s symbols", len(TICKERS))
    now = datetime.now(UTC)
    today = now.date()
    points: list[OilPricePoint] = []
    for symbol, ticker in TICKERS.items():
        price = _extract_last_price(ticker)
        points.append(
            OilPricePoint(
                symbol=symbol,
                ticker=ticker,
                price_usd=price,
                price_date=today,
                fetched_at=now,
            )
        )
        logger.debug("Fetched oil price symbol=%s ticker=%s price_usd=%s", symbol, ticker, price)
    logger.info("Fetched %s current oil prices", len(points))
    return points


def upsert_daily_oil_prices(db: Session, prices: list[OilPricePoint]) -> list[OilPriceDaily]:
    logger.info("Upserting %s daily oil price rows", len(prices))
    saved_rows: list[OilPriceDaily] = []
    for point in prices:
        logger.debug(
            "Upserting oil price symbol=%s ticker=%s price_date=%s price_usd=%s",
            point.symbol,
            point.ticker,
            point.price_date,
            point.price_usd,
        )
        existing = (
            db.query(OilPriceDaily)
            .filter(
                OilPriceDaily.symbol == point.symbol,
                OilPriceDaily.price_date == point.price_date,
            )
            .first()
        )
        if existing:
            existing.price_usd = point.price_usd
            existing.ticker = point.ticker
            existing.fetched_at = point.fetched_at
            existing.source = "yahoo_finance"
            saved_rows.append(existing)
        else:
            row = OilPriceDaily(
                symbol=point.symbol,
                ticker=point.ticker,
                price_date=point.price_date,
                price_usd=point.price_usd,
                currency="USD",
                source="yahoo_finance",
                fetched_at=point.fetched_at,
            )
            db.add(row)
            saved_rows.append(row)

    db.commit()
    logger.info("Committed %s oil price rows", len(saved_rows))
    for row in saved_rows:
        db.refresh(row)
    logger.debug("Refreshed %s persisted oil price rows", len(saved_rows))
    return saved_rows


def ingest_daily_oil_prices(db: Session) -> list[OilPriceDaily]:
    logger.info("Starting oil price ingestion")
    prices = fetch_current_oil_prices()
    rows = upsert_daily_oil_prices(db, prices)
    logger.info("Completed oil price ingestion rows=%s", len(rows))
    return rows


def get_latest_daily_prices(db: Session) -> list[OilPriceDaily]:
    logger.debug("Fetching latest daily oil prices")
    results: list[OilPriceDaily] = []
    for symbol in TICKERS:
        row = (
            db.query(OilPriceDaily)
            .filter(OilPriceDaily.symbol == symbol)
            .order_by(OilPriceDaily.price_date.desc())
            .first()
        )
        if row:
            results.append(row)
    logger.info("Fetched latest oil prices for %s symbols", len(results))
    return results
