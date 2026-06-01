import React from 'react'

import type { PriceHistorySeries } from '../lib/api'
import { getTickerColor } from '../lib/tickerColor'

type PriceHistoryChartProps = {
  series: PriceHistorySeries[]
}

const WIDTH = 920
const HEIGHT = 440
const MARGIN = {
  top: 28,
  right: 28,
  bottom: 44,
  left: 64,
}

const DATE_ONLY_REGEX = /^\d{4}-\d{2}-\d{2}$/

const parsePriceDate = (value: string): Date | null => {
  if (!value) {
    return null
  }

  const trimmed = value.trim()
  const candidate = DATE_ONLY_REGEX.test(trimmed) ? `${trimmed}T00:00:00Z` : trimmed
  const dateValue = new Date(candidate)
  return Number.isNaN(dateValue.getTime()) ? null : dateValue
}

const formatDate = (value: string): string => {
  const dateValue = parsePriceDate(value)
  if (!dateValue) {
    return 'Invalid date'
  }

  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(dateValue)
}

const buildPath = (
  data: Array<{ x: number; y: number }>,
): string => {
  return data.reduce((path, point, index) => `${path}${index === 0 ? 'M' : 'L'} ${point.x} ${point.y} `, '').trim()
}

const getPointDate = (point: { price_date?: string | null; timestamp?: string | null }): string | null => {
  const rawDate = point.price_date ?? point.timestamp ?? null
  if (typeof rawDate !== 'string') {
    return null
  }

  const trimmed = rawDate.trim()
  return trimmed.length > 0 ? trimmed : null
}

const hasPointDate = (point: { price_date?: string | null; timestamp?: string | null }): boolean => {
  return getPointDate(point) !== null
}

const isPriceOverlayIndicator = (indicatorName: string): boolean => {
  return indicatorName.startsWith('sma_') || indicatorName.startsWith('ema_')
}

const getIndicatorStroke = (indicatorName: string): string => {
  if (indicatorName.startsWith('sma_')) {
    return 'rgba(251, 191, 36, 0.9)'
  }

  if (indicatorName.startsWith('ema_')) {
    return 'rgba(34, 197, 94, 0.9)'
  }

  return 'rgba(148, 163, 184, 0.85)'
}

