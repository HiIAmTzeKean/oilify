"""Tests for the Oilify price service layer."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.analytics import rebuild_market_analytics
from oilify_studio_backend.services.price import (
    LatestPricePoint,
    PricePoint,
    fetch_current_prices,
    fetch_historical_prices,
    get_latest_prices,
    upsert_daily_prices,
)


def _seed_tickers(db_session) -> None:
    db_session.add_all(
        [
            Tickers(symbol="WTI", ticker="CL=F"),
            Tickers(symbol="BRENT", ticker="BZ=F"),
        ]
    )
    db_session.commit()


def test_fetch_current_prices_uses_supported_tickers(db_session, monkeypatch) -> None:
    _seed_tickers(db_session)
    prices = {"CL=F": 101.25, "BZ=F": 104.5}

    monkeypatch.setattr(
        "oilify_studio_backend.services.price._extract_last_price",
        lambda ticker_symbol: prices[ticker_symbol],
    )

    points = fetch_current_prices(db_session)

    assert [point.symbol for point in points] == ["WTI", "BRENT"]
    assert [point.ticker for point in points] == ["CL=F", "BZ=F"]
    assert [point.price for point in points] == [101.25, 104.5]
    assert [point.currency for point in points] == ["USD", "USD"]
    assert all(point.price_date == date.today() for point in points)
    assert all(point.fetched_at.tzinfo is not None for point in points)


def test_fetch_historical_prices_returns_last_30_rows_per_ticker(db_session, monkeypatch) -> None:
    _seed_tickers(db_session)

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

        @property
        def fast_info(self) -> dict[str, str]:
            return {"currency": "USD"}

        def history(self, period: str, interval: str, auto_adjust: bool) -> _FakeHistory:
            assert period == "6mo"
            assert interval == "1d"
            assert auto_adjust is False
            rows = [
                (datetime(2025, 1, 1) + timedelta(days=day_offset), 100.0 + day_offset)
                for day_offset in range(35)
            ]
            return _FakeHistory(rows)

    monkeypatch.setattr("oilify_studio_backend.services.price.yf.Ticker", _FakeTicker)

    points = fetch_historical_prices(db_session)

    assert len(points) == 60
    assert [point.symbol for point in points[:30]] == ["WTI"] * 30
    assert [point.symbol for point in points[30:]] == ["BRENT"] * 30
    assert points[0].price_date == date(2025, 1, 6)
    assert points[-1].price_date == date(2025, 2, 4)


def test_upsert_daily_prices_inserts_and_updates(db_session) -> None:
    today = date.today()
    first_batch = [
        PricePoint("WTI", "CL=F", 100.0, "USD", today, datetime.now(UTC)),
        PricePoint("BRENT", "BZ=F", 102.0, "USD", today, datetime.now(UTC)),
    ]

    inserted_rows = upsert_daily_prices(db_session, first_batch)

    assert len(inserted_rows) == 2

    second_batch = [PricePoint("WTI", "CL=F", 110.0, "USD", today, datetime.now(UTC))]
    updated_rows = upsert_daily_prices(db_session, second_batch)

    assert updated_rows[0].price == 110.0
    stored_row = (
        db_session.query(Price)
        .join(Price.ticker)
        .filter(Tickers.symbol == "WTI", Price.date == today)
        .one()
    )
    assert stored_row.price == 110.0
    assert stored_row.source == "yahoo_finance"


def test_get_latest_prices_returns_latest_rows(db_session) -> None:
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
                date=yesterday,
                price=99.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            Price(
                ticker_id=wti_ticker.id,
                date=today,
                price=100.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            Price(
                ticker_id=brent_ticker.id,
                date=yesterday,
                price=101.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            Price(
                ticker_id=brent_ticker.id,
                date=today,
                price=102.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
        ]
    )
    db_session.commit()

    latest_rows = get_latest_prices(db_session)

    assert isinstance(latest_rows[0], LatestPricePoint)
    assert [row.current.ticker.symbol for row in latest_rows] == ["WTI", "BRENT"]
    assert [row.current.date for row in latest_rows] == [today, today]
    previous_dates = []
    for row in latest_rows:
        assert row.previous is not None
        previous_dates.append(row.previous.date)
    assert previous_dates == [yesterday, yesterday]


def test_rebuild_market_analytics_persists_indicator_rows(db_session) -> None:
    _seed_tickers(db_session)
    ticker_ids = {
        row.ticker: row.id
        for row in db_session.query(Tickers).order_by(Tickers.id).all()
    }
    today = date.today()
    rows = []
    for day_offset in range(30):
        price_date = today - timedelta(days=29 - day_offset)
        rows.append(
            Price(
                ticker_id=ticker_ids["CL=F"],
                date=price_date,
                price=100.0 + day_offset,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            )
        )
        rows.append(
            Price(
                ticker_id=ticker_ids["BZ=F"],
                date=price_date,
                price=110.0 + day_offset,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            )
        )

    db_session.add_all(rows)
    db_session.commit()

    analytics = rebuild_market_analytics(db_session)

    assert len(analytics.indicator_rows) > 0
    assert len(analytics.volatility_rows) > 0