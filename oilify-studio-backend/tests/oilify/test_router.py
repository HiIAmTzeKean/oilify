"""Tests for the Oilify oil price router."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import OilPriceDaily


def _make_price(
    *,
    symbol: str,
    ticker: str,
    price_date: date,
    price_usd: float,
) -> OilPriceDaily:
    return OilPriceDaily(
        symbol=symbol,
        ticker=ticker,
        price_date=price_date,
        price_usd=price_usd,
        currency="USD",
        source="yahoo_finance",
        fetched_at=datetime.now(UTC),
    )


def test_refresh_prices_returns_upserted_rows(client, mocker) -> None:
    rows = [
        _make_price(symbol="WTI", ticker="CL=F", price_date=date.today(), price_usd=101.0),
        _make_price(symbol="BRENT", ticker="BZ=F", price_date=date.today(), price_usd=103.5),
    ]
    mocker.patch(
        "oilify_studio_backend.router.oil_price_router.ingest_daily_oil_prices",
        return_value=rows,
    )

    response = client.post("/api/v1/oil-prices/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated_rows"] == 2
    assert [item["symbol"] for item in payload["prices"]] == ["WTI", "BRENT"]


def test_latest_prices_returns_latest_rows(client, db_session) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    db_session.add_all(
        [
            _make_price(symbol="WTI", ticker="CL=F", price_date=yesterday, price_usd=99.0),
            _make_price(symbol="WTI", ticker="CL=F", price_date=today, price_usd=100.0),
            _make_price(symbol="BRENT", ticker="BZ=F", price_date=yesterday, price_usd=101.0),
            _make_price(symbol="BRENT", ticker="BZ=F", price_date=today, price_usd=102.0),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/oil-prices/latest")

    assert response.status_code == 200
    payload = response.json()
    assert [item["symbol"] for item in payload] == ["WTI", "BRENT"]
    assert [item["price_date"] for item in payload] == [today.isoformat(), today.isoformat()]


def test_daily_prices_filters_by_date(client, db_session) -> None:
    today = date.today()
    other_day = today - timedelta(days=1)

    db_session.add_all(
        [
            _make_price(symbol="WTI", ticker="CL=F", price_date=other_day, price_usd=98.0),
            _make_price(symbol="WTI", ticker="CL=F", price_date=today, price_usd=100.0),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/oil-prices/daily?date={today.isoformat()}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["price_date"] == today.isoformat()
    assert payload[0]["price_usd"] == 100.0