from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from oilify_backend.db import OilPriceDaily, get_db
from oilify_backend.schemas import OilPriceResponse, OilPriceSyncResponse
from oilify_backend.services.oil_price import get_latest_daily_prices, ingest_daily_oil_prices


def _to_response(row: OilPriceDaily) -> OilPriceResponse:
    return OilPriceResponse(
        symbol=row.symbol,
        ticker=row.ticker,
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
        rows = ingest_daily_oil_prices(db)
        prices = [_to_response(row) for row in rows]
        return OilPriceSyncResponse(updated_rows=len(prices), prices=prices)

    @router.get("/latest", response_model=list[OilPriceResponse])
    def get_latest_prices(db: Session = Depends(get_db)) -> list[OilPriceResponse]:
        rows = get_latest_daily_prices(db)
        return [_to_response(row) for row in rows]

    @router.get("/daily", response_model=list[OilPriceResponse])
    def get_prices_for_date(
        target_date: date = Query(..., alias="date"),
        db: Session = Depends(get_db),
    ) -> list[OilPriceResponse]:
        rows = db.query(OilPriceDaily).filter(OilPriceDaily.price_date == target_date).all()
        return [_to_response(row) for row in rows]

    return router
