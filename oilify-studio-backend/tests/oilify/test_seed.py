"""Tests for the Oilify bootstrap seed."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.db.seed import seed_initial_tickers
from oilify_studio_backend.services.price import PricePoint


def _build_price_points() -> list[PricePoint]:
    fetched_at = datetime.now(UTC)
    points: list[PricePoint] = []
    for symbol, ticker, base_price in [("WTI", "CL=F", 100.0), ("BRENT", "BZ=F", 105.0)]:
        for day_offset in range(30):
            points.append(
                PricePoint(
                    symbol=symbol,
                    ticker=ticker,
                    price_usd=base_price + day_offset,
                    price_date=date.today() - timedelta(days=29 - day_offset),
                    fetched_at=fetched_at,
                )
            )
    return points


def test_seed_initial_tickers_seeds_tickers_and_historical_prices(db_session, monkeypatch) -> None:
    points = _build_price_points()
    monkeypatch.setattr("oilify_studio_backend.db.seed.fetch_historical_prices", lambda days=30: points)

    seed_initial_tickers()

    assert db_session.query(Tickers).count() == 2
    assert db_session.query(Price).count() == 60

    seed_initial_tickers()

    assert db_session.query(Tickers).count() == 2
    assert db_session.query(Price).count() == 60