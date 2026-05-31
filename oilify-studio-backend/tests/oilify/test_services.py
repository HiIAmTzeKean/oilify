"""Tests for the Oilify oil price service layer."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import OilPriceDaily
from oilify_studio_backend.services.oil_price import OilPricePoint, fetch_current_oil_prices, get_latest_daily_prices, upsert_daily_oil_prices


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
        db_session.query(OilPriceDaily)
        .filter(OilPriceDaily.symbol == "WTI", OilPriceDaily.price_date == today)
        .one()
    )
    assert stored_row.price_usd == 110.0
    assert stored_row.source == "yahoo_finance"


def test_get_latest_daily_prices_returns_latest_rows(db_session) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    db_session.add_all(
        [
            OilPriceDaily(
                symbol="WTI",
                ticker="CL=F",
                price_date=yesterday,
                price_usd=99.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            OilPriceDaily(
                symbol="WTI",
                ticker="CL=F",
                price_date=today,
                price_usd=100.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            OilPriceDaily(
                symbol="BRENT",
                ticker="BZ=F",
                price_date=yesterday,
                price_usd=101.0,
                currency="USD",
                source="yahoo_finance",
                fetched_at=datetime.now(UTC),
            ),
            OilPriceDaily(
                symbol="BRENT",
                ticker="BZ=F",
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