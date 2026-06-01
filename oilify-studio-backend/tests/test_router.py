"""Tests for the Oilify price router."""

from datetime import UTC, date, datetime, timedelta

from oilify_studio_backend.db.schema import HistoricalVolatility, Price, TechnicalIndicator, Tickers
from oilify_studio_backend.services.price import PricePoint, _round_to_30min, upsert_prices


def _make_price(
    *,
    ticker_id: int,
    timestamp: datetime,
    price: float,
) -> Price:
    return Price(
        ticker_id=ticker_id,
        timestamp=timestamp,
        price=price,
        currency="USD",
        source="yahoo_finance",
        fetched_at=datetime.now(UTC),
    )


def _make_ticker(*, symbol: str, ticker: str, short_name: str, long_name: str) -> Tickers:
    return Tickers(
        symbol=symbol,
        ticker=ticker,
        short_name=short_name,
        long_name=long_name,
    )


def test_refresh_prices_returns_upserted_rows(client, mocker) -> None:
    now = datetime.now(UTC)
    rows = [
        _make_price(ticker_id=1, price_at=now, price=101.0),
        _make_price(ticker_id=2, price_at=now, price=103.5),
    ]
    mocker.patch(
        "oilify_studio_backend.router.price_router.ingest_prices",
        return_value=rows,
    )

    response = client.post("/api/v1/prices/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated_rows"] == 2
    assert [item["symbol"] for item in payload["prices"]] == ["CL=F", "BZ=F"]
    assert [item["short_name"] for item in payload["prices"]] == ["CL=F short", "BZ=F short"]


def test_refresh_prices_includes_previous_day_comparison(client, db_session, mocker) -> None:
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    custom_ticker = Tickers(symbol="TEST", ticker="TEST")
    db_session.add(custom_ticker)
    db_session.flush()
        db_session.add(
            _make_price(
                ticker_id=custom_ticker.id,
                timestamp=yesterday_start,
                price=99.0,
            )
        )
    db_session.commit()

    price_at = _round_to_30min(now)
    current_points = [PricePoint("TEST", "TEST", 101.0, "USD", price_at, now)]
    mocker.patch(
        "oilify_studio_backend.router.price_router.ingest_prices",
        side_effect=lambda db: upsert_prices(db, current_points),
    )

    response = client.post("/api/v1/prices/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["updated_rows"] == 1
    assert payload["prices"][0]["previous_price"] == 99.0
    assert payload["prices"][0]["price_change"] == 2.0
    assert round(payload["prices"][0]["price_change_pct"], 2) == 2.02


def test_latest_prices_returns_latest_rows(client, db_session) -> None:
    now = datetime.now(UTC)
    today = now.date()
    yesterday = today - timedelta(days=1)
    yesterday_start = datetime.combine(yesterday, datetime.min.time(), tzinfo=UTC)
    today_start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)

    alpha_ticker = _make_ticker(symbol="LATE1", ticker="LATE1", short_name="Late 1", long_name="Late One")
    beta_ticker = _make_ticker(symbol="LATE2", ticker="LATE2", short_name="Late 2", long_name="Late Two")
    db_session.add_all([alpha_ticker, beta_ticker])
    db_session.flush()

    db_session.add_all(
        [
                _make_price(ticker_id=alpha_ticker.id, timestamp=yesterday_start, price=99.0),
                _make_price(ticker_id=alpha_ticker.id, timestamp=today_start, price=100.0),
                _make_price(ticker_id=beta_ticker.id, timestamp=yesterday_start, price=101.0),
                _make_price(ticker_id=beta_ticker.id, timestamp=today_start, price=102.0),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/prices/latest")

    assert response.status_code == 200
    payload = response.json()
    payload_by_symbol = {item["symbol"]: item for item in payload}
    assert payload_by_symbol["LATE1"]["short_name"] == "Late 1"
    assert payload_by_symbol["LATE2"]["short_name"] == "Late 2"
        assert payload_by_symbol["LATE1"]["timestamp"] == today_start.replace(tzinfo=None).isoformat()
        assert payload_by_symbol["LATE2"]["timestamp"] == today_start.replace(tzinfo=None).isoformat()
    assert payload_by_symbol["LATE1"]["previous_price"] == 99.0
    assert payload_by_symbol["LATE1"]["price_change"] == 1.0
    assert round(payload_by_symbol["LATE1"]["price_change_pct"], 2) == 1.01


def test_daily_prices_filters_by_date(client, db_session) -> None:
    target_date = date.today() + timedelta(days=7)
    other_day = target_date - timedelta(days=1)
    target_start = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
    other_day_start = datetime.combine(other_day, datetime.min.time(), tzinfo=UTC)

    custom_ticker = _make_ticker(symbol="DAILY1", ticker="DAILY1", short_name="Daily 1", long_name="Daily One")
    db_session.add(custom_ticker)
    db_session.flush()

    db_session.add_all(
        [
                _make_price(ticker_id=custom_ticker.id, timestamp=other_day_start, price=98.0),
                _make_price(ticker_id=custom_ticker.id, timestamp=target_start, price=100.0),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/prices/daily?date={target_date.isoformat()}")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
        assert payload[0]["timestamp"] == target_start.replace(tzinfo=None).isoformat()
    assert payload[0]["price"] == 100.0


def test_history_prices_returns_grouped_series(client, db_session, mocker) -> None:
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
    yesterday_start = datetime.combine(yesterday, datetime.min.time(), tzinfo=UTC)
    custom_ticker = _make_ticker(
        symbol="HIST1",
        ticker="HIST1",
        short_name="Hist 1",
        long_name="Hist One",
    )
    db_session.add(custom_ticker)
    db_session.flush()
    db_session.add_all(
        [
            TechnicalIndicator(
                ticker_id=custom_ticker.id,
                date=yesterday,
                name="sma_20",
                value=99.0,
                window_size=20,
            ),
            TechnicalIndicator(
                ticker_id=custom_ticker.id,
                date=today,
                name="sma_20",
                value=100.0,
                window_size=20,
            ),
            HistoricalVolatility(
                ticker_id=custom_ticker.id,
                date=today,
                value=0.32,
                window_size=20,
                annualization_factor=252,
            ),
        ]
    )
    db_session.commit()

    points = [
        PricePoint("HIST1", "HIST1", 99.5, "USD", yesterday_start, datetime.now(UTC)),
        PricePoint("HIST1", "HIST1", 100.5, "USD", today_start, datetime.now(UTC)),
    ]
    mocker.patch(
        "oilify_studio_backend.router.price_router.fetch_historical_prices",
        return_value=points,
    )

    response = client.get("/api/v1/prices/history?days=30")

    assert response.status_code == 200
    payload = response.json()
    payload_by_symbol = {item["symbol"]: item for item in payload}
    assert payload_by_symbol["HIST1"]["short_name"] == "Hist 1"
    assert len(payload_by_symbol["HIST1"]["points"]) == 2
        assert payload_by_symbol["HIST1"]["points"][0]["timestamp"] == yesterday_start.isoformat().replace("+00:00", "Z")
        assert payload_by_symbol["HIST1"]["points"][1]["timestamp"] == today_start.isoformat().replace("+00:00", "Z")
    assert payload_by_symbol["HIST1"]["technical_indicators"][0]["indicator_name"] == "sma_20"
    assert payload_by_symbol["HIST1"]["technical_indicators"][0]["points"][1]["indicator_value"] == 100.0
    assert payload_by_symbol["HIST1"]["historical_volatility"][0]["points"][0]["annualized_volatility"] == 0.32