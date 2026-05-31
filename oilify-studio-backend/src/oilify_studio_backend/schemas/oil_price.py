from datetime import date, datetime

from pydantic import BaseModel


class OilPriceResponse(BaseModel):
    symbol: str
    ticker: str
    price_date: date
    price_usd: float
    currency: str
    source: str
    fetched_at: datetime


class OilPriceSyncResponse(BaseModel):
    updated_rows: int
    prices: list[OilPriceResponse]
