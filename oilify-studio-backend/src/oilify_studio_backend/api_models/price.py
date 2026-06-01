from datetime import datetime

from pydantic import BaseModel, Field


class PriceResponse(BaseModel):
    symbol: str
    ticker: str
    short_name: str | None = None
    long_name: str | None = None
    price_at: datetime
    price: float
    previous_price: float | None = None
    price_change: float | None = None
    price_change_pct: float | None = None
    currency: str
    source: str
    fetched_at: datetime


class PriceSyncResponse(BaseModel):
    updated_rows: int
    prices: list[PriceResponse]


class PriceHistoryPointResponse(BaseModel):
    price_at: datetime
    price: float


class PriceIndicatorPointResponse(BaseModel):
    price_at: datetime
    indicator_value: float


class PriceIndicatorSeriesResponse(BaseModel):
    indicator_name: str
    indicator_label: str
    window_size: int | None = None
    points: list[PriceIndicatorPointResponse]


class HistoricalVolatilityPointResponse(BaseModel):
    price_at: datetime
    annualized_volatility: float


class HistoricalVolatilitySeriesResponse(BaseModel):
    window_size: int
    annualization_factor: int
    points: list[HistoricalVolatilityPointResponse]


class PriceHistorySeriesResponse(BaseModel):
    symbol: str
    ticker: str
    short_name: str | None = None
    long_name: str | None = None
    currency: str | None = None
    points: list[PriceHistoryPointResponse]
    technical_indicators: list[PriceIndicatorSeriesResponse] = Field(default_factory=list)
    historical_volatility: list[HistoricalVolatilitySeriesResponse] = Field(default_factory=list)
