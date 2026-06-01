import type { Price, PriceHistorySeries } from '../types'

const API_BASE = 'http://localhost:9000'

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