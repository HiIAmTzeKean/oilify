"""Tests for the Oilify price router."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import HistoricalVolatility, Price, TechnicalIndicator, Tickers
from oilify_studio_backend.services.price import PricePoint


def _make_price(
    *,
    ticker_id: int,
    price_date: date,
    price: float,
) -> Price:
    return Price(
        ticker_id=ticker_id,
        price_date=price_date,
        price=price,
        currency="USD",
        source="yahoo_finance",
        fetched_at=datetime.now(UTC),
    )


def test_refresh_prices_returns_upserted_rows(client, mocker) -> None:
    rows = [
        _make_price(ticker_id=1, price_date=date.today(), price=101.0),
        _make_price(ticker_id=2, price_date=date.today(), price=103.5),
    ]
    mocker.patch(
        "oilify_studio_backend.router.price_router.ingest_daily_prices",
        return_value=rows,
    )

    response = client.post("/api/v1/prices/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated_rows"] == 2
    assert [item["symbol"] for item in payload["prices"]] == ["CL=F", "BZ=F"]
    assert [item["short_name"] for item in payload["prices"]] == ["CL=F short", "BZ=F short"]


def test_latest_prices_returns_latest_rows(client, db_session) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)

    wti_ticker = db_session.query(Tickers).filter(Tickers.ticker == "CL=F").one()
    brent_ticker = db_session.query(Tickers).filter(Tickers.ticker == "BZ=F").one()

    db_session.add_all(
        [
            _make_price(ticker_id=wti_ticker.id, price_date=yesterday, price=99.0),
            _make_price(ticker_id=wti_ticker.id, price_date=today, price=100.0),
            _make_price(ticker_id=brent_ticker.id, price_date=yesterday, price=101.0),
            _make_price(ticker_id=brent_ticker.id, price_date=today, price=102.0),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/prices/latest")

    assert response.status_code == 200
    payload = response.json()
    payload_by_symbol = {item["symbol"]: item for item in payload}
    assert payload_by_symbol["CL=F"]["short_name"] == "CL=F short"
    assert payload_by_symbol["BZ=F"]["short_name"] == "BZ=F short"
    assert payload_by_symbol["CL=F"]["price_date"] == today.isoformat()
    assert payload_by_symbol["BZ=F"]["price_date"] == today.isoformat()
    assert payload_by_symbol["CL=F"]["previous_price"] == 99.0
    assert payload_by_symbol["CL=F"]["price_change"] == 1.0
    assert round(payload_by_symbol["CL=F"]["price_change_pct"], 2) == 1.01


def test_daily_prices_filters_by_date(client, db_session) -> None:
    today = date.today()
    other_day = today - timedelta(days=1)

    wti_ticker = db_session.query(Tickers).filter(Tickers.ticker == "CL=F").one()

    db_session.add_all(
        [
            _make_price(ticker_id=wti_ticker.id, price_date=other_day, price=98.0),
            _make_price(ticker_id=wti_ticker.id, price_date=today, price=100.0),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/prices/daily?date={today.isoformat()}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["price_date"] == today.isoformat()
    assert payload[0]["price"] == 100.0


def test_history_prices_returns_grouped_series(client, db_session, mocker) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)
    wti_ticker = db_session.query(Tickers).filter(Tickers.ticker == "CL=F").one()
    db_session.add_all(
        [
            TechnicalIndicator(
                ticker_id=wti_ticker.id,
                indicator_date=yesterday,
                indicator_name="sma_20",
                indicator_value=99.0,
                window_size=20,
            ),
            TechnicalIndicator(
                ticker_id=wti_ticker.id,
                indicator_date=today,
                indicator_name="sma_20",
                indicator_value=100.0,
                window_size=20,
            ),
            HistoricalVolatility(
                ticker_id=wti_ticker.id,
                volatility_date=today,
                annualized_volatility=0.32,
                window_size=20,
                annualization_factor=252,
            ),
        ]
    )
    db_session.commit()

    points = [
        PricePoint("CL=F", "CL=F", 99.5, "USD", yesterday, datetime.now(UTC)),
        PricePoint("CL=F", "CL=F", 100.5, "USD", today, datetime.now(UTC)),
        PricePoint("BZ=F", "BZ=F", 101.5, "USD", yesterday, datetime.now(UTC)),
        PricePoint("BZ=F", "BZ=F", 102.5, "USD", today, datetime.now(UTC)),
    ]
    mocker.patch(
        "oilify_studio_backend.router.price_router.fetch_historical_prices",
        return_value=points,
    )

    response = client.get("/api/v1/prices/history?days=30")

    assert response.status_code == 200
    payload = response.json()
    payload_by_symbol = {item["symbol"]: item for item in payload}
    assert payload_by_symbol["CL=F"]["short_name"] == "CL=F short"
    assert payload_by_symbol["BZ=F"]["short_name"] == "BZ=F short"
    assert [len(payload_by_symbol[symbol]["points"]) for symbol in ["CL=F", "BZ=F"]] == [2, 2]
    assert payload_by_symbol["CL=F"]["points"][0]["price_date"] == yesterday.isoformat()
    assert payload_by_symbol["CL=F"]["points"][1]["price_date"] == today.isoformat()
    assert payload_by_symbol["CL=F"]["technical_indicators"][0]["indicator_name"] == "sma_20"
    assert payload_by_symbol["CL=F"]["technical_indicators"][0]["points"][1]["indicator_value"] == 100.0
    assert payload_by_symbol["CL=F"]["historical_volatility"][0]["annualized_volatility"] == 0.32