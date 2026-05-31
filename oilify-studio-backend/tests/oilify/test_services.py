"""Tests for the Oilify oil price service layer."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.oil_price import (
    OilPricePoint,
    fetch_current_oil_prices,
    fetch_historical_oil_prices,
    get_latest_daily_prices,
    upsert_daily_oil_prices,
)


def test_fetch_current_oil_prices_uses_supported_tickers(monkeypatch) -> None:
    prices = {"CL=F": 101.25, "BZ=F": 104.5}

    monkeypatch.setattr(
        "oilify_studio_backend.services.oil_price._extract_last_price",
        lambda ticker_symbol: prices[ticker_symbol],
    )

    points = fetch_current_oil_prices()

    assert [point.symbol for point in points] == ["WTI", "BRENT"]
    assert [point.ticker for point in points] == ["CL=F", "BZ=F"]
    assert [point.price_usd for point in points] == [101.25, 104.5]
    assert all(point.price_date == date.today() for point in points)
    assert all(point.fetched_at.tzinfo is not None for point in points)


def test_fetch_historical_oil_prices_returns_last_30_rows_per_ticker(monkeypatch) -> None:
    class _FakeHistory:
        def __init__(self, rows: list[tuple[datetime, float]]) -> None:
            self._rows = rows

        @property
        def empty(self) -> bool:
            return not self._rows

        def tail(self, days: int) -> "_FakeHistory":
            return _FakeHistory(self._rows[-days:])

        def iterrows(self):
            for price_date, close_price in self._rows:
                yield price_date, {"Close": close_price}

    class _FakeTicker:
        def __init__(self, ticker_symbol: str) -> None:
            self.ticker_symbol = ticker_symbol

        def history(self, period: str, interval: str, auto_adjust: bool) -> _FakeHistory:
            assert period == "6mo"
            assert interval == "1d"
            assert auto_adjust is False
            rows = [
                (datetime(2025, 1, 1) + timedelta(days=day_offset), 100.0 + day_offset)
                for day_offset in range(35)
            ]
            return _FakeHistory(rows)

    monkeypatch.setattr("oilify_studio_backend.services.oil_price.yf.Ticker", _FakeTicker)

    points = fetch_historical_oil_prices()

    assert len(points) == 60
    assert [point.symbol for point in points[:30]] == ["WTI"] * 30
    assert [point.symbol for point in points[30:]] == ["BRENT"] * 30
    assert points[0].price_date == date(2025, 1, 6)
    assert points[-1].price_date == date(2025, 2, 4)


def test_upsert_daily_oil_prices_inserts_and_updates(db_session) -> None:
    today = date.today()
    first_batch = [
        OilPricePoint("WTI", "CL=F", 100.0, today, datetime.now(UTC)),
        OilPricePoint("BRENT", "BZ=F", 102.0, today, datetime.now(UTC)),
    ]

    inserted_rows = upsert_daily_oil_prices(db_session, first_batch)

    assert len(inserted_rows) == 2

    second_batch = [OilPricePoint("WTI", "CL=F", 110.0, today, datetime.now(UTC))]
    updated_rows = upsert_daily_oil_prices(db_session, second_batch)

    assert updated_rows[0].price_usd == 110.0
    stored_row = (
        db_session.query(Price)
        .join(Price.ticker)
        .filter(Tickers.symbol == "WTI", Price.price_date == today)
        .one()
    )
    assert stored_row.price_usd == 110.0
    assert stored_row.source == "yahoo_finance"


def test_get_latest_daily_prices_returns_latest_rows(db_session) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    wti_ticker = Tickers(symbol="WTI", ticker="CL=F")
    brent_ticker = Tickers(symbol="BRENT", ticker="BZ=F")
    db_session.add_all([wti_ticker, brent_ticker])
    db_session.flush()

    db_session.add_all(
        [
            Price(
                ticker_id=wti_ticker.id,
                price_date=yesterday,
                price_usd=99.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            Price(
                ticker_id=wti_ticker.id,
                price_date=today,
                price_usd=100.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            Price(
                ticker_id=brent_ticker.id,
                price_date=yesterday,
                price_usd=101.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            Price(
                ticker_id=brent_ticker.id,
                price_date=today,
                price_usd=102.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
        ]
    )
    db_session.commit()

    latest_rows = get_latest_daily_prices(db_session)

    assert [row.symbol for row in latest_rows] == ["WTI", "BRENT"]
    assert [row.price_date for row in latest_rows] == [today, today]