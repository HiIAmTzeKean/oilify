import React from 'react'

import type { PriceHistorySeries } from '../lib/api'
import { getTickerColor } from '../lib/tickerColor'

type VolatilityChartProps = {
  series: PriceHistorySeries[]
}

const WIDTH = 920
const HEIGHT = 280
const MARGIN = {
  top: 28,
  right: 28,
  bottom: 44,
  left: 64,
}

const formatDate = (value: string): string => {
  const dateValue = new Date(`${value}T00:00:00`)
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(dateValue)
}

const buildPath = (data: Array<{ x: number; y: number }>): string => {
  return data.reduce((path, point, index) => `${path}${index === 0 ? 'M' : 'L'} ${point.x} ${point.y} `, '').trim()
}

export default function VolatilityChart({ series }: VolatilityChartProps) {
  const volatilityPoints = series.flatMap((item) => item.historical_volatility)
  const allDates = Array.from(new Set(volatilityPoints.map((point) => point.price_date))).sort()

  if (allDates.length === 0 || volatilityPoints.length === 0) {
    return (
      <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-6 text-sm text-slate-300">
        No volatility history is available yet.
      </div>
    )
  }

  const values = volatilityPoints.map((point) => point.annualized_volatility * 100)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const range = maxValue - minValue || 1
  const minChartValue = Math.max(0, minValue - range * 0.08)
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

  const yTicks = Array.from({ length: 4 }, (_, index) => {
    const value = minChartValue + ((maxChartValue - minChartValue) * index) / 3
    return value
  }).reverse()

  const xTickIndices = allDates.length <= 6
    ? allDates.map((_, index) => index)
    : [0, Math.floor((allDates.length - 1) * 0.33), Math.floor((allDates.length - 1) * 0.66), allDates.length - 1]

  return (
    <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-5 shadow-2xl shadow-black/20 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-4 px-1 pb-4">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Volatility analysis</p>
          <p className="mt-2 text-lg font-semibold text-white">20-day historical volatility</p>
        </div>
        <div className="flex flex-wrap gap-3 text-xs text-slate-300">
          {series.map((item) => {
            const lastVolatility = item.historical_volatility.at(-1)
            return (
              <div key={item.ticker} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: getTickerColor(item.ticker) }} />
                <span>
                  {item.short_name ?? item.symbol}
                  {lastVolatility ? ` ${Math.round(lastVolatility.annualized_volatility * 1000) / 10}%` : ''}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full overflow-visible">
        {yTicks.map((value) => {
          const y = yForValue(value)
          return (
            <g key={value}>
              <line x1={MARGIN.left} y1={y} x2={chartRight} y2={y} stroke="rgba(148,163,184,0.15)" strokeDasharray="4 8" />
              <text x={MARGIN.left - 12} y={y + 4} textAnchor="end" className="fill-slate-400" fontSize="12">
                {value.toFixed(1)}%
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

        {series.map((item) => {
          const orderedPoints = [...item.historical_volatility].sort((left, right) => left.price_date.localeCompare(right.price_date))
          const mappedPoints = orderedPoints.map((point) => ({
            x: xForDate(point.price_date),
            y: yForValue(point.annualized_volatility * 100),
          }))
          const stroke = getTickerColor(item.ticker)

          return (
            <React.Fragment key={item.ticker}>
              <path
                d={buildPath(mappedPoints)}
                fill="none"
                stroke={stroke}
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d={`${buildPath(mappedPoints)} L ${mappedPoints.at(-1)?.x ?? MARGIN.left} ${chartBottom} L ${mappedPoints[0]?.x ?? MARGIN.left} ${chartBottom} Z`}
                fill={stroke}
                opacity="0.08"
              />
              {mappedPoints.map((point, index) => (
                <circle
                  key={`${item.ticker}-${orderedPoints[index].price_date}`}
                  cx={point.x}
                  cy={point.y}
                  r="4"
                  fill={stroke}
                  stroke="#0f172a"
                  strokeWidth="2"
                />
              ))}
            </React.Fragment>
          )
        })}
      </svg>
    </div>
  )
}
