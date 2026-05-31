"""Tests for the Oilify bootstrap seed."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.db.seed import seed_initial_tickers
from oilify_studio_backend.services.price import PricePoint


def _build_price_points() -> list[PricePoint]:
    fetched_at = datetime.now(UTC)
    points: list[PricePoint] = []
    for ticker, base_price in [
        ("CL=F", 100.0),
        ("BZ=F", 105.0),
        ("NG=F", 110.0),
        ("HO=F", 115.0),
        ("RB=F", 120.0),
    ]:
        for day_offset in range(30):
            points.append(
                PricePoint(
                    symbol=ticker,
                    ticker=ticker,
                    price_usd=base_price + day_offset,
                    price_date=date.today() - timedelta(days=29 - day_offset),
                    fetched_at=fetched_at,
                )
            )
    return points


def test_seed_initial_tickers_seeds_tickers_and_historical_prices(db_session, monkeypatch) -> None:
    points = _build_price_points()
    monkeypatch.setattr(
        "oilify_studio_backend.db.seed._resolve_seed_metadata",
        lambda ticker: (ticker, f"{ticker} short", f"{ticker} long"),
    )
    monkeypatch.setattr(
        "oilify_studio_backend.db.seed.fetch_historical_prices",
        lambda session, days=30: points,
    )

    seed_initial_tickers()

    assert db_session.query(Tickers).count() == 5
    assert db_session.query(Price).count() == 150
    assert [row.symbol for row in db_session.query(Tickers).order_by(Tickers.id).all()] == [
        "CL=F",
        "BZ=F",
        "NG=F",
        "HO=F",
        "RB=F",
    ]
    assert [row.short_name for row in db_session.query(Tickers).order_by(Tickers.id).all()] == [
        "CL=F short",
        "BZ=F short",
        "NG=F short",
        "HO=F short",
        "RB=F short",
    ]
    assert [row.long_name for row in db_session.query(Tickers).order_by(Tickers.id).all()] == [
        "CL=F long",
        "BZ=F long",
        "NG=F long",
        "HO=F long",
        "RB=F long",
    ]

    seed_initial_tickers()

    assert db_session.query(Tickers).count() == 5
    assert db_session.query(Price).count() == 150