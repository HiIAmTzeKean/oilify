from dataclasses import dataclass
from datetime import UTC, date, datetime

import yfinance as yf
from sqlalchemy.orm import Session

from oilify_studio_backend.db.schema import OilPriceDaily


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
    ticker = yf.Ticker(ticker_symbol)
    fast_info = getattr(ticker, "fast_info", None)
    if fast_info and getattr(fast_info, "get", None):
        last_price = fast_info.get("lastPrice")
        if last_price is not None:
            return float(last_price)

    history = ticker.history(period="1d", interval="1m", auto_adjust=False)
    if history.empty:
        raise ValueError(f"No market price available for ticker {ticker_symbol}")
    return float(history["Close"].iloc[-1])


def fetch_current_oil_prices() -> list[OilPricePoint]:
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
    return points


def upsert_daily_oil_prices(db: Session, prices: list[OilPricePoint]) -> list[OilPriceDaily]:
    saved_rows: list[OilPriceDaily] = []
    for point in prices:
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
    for row in saved_rows:
        db.refresh(row)
    return saved_rows


def ingest_daily_oil_prices(db: Session) -> list[OilPriceDaily]:
    prices = fetch_current_oil_prices()
    return upsert_daily_oil_prices(db, prices)


def get_latest_daily_prices(db: Session) -> list[OilPriceDaily]:
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
    return results
