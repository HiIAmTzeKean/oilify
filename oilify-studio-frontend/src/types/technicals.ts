export type TechnicalIndicatorPoint = {
  timestamp?: string
  indicator_value: number
}

export type TechnicalIndicatorSeries = {
  indicator_name: string
  indicator_label: string
  points: TechnicalIndicatorPoint[]
}
