import logging
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from oilify_studio_backend.db import Price, Tickers, get_db
from oilify_studio_backend.schemas.price import (
    PriceHistoryPointResponse,
    PriceHistorySeriesResponse,
    PriceResponse,
    PriceSyncResponse,
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

    return PriceResponse(
        symbol=ticker.symbol if ticker is not None else "",
        ticker=ticker.ticker if ticker is not None else "",
        short_name=ticker.short_name if ticker is not None else None,
        long_name=ticker.long_name if ticker is not None else None,
        price_date=row.price_date,
        price_usd=row.price_usd,
        currency=row.currency,
        source=row.source,
        fetched_at=row.fetched_at,
    )


def _group_history_points(db: Session, days: int) -> list[PriceHistorySeriesResponse]:
    points = fetch_historical_prices(db, days=days)
    grouped_points: dict[tuple[str, str], list[PriceHistoryPointResponse]] = defaultdict(list)

    for point in points:
        grouped_points[(point.symbol, point.ticker)].append(
            PriceHistoryPointResponse(
                price_date=point.price_date,
                price_usd=point.price_usd,
            )
        )

    ticker_rows = db.query(Tickers).order_by(Tickers.id).all()
    series: list[PriceHistorySeriesResponse] = []
    for ticker_row in ticker_rows:
        point_list = grouped_points.get((ticker_row.symbol, ticker_row.ticker), [])
        series.append(
            PriceHistorySeriesResponse(
                symbol=ticker_row.symbol,
                ticker=ticker_row.ticker,
                short_name=ticker_row.short_name,
                long_name=ticker_row.long_name,
                points=sorted(point_list, key=lambda point: point.price_date),
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
            prices = [_to_response(row, db) for row in rows]
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
