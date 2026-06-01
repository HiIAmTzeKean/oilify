import type { HistoricalVolatilitySeries } from './volatility'
import type { TechnicalIndicatorSeries } from './technicals'

export type Price = {
  symbol: string
  ticker: string
  short_name?: string | null
  long_name?: string | null
  timestamp?: string
  price: number
  previous_price?: number | null
  price_change?: number | null
  price_change_pct?: number | null
  currency: string
  source: string
  fetched_at: string
}

export type PriceHistoryPoint = {
  timestamp?: string
  price: number
}

export type PriceHistorySeries = {
  symbol: string
  ticker: string
  short_name?: string | null
  long_name?: string | null
  currency?: string | null
  points: PriceHistoryPoint[]
  technical_indicators: TechnicalIndicatorSeries[]
  historical_volatility: HistoricalVolatilitySeries[]
}
