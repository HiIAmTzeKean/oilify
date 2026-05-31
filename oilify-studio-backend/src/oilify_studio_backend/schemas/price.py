from datetime import date, datetime

from pydantic import BaseModel


class PriceResponse(BaseModel):
    symbol: str
    ticker: str
    price_date: date
    price_usd: float
    currency: str
    source: str
    fetched_at: datetime


class PriceSyncResponse(BaseModel):
    updated_rows: int
    prices: list[PriceResponse]


class PriceHistoryPointResponse(BaseModel):
    price_date: date
    price_usd: float


class PriceHistorySeriesResponse(BaseModel):
    symbol: str
    ticker: str
    points: list[PriceHistoryPointResponse]
