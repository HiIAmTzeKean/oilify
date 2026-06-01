import logging
from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from oilify_studio_backend.api_models.price import (
    HistoricalVolatilityPointResponse,
    PriceHistoryPointResponse,
    PriceHistorySeriesResponse,
    PriceIndicatorPointResponse,
    PriceIndicatorSeriesResponse,
    HistoricalVolatilitySeriesResponse,
    PriceResponse,
    PriceSyncResponse,
)
from oilify_studio_backend.db import (
    HistoricalVolatility,
    Price,
    TechnicalIndicator,
    Tickers,
    get_db,
)
from oilify_studio_backend.services.price import (
    fetch_historical_prices,
    get_latest_prices,
    ingest_prices,
)


logger = logging.getLogger(__name__)


def _to_response(row: Price, db: Session, previous_price: float | None = None) -> PriceResponse:
    ticker = row.ticker
    if ticker is None:
        ticker = db.query(Tickers).filter(Tickers.id == row.ticker_id).one_or_none()

    if previous_price is None:
        previous_price = getattr(row, "previous_price", None)

    price_change = None
    price_change_pct = None
    if previous_price is not None:
        price_change = row.price - previous_price
        if previous_price != 0:
            price_change_pct = (price_change / previous_price) * 100

    return PriceResponse(
        symbol=ticker.symbol if ticker is not None else "",
        ticker=ticker.ticker if ticker is not None else "",
        short_name=ticker.short_name if ticker is not None else None,
        long_name=ticker.long_name if ticker is not None else None,
        timestamp=row.timestamp,
        price=row.price,
        previous_price=previous_price,
        price_change=price_change,
        price_change_pct=price_change_pct,
        currency=row.currency,
        source=row.source,
        fetched_at=row.fetched_at,
    )


