export type HistoricalVolatilityPoint = {
  timestamp?: string
  annualized_volatility: number
}

export type HistoricalVolatilitySeries = {
  window_size: number
  annualization_factor: number
  points: HistoricalVolatilityPoint[]
}
