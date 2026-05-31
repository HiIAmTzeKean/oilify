"""Tests for the Oilify oil price router."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import Price, Tickers
from oilify_studio_backend.services.oil_price import PricePoint


def _make_price(
    *,
    ticker_id: int,
    price_date: date,
    price_usd: float,
) -> Price:
    return Price(
        ticker_id=ticker_id,
        price_date=price_date,
        price_usd=price_usd,
        currency="USD",
        source="yahoo_finance",
        fetched_at=datetime.now(UTC),
    )


def test_refresh_prices_returns_upserted_rows(client, mocker) -> None:
    rows = [
        _make_price(ticker_id=1, price_date=date.today(), price_usd=101.0),
        _make_price(ticker_id=2, price_date=date.today(), price_usd=103.5),
    ]
    mocker.patch(
        "oilify_studio_backend.router.oil_price_router.ingest_daily_prices",
        return_value=rows,
    )

    response = client.post("/api/v1/prices/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated_rows"] == 2
    assert [item["symbol"] for item in payload["prices"]] == ["WTI", "BRENT"]


def test_latest_prices_returns_latest_rows(client, db_session) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    wti_ticker = db_session.query(Tickers).filter(Tickers.symbol == "WTI").one()
    brent_ticker = db_session.query(Tickers).filter(Tickers.symbol == "BRENT").one()

    db_session.add_all(
        [
            _make_price(ticker_id=wti_ticker.id, price_date=yesterday, price_usd=99.0),
            _make_price(ticker_id=wti_ticker.id, price_date=today, price_usd=100.0),
            _make_price(ticker_id=brent_ticker.id, price_date=yesterday, price_usd=101.0),
            _make_price(ticker_id=brent_ticker.id, price_date=today, price_usd=102.0),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/prices/latest")

    assert response.status_code == 200
    payload = response.json()
    assert [item["symbol"] for item in payload] == ["WTI", "BRENT"]
    assert [item["price_date"] for item in payload] == [today.isoformat(), today.isoformat()]


def test_daily_prices_filters_by_date(client, db_session) -> None:
    today = date.today()
    other_day = today - timedelta(days=1)

    wti_ticker = db_session.query(Tickers).filter(Tickers.symbol == "WTI").one()

    db_session.add_all(
        [
            _make_price(ticker_id=wti_ticker.id, price_date=other_day, price_usd=98.0),
            _make_price(ticker_id=wti_ticker.id, price_date=today, price_usd=100.0),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/prices/daily?date={today.isoformat()}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["price_date"] == today.isoformat()
    assert payload[0]["price_usd"] == 100.0


def test_history_prices_returns_grouped_series(client, mocker) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)
    points = [
        PricePoint("WTI", "CL=F", 99.5, yesterday, datetime.now(UTC)),
        PricePoint("WTI", "CL=F", 100.5, today, datetime.now(UTC)),
        PricePoint("BRENT", "BZ=F", 101.5, yesterday, datetime.now(UTC)),
        PricePoint("BRENT", "BZ=F", 102.5, today, datetime.now(UTC)),
    ]
    mocker.patch(
        "oilify_studio_backend.router.oil_price_router.fetch_historical_prices",
        return_value=points,
    )

    response = client.get("/api/v1/prices/history?days=30")

    assert response.status_code == 200
    payload = response.json()
    assert [item["symbol"] for item in payload] == ["WTI", "BRENT"]
    assert [len(item["points"]) for item in payload] == [2, 2]
    assert payload[0]["points"][0]["price_date"] == yesterday.isoformat()
    assert payload[0]["points"][1]["price_date"] == today.isoformat()