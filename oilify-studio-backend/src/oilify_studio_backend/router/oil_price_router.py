import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from oilify_studio_backend.db import Price, get_db
from oilify_studio_backend.schemas import OilPriceResponse, OilPriceSyncResponse
from oilify_studio_backend.services.oil_price import (
    get_latest_daily_prices,
    ingest_daily_oil_prices,
)


logger = logging.getLogger(__name__)


def _to_response(row: Price) -> OilPriceResponse:
    return OilPriceResponse(
        symbol=row.ticker.symbol,
        ticker=row.ticker.ticker,
        price_date=row.price_date,
        price_usd=row.price_usd,
        currency=row.currency,
        source=row.source,
        fetched_at=row.fetched_at,
    )


def create_oil_price_router() -> APIRouter:
    router = APIRouter(prefix="/oil-prices", tags=["Oil Prices"])

    @router.post("/refresh", response_model=OilPriceSyncResponse)
    def refresh_prices(db: Session = Depends(get_db)) -> OilPriceSyncResponse:
        logger.info("Oil price refresh requested")
        try:
            rows = ingest_daily_oil_prices(db)
            prices = [_to_response(row) for row in rows]
            logger.info("Oil price refresh completed updated_rows=%s", len(prices))
            logger.debug(
                "Oil price refresh returned symbols=%s",
                [price.symbol for price in prices],
            )
            return OilPriceSyncResponse(updated_rows=len(prices), prices=prices)
        except Exception:
            logger.exception("Oil price refresh failed")
            raise

    @router.get("/latest", response_model=list[OilPriceResponse])
    def get_latest_prices(db: Session = Depends(get_db)) -> list[OilPriceResponse]:
        logger.info("Latest oil price lookup requested")
        try:
            rows = get_latest_daily_prices(db)
            prices = [_to_response(row) for row in rows]
            logger.debug(
                "Latest oil price lookup returned symbols=%s",
                [price.symbol for price in prices],
            )
            return prices
        except Exception:
            logger.exception("Latest oil price lookup failed")
            raise

    @router.get("/daily", response_model=list[OilPriceResponse])
    def get_prices_for_date(
        target_date: date = Query(..., alias="date"),
        db: Session = Depends(get_db),
    ) -> list[OilPriceResponse]:
        logger.info("Daily oil price lookup requested for date=%s", target_date)
        try:
            rows = (
                db.query(Price)
                .options(joinedload(Price.ticker))
                .filter(Price.price_date == target_date)
                .all()
            )
            prices = [_to_response(row) for row in rows]
            logger.debug("Daily oil price lookup returned count=%s", len(prices))
            return prices
        except Exception:
            logger.exception("Daily oil price lookup failed for date=%s", target_date)
            raise

    return router