def _group_history_points(db: Session, days: int) -> list[PriceHistorySeriesResponse]:
    points = fetch_historical_prices(db, days=days)
    grouped_points: dict[tuple[str, str], list[PriceHistoryPointResponse]] = defaultdict(list)
    series_currency: dict[tuple[str, str], str] = {}
    cutoff_date: date | None = None

    for point in points:
        point_date = point.timestamp.date()
        if cutoff_date is None or point_date < cutoff_date:
            cutoff_date = point_date
        series_key = (point.symbol, point.ticker)
        series_currency.setdefault(series_key, point.currency)
        grouped_points[series_key].append(
            PriceHistoryPointResponse(
                timestamp=point.timestamp,
                price=point.price,
            )
        )

    # indicator_series: series_key -> (indicator_name, window_size) -> points
    indicator_series: dict[tuple[str, str], dict[tuple[str, int], list[PriceIndicatorPointResponse]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    # volatility_series: series_key -> window_size -> {annualization_factor, points}
    volatility_series: dict[tuple[str, str], dict[int, dict]] = defaultdict(lambda: defaultdict(dict))

    if cutoff_date is not None:
        indicator_rows = (
            db.query(Tickers, TechnicalIndicator)
            .join(TechnicalIndicator, TechnicalIndicator.ticker_id == Tickers.id)
            .filter(TechnicalIndicator.date >= cutoff_date)
            .order_by(
                Tickers.id,
                TechnicalIndicator.name,
                TechnicalIndicator.window_size,
                TechnicalIndicator.date,
            )
            .all()
        )
        for ticker_row, indicator_row in indicator_rows:
            series_key = (ticker_row.symbol, ticker_row.ticker)
            key = (indicator_row.name, indicator_row.window_size)
            indicator_series[series_key][key].append(
                PriceIndicatorPointResponse(
                    timestamp=datetime.combine(indicator_row.date, datetime.min.time()),
                    indicator_value=indicator_row.value,
                )
            )

        volatility_rows = (
            db.query(Tickers, HistoricalVolatility)
            .join(HistoricalVolatility, HistoricalVolatility.ticker_id == Tickers.id)
            .filter(HistoricalVolatility.date >= cutoff_date)
            .order_by(Tickers.id, HistoricalVolatility.window_size, HistoricalVolatility.date)
            .all()
        )
        for ticker_row, volatility_row in volatility_rows:
            series_key = (ticker_row.symbol, ticker_row.ticker)
            ws = volatility_row.window_size
            entry = volatility_series[series_key].get(ws)
            if not entry:
                volatility_series[series_key][ws] = {
                    "annualization_factor": volatility_row.annualization_factor,
                    "points": [],
                }
                entry = volatility_series[series_key][ws]

            entry["points"].append(
                HistoricalVolatilityPointResponse(
                    timestamp=datetime.combine(volatility_row.date, datetime.min.time()),
                    annualized_volatility=volatility_row.value,
                )
            )

    ticker_rows = db.query(Tickers).order_by(Tickers.id).all()
    series: list[PriceHistorySeriesResponse] = []
    for ticker_row in ticker_rows:
        series_key = (ticker_row.symbol, ticker_row.ticker)
        point_list = grouped_points.get((ticker_row.symbol, ticker_row.ticker), [])
        indicator_list = [
            PriceIndicatorSeriesResponse(
                indicator_name=indicator_name,
                indicator_label=indicator_name.replace("_", " ").upper(),
                window_size=window_size,
                points=points,
            )
            for (indicator_name, window_size), points in indicator_series.get(series_key, {}).items()
        ]
        # build volatility series objects
        hv_series_list: list[HistoricalVolatilitySeriesResponse] = []
        for ws, entry in sorted(volatility_series.get(series_key, {}).items()):
            hv_series_list.append(
                HistoricalVolatilitySeriesResponse(
                    window_size=ws,
                    annualization_factor=entry["annualization_factor"],
                    points=sorted(entry["points"], key=lambda p: p.timestamp),
                )
            )

        series.append(
            PriceHistorySeriesResponse(
                symbol=ticker_row.symbol,
                ticker=ticker_row.ticker,
                short_name=ticker_row.short_name,
                long_name=ticker_row.long_name,
                currency=series_currency.get(series_key),
                points=sorted(point_list, key=lambda point: point.timestamp),
                technical_indicators=indicator_list,
                historical_volatility=hv_series_list,
            )
        )

    return series


def create_price_router() -> APIRouter:
    router = APIRouter(prefix="/prices", tags=["Prices"])

    @router.post("/refresh", response_model=PriceSyncResponse)
    def refresh_prices(db: Session = Depends(get_db)) -> PriceSyncResponse:
        logger.info("Price refresh requested")
        try:
            rows = ingest_prices(db)
            latest_rows = get_latest_prices(db)
            latest_rows_by_ticker_id = {row.current.ticker_id: row for row in latest_rows}
            prices = []
            for row in rows:
                latest_row = latest_rows_by_ticker_id.get(row.ticker_id)
                previous_price = None
                if latest_row is not None and latest_row.previous is not None:
                    previous_price = latest_row.previous.price

                prices.append(_to_response(row, db, previous_price))
            logger.info("Price refresh completed updated_rows=%s", len(prices))
            logger.debug(
                "Price refresh returned symbols=%s",
                [price.symbol for price in prices],
            )
            return PriceSyncResponse(updated_rows=len(rows), prices=prices)
        except Exception:
            logger.exception("Price refresh failed")
            raise

    @router.get("/latest", response_model=list[PriceResponse])
    def get_latest_prices_route(db: Session = Depends(get_db)) -> list[PriceResponse]:
        logger.info("Latest price lookup requested")
        try:
            rows = get_latest_prices(db)
            prices = []
            for row in rows:
                previous_price = row.previous.price if row.previous is not None else None
                prices.append(_to_response(row.current, db, previous_price))
            logger.debug(
                "Latest price lookup returned symbols=%s",
                [price.symbol for price in prices],
            )
            return prices
        except Exception:
            logger.exception("Latest price lookup failed")
            raise

    @router.get("/daily", response_model=list[PriceResponse])
    def get_prices_for_date(
        target_date: date = Query(..., alias="date"),
        db: Session = Depends(get_db),
    ) -> list[PriceResponse]:
        logger.info("Price lookup requested for date=%s", target_date)
        try:
            rows = (
                db.query(Price)
                .options(joinedload(Price.ticker))
                .filter(Price.timestamp >= target_date, Price.timestamp < date(target_date.year, target_date.month, target_date.day + 1))
                .all()
            )
            prices = [_to_response(row, db) for row in rows]
            logger.debug("Price lookup returned count=%s", len(prices))
            return prices
        except Exception:
            logger.exception("Price lookup failed for date=%s", target_date)
            raise

    @router.get("/history", response_model=list[PriceHistorySeriesResponse])
    def get_price_history(
        days: int = Query(30, ge=1, le=365),
        db: Session = Depends(get_db),
    ) -> list[PriceHistorySeriesResponse]:
        logger.info("Historical price lookup requested days=%s", days)
        try:
            series = _group_history_points(db, days)
            logger.debug(
                "Historical price lookup returned series=%s",
                [item.symbol for item in series],
            )
            return series
        except Exception:
            logger.exception("Historical price lookup failed days=%s", days)
            raise

    return router
