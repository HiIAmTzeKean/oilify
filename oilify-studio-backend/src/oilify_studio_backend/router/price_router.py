import logging
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from oilify_studio_backend.api_models.price import (
    HistoricalVolatilityPointResponse,
    PriceHistoryPointResponse,
    PriceHistorySeriesResponse,
    PriceIndicatorPointResponse,
    PriceIndicatorSeriesResponse,
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
    ingest_daily_prices,
)


logger = logging.getLogger(__name__)


def _to_response(row: Price, db: Session) -> PriceResponse:
    ticker = row.ticker
    if ticker is None:
        ticker = db.query(Tickers).filter(Tickers.id == row.ticker_id).one_or_none()

    previous_price_usd = getattr(row, "previous_price_usd", None)
    price_change_usd = None
    price_change_pct = None
    if previous_price_usd is not None:
        price_change_usd = row.price_usd - previous_price_usd
        if previous_price_usd != 0:
            price_change_pct = (price_change_usd / previous_price_usd) * 100

    return PriceResponse(
        symbol=ticker.symbol if ticker is not None else "",
        ticker=ticker.ticker if ticker is not None else "",
        short_name=ticker.short_name if ticker is not None else None,
        long_name=ticker.long_name if ticker is not None else None,
        price_date=row.price_date,
        price_usd=row.price_usd,
        previous_price_usd=previous_price_usd,
        price_change_usd=price_change_usd,
        price_change_pct=price_change_pct,
        currency=row.currency,
        source=row.source,
        fetched_at=row.fetched_at,
    )


def _group_history_points(db: Session, days: int) -> list[PriceHistorySeriesResponse]:
    points = fetch_historical_prices(db, days=days)
    grouped_points: dict[tuple[str, str], list[PriceHistoryPointResponse]] = defaultdict(list)
    cutoff_date: date | None = None

    for point in points:
        if cutoff_date is None or point.price_date < cutoff_date:
            cutoff_date = point.price_date
        grouped_points[(point.symbol, point.ticker)].append(
            PriceHistoryPointResponse(
                price_date=point.price_date,
                price_usd=point.price_usd,
            )
        )

    indicator_series: dict[tuple[str, str], dict[str, list[PriceIndicatorPointResponse]]] = defaultdict(
        lambda: defaultdict(list)
    )
    volatility_series: dict[tuple[str, str], list[HistoricalVolatilityPointResponse]] = defaultdict(list)

    if cutoff_date is not None:
        indicator_rows = (
            db.query(Tickers, TechnicalIndicator)
            .join(TechnicalIndicator, TechnicalIndicator.ticker_id == Tickers.id)
            .filter(TechnicalIndicator.indicator_date >= cutoff_date)
            .order_by(Tickers.id, TechnicalIndicator.indicator_name, TechnicalIndicator.indicator_date)
            .all()
        )
        for ticker_row, indicator_row in indicator_rows:
            indicator_series[(ticker_row.symbol, ticker_row.ticker)][indicator_row.indicator_name].append(
                PriceIndicatorPointResponse(
                    price_date=indicator_row.indicator_date,
                    indicator_value=indicator_row.indicator_value,
                )
            )

        volatility_rows = (
            db.query(Tickers, HistoricalVolatility)
            .join(HistoricalVolatility, HistoricalVolatility.ticker_id == Tickers.id)
            .filter(HistoricalVolatility.volatility_date >= cutoff_date)
            .order_by(Tickers.id, HistoricalVolatility.volatility_date)
            .all()
        )
        for ticker_row, volatility_row in volatility_rows:
            volatility_series[(ticker_row.symbol, ticker_row.ticker)].append(
                HistoricalVolatilityPointResponse(
                    price_date=volatility_row.volatility_date,
                    annualized_volatility=volatility_row.annualized_volatility,
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
                points=points,
            )
            for indicator_name, points in indicator_series.get(series_key, {}).items()
        ]
        series.append(
            PriceHistorySeriesResponse(
                symbol=ticker_row.symbol,
                ticker=ticker_row.ticker,
                short_name=ticker_row.short_name,
                long_name=ticker_row.long_name,
                points=sorted(point_list, key=lambda point: point.price_date),
                technical_indicators=indicator_list,
                historical_volatility=sorted(
                    volatility_series.get(series_key, []), key=lambda point: point.price_date
                ),
            )
        )

    return series


def create_price_router() -> APIRouter:
    router = APIRouter(prefix="/prices", tags=["Prices"])

    @router.post("/refresh", response_model=PriceSyncResponse)
    def refresh_prices(db: Session = Depends(get_db)) -> PriceSyncResponse:
        logger.info("Price refresh requested")
        try:
            rows = ingest_daily_prices(db)
            prices = [_to_response(row, db) for row in rows]
            logger.info("Price refresh completed updated_rows=%s", len(prices))
            logger.debug(
                "Price refresh returned symbols=%s",
                [price.symbol for price in prices],
            )
            return PriceSyncResponse(updated_rows=len(prices), prices=prices)
        except Exception:
            logger.exception("Price refresh failed")
            raise

    @router.get("/latest", response_model=list[PriceResponse])
    def get_latest_prices_route(db: Session = Depends(get_db)) -> list[PriceResponse]:
        logger.info("Latest price lookup requested")
        try:
            rows = get_latest_prices(db)
            prices = [_to_response(row.current, db) for row in rows]
            for index, row in enumerate(rows):
                previous_price_usd = row.previous.price_usd if row.previous is not None else None
                prices[index].previous_price_usd = previous_price_usd
                if previous_price_usd is not None:
                    prices[index].price_change_usd = prices[index].price_usd - previous_price_usd
                    if previous_price_usd != 0:
                        prices[index].price_change_pct = (
                            prices[index].price_change_usd / previous_price_usd
                        ) * 100
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
        logger.info("Daily price lookup requested for date=%s", target_date)
        try:
            rows = (
                db.query(Price)
                .options(joinedload(Price.ticker))
                .filter(Price.price_date == target_date)
                .all()
            )
            prices = [_to_response(row, db) for row in rows]
            logger.debug("Daily price lookup returned count=%s", len(prices))
            return prices
        except Exception:
            logger.exception("Daily price lookup failed for date=%s", target_date)
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