export default function PriceHistoryChart({ series }: PriceHistoryChartProps) {
  const getDisplayName = (item: PriceHistorySeries): string => item.short_name ?? item.symbol
  const chartCurrency = series.find((item) => item.currency)?.currency ?? 'USD'
  const allPoints = series.flatMap((item) => item.points)
  const indicatorPoints = series.flatMap((item) =>
    item.technical_indicators.flatMap((indicatorSeries) => indicatorSeries.points),
  )
  const allDates = Array.from(
    new Set([...allPoints, ...indicatorPoints].map((point) => getPointDate(point)).filter(Boolean)),
  ).sort() as string[]

  if (allDates.length === 0 || allPoints.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-white/10 bg-slate-950/50 p-6 text-sm text-slate-300">
        No chart data is available yet.
      </div>
    )
  }

  const values = allPoints.map((point) => point.price)
  const overlayValues = series.flatMap((item) =>
    item.technical_indicators
      .filter((indicatorSeries) => isPriceOverlayIndicator(indicatorSeries.indicator_name))
      .flatMap((indicatorSeries) => indicatorSeries.points.map((point) => point.indicator_value)),
  )
  const plotValues = overlayValues.length > 0 ? [...values, ...overlayValues] : values
  const minValue = Math.min(...values)
  const maxValue = Math.max(...plotValues)
  const range = maxValue - minValue || 1
  const minChartValue = minValue - range * 0.08
  const maxChartValue = maxValue + range * 0.08
  const chartWidth = WIDTH - MARGIN.left - MARGIN.right
  const chartHeight = HEIGHT - MARGIN.top - MARGIN.bottom
  const chartBottom = MARGIN.top + chartHeight
  const chartRight = MARGIN.left + chartWidth

  const xForDate = (date: string): number => {
    const index = allDates.indexOf(date)
    if (allDates.length <= 1) {
      return MARGIN.left + chartWidth / 2
    }
    return MARGIN.left + (chartWidth * index) / (allDates.length - 1)
  }

  const yForValue = (value: number): number => {
    const percentage = (value - minChartValue) / (maxChartValue - minChartValue || 1)
    return chartBottom - percentage * chartHeight
  }

  const yTicks = Array.from({ length: 5 }, (_, index) => {
    const value = minChartValue + ((maxChartValue - minChartValue) * index) / 4
    return value
  }).reverse()

  const xTickIndices = allDates.length <= 6
    ? allDates.map((_, index) => index)
    : [0, Math.floor((allDates.length - 1) * 0.25), Math.floor((allDates.length - 1) * 0.5), Math.floor((allDates.length - 1) * 0.75), allDates.length - 1]

  return (
    <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-4 px-1 pb-4">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-slate-400">30-day history</p>
          <p className="mt-2 text-lg font-semibold text-white">Tracked benchmark closing prices and overlays</p>
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-slate-300">
          {series.map((item) => (
            <React.Fragment key={item.ticker}>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: getTickerColor(item.ticker) }} />
                <span>{getDisplayName(item)}</span>
              </div>
              {item.technical_indicators
                .filter((indicatorSeries) => isPriceOverlayIndicator(indicatorSeries.indicator_name))
                .map((indicatorSeries) => (
                  <div
                    key={`${item.ticker}-${indicatorSeries.indicator_name}`}
                    className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/55 px-3 py-1.5"
                  >
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: getIndicatorStroke(indicatorSeries.indicator_name) }}
                    />
                    <span>{getDisplayName(item)} {indicatorSeries.indicator_label}</span>
                  </div>
                ))}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="px-1 pb-4 text-xs leading-6 text-slate-400">
        The chart overlays moving averages from persisted database rows. RSI and volatility are stored in the backend
        and shown in separate analysis modules below.
      </div>

      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full overflow-visible">
        {yTicks.map((value) => {
          const y = yForValue(value)
          return (
            <g key={value}>
              <line x1={MARGIN.left} y1={y} x2={chartRight} y2={y} stroke="rgba(148,163,184,0.15)" strokeDasharray="4 8" />
              <text x={MARGIN.left - 12} y={y + 4} textAnchor="end" className="fill-slate-400" fontSize="12">
                {chartCurrency} {value.toFixed(0)}
              </text>
            </g>
          )
        })}

        <line x1={MARGIN.left} y1={MARGIN.top} x2={MARGIN.left} y2={chartBottom} stroke="rgba(148,163,184,0.2)" />
        <line x1={MARGIN.left} y1={chartBottom} x2={chartRight} y2={chartBottom} stroke="rgba(148,163,184,0.2)" />

        {xTickIndices.map((index) => {
          const dateValue = allDates[index]
          const x = xForDate(dateValue)
          return (
            <g key={dateValue}>
              <line x1={x} y1={chartBottom} x2={x} y2={chartBottom + 8} stroke="rgba(148,163,184,0.2)" />
              <text x={x} y={chartBottom + 28} textAnchor="middle" className="fill-slate-400" fontSize="12">
                {formatDate(dateValue)}
              </text>
            </g>
          )
        })}

        {series
          .filter((item) => item.points.some((point) => hasPointDate(point)))
          .map((item) => {
          const orderedPoints = item.points
            .filter((point) => hasPointDate(point))
            .slice()
            .sort((left, right) => (getPointDate(left) ?? '').localeCompare(getPointDate(right) ?? ''))

          const mappedPoints = orderedPoints.map((point) => ({
            x: xForDate(getPointDate(point) ?? ''),
            y: yForValue(point.price),
          }))
          const path = buildPath(mappedPoints)
          const stroke = getTickerColor(item.ticker)

          return (
            <React.Fragment key={item.ticker}>
              <path d={path} fill="none" stroke={stroke} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              {mappedPoints.map((point, index) => (
                <circle key={`${item.ticker}-${orderedPoints[index].price_date}`} cx={point.x} cy={point.y} r="4" fill={stroke} stroke="#0f172a" strokeWidth="2" />
              ))}

              {item.technical_indicators
                .filter((indicatorSeries) => {
                  if (!isPriceOverlayIndicator(indicatorSeries.indicator_name)) return false
                  return indicatorSeries.points.some((point) => hasPointDate(point))
                })
                .map((indicatorSeries) => {
                  const mappedIndicatorPoints = indicatorSeries.points
                    .filter((point) => hasPointDate(point))
                    .slice()
                    .sort((left, right) => (getPointDate(left) ?? '').localeCompare(getPointDate(right) ?? ''))
                    .map((point) => ({
                      x: xForDate(getPointDate(point) ?? ''),
                      y: yForValue(point.indicator_value),
                    }))

                  const orderedIndicatorPoints = indicatorSeries.points
                    .filter((point) => hasPointDate(point))
                    .slice()
                    .sort((left, right) => (getPointDate(left) ?? '').localeCompare(getPointDate(right) ?? ''))

                  return (
                    <React.Fragment key={`${item.ticker}-${indicatorSeries.indicator_name}`}>
                      <path
                        d={buildPath(mappedIndicatorPoints)}
                        fill="none"
                        stroke={getIndicatorStroke(indicatorSeries.indicator_name)}
                        strokeDasharray="8 8"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      {mappedIndicatorPoints.map((point, index) => (
                        <circle
                          key={`${item.ticker}-${indicatorSeries.indicator_name}-${getPointDate(orderedIndicatorPoints[index]) ?? index}`}
                          cx={point.x}
                          cy={point.y}
                          r="3"
                          fill={getIndicatorStroke(indicatorSeries.indicator_name)}
                          stroke="#0f172a"
                          strokeWidth="1.5"
                        />
                      ))}
                    </React.Fragment>
                  )
                })}
            </React.Fragment>
          )
        })}
      </svg>
    </div>
  )
}
