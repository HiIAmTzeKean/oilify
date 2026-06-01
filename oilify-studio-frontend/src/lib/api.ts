const API_BASE = 'http://localhost:9000'

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

export type TechnicalIndicatorPoint = {
  timestamp?: string
  indicator_value: number
}

export type TechnicalIndicatorSeries = {
  indicator_name: string
  indicator_label: string
  points: TechnicalIndicatorPoint[]
}

export type HistoricalVolatilityPoint = {
  timestamp?: string
  annualized_volatility: number
}

export type HistoricalVolatilitySeries = {
  window_size: number
  annualization_factor: number
  points: HistoricalVolatilityPoint[]
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

export const apiFetch = (endpoint: string, options: RequestInit = {}): Promise<Response> => {
  const url = `${API_BASE}${endpoint}`
  const token = typeof window !== 'undefined' ? localStorage.getItem('oilify_access_token') : null
  const headers = new Headers(options.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(url, { ...options, headers })
}

export const buildUrl = (endpoint: string): string => {
  return `${API_BASE}${endpoint}`
}

export const getLatestPrices = async (): Promise<Price[]> => {
  const response = await apiFetch('/api/v1/prices/latest')
  if (!response.ok) {
    throw new Error(`Failed to load prices: ${response.status}`)
  }
  return response.json() as Promise<Price[]>
}

export const getPriceHistory = async (days = 30): Promise<PriceHistorySeries[]> => {
  const response = await apiFetch(`/api/v1/prices/history?days=${days}`)
  if (!response.ok) {
    throw new Error(`Failed to load price history: ${response.status}`)
  }
  return response.json() as Promise<PriceHistorySeries[]>
}

export const refreshPrices = async (): Promise<Price[]> => {
  const response = await apiFetch('/api/v1/prices/refresh', { method: 'POST' })
  if (!response.ok) {
    throw new Error(`Failed to refresh prices: ${response.status}`)
  }
  const payload = await response.json() as { prices: Price[] }
  return payload.prices
}