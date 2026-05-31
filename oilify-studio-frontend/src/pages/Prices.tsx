import React from 'react'

import PriceHistoryChart from '../components/PriceHistoryChart'
import VolatilityChart from '../components/VolatilityChart'
import {
  getLatestPrices,
  getPriceHistory,
  refreshPrices,
  type Price,
  type PriceHistorySeries,
} from '../lib/api'
import { getTickerColor } from '../lib/tickerColor'

const HISTORY_DAYS = 30

export default function Prices() {
  const [prices, setPrices] = React.useState<Price[]>([])
  const [history, setHistory] = React.useState<PriceHistorySeries[]>([])
  const [selectedTickers, setSelectedTickers] = React.useState<string[]>([])
  const [loadingPrices, setLoadingPrices] = React.useState(true)
  const [loadingHistory, setLoadingHistory] = React.useState(true)
  const [syncing, setSyncing] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const loadLatestPrices = React.useCallback(async () => {
    setLoadingPrices(true)
    try {
      const latest = await getLatestPrices()
      if (latest.length > 0) {
        setPrices(latest)
        return
      }

      const refreshed = await refreshPrices()
      setPrices(refreshed)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoadingPrices(false)
    }
  }, [])

  const loadHistory = React.useCallback(async () => {
    setLoadingHistory(true)
    try {
      const series = await getPriceHistory(HISTORY_DAYS)
      setHistory(series)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoadingHistory(false)
    }
  }, [])

  React.useEffect(() => {
    void loadLatestPrices()
    void loadHistory()
  }, [loadHistory, loadLatestPrices])

  React.useEffect(() => {
    if (history.length === 0) {
      return
    }

    setSelectedTickers((currentSelection) => {
      const availableTickers = history.map((item) => item.ticker)
      const nextSelection = currentSelection.filter((ticker) => availableTickers.includes(ticker))
      return nextSelection.length > 0 ? nextSelection : availableTickers
    })
  }, [history])

  const getDisplayName = (item: Price): string => item.short_name ?? item.symbol
  const getSeriesDisplayName = (item: PriceHistorySeries): string => item.short_name ?? item.symbol

  const visibleHistory = React.useMemo(
    () => history.filter((item) => selectedTickers.includes(item.ticker)),
    [history, selectedTickers],
  )

  const formatChange = (price: Price): { label: string | null; tone: string } => {
    if (price.price_change_usd === undefined || price.price_change_usd === null || price.previous_price_usd === null) {
      return { label: null, tone: 'bg-slate-400/15 text-slate-300' }
    }

    if (price.price_change_usd > 0) {
      return {
        label: `▲ ${price.price_change_usd.toFixed(2)} (${price.price_change_pct?.toFixed(2) ?? '0.00'}%)`,
        tone: 'bg-emerald-400/15 text-emerald-300',
      }
    }

    if (price.price_change_usd < 0) {
      return {
        label: `▼ ${Math.abs(price.price_change_usd).toFixed(2)} (${Math.abs(price.price_change_pct ?? 0).toFixed(2)}%)`,
        tone: 'bg-rose-400/15 text-rose-300',
      }
    }

    return { label: '• flat vs yesterday', tone: 'bg-slate-400/15 text-slate-300' }
  }

  function toggleTicker(ticker: string) {
    setSelectedTickers((currentSelection) => {
      if (currentSelection.includes(ticker)) {
        if (currentSelection.length === 1) {
          return currentSelection
        }
        return currentSelection.filter((item) => item !== ticker)
      }

      return [...currentSelection, ticker]
    })
  }

  async function handleRefresh() {
    setSyncing(true)
    setError(null)
    try {
      const refreshed = await refreshPrices()
      setPrices(refreshed)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 border-b border-white/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <p className="text-sm uppercase tracking-[0.3em] text-amber-200/80">Price dashboard</p>
          <h1 className="text-4xl font-semibold sm:text-5xl">Current prices, overlays, and volatility</h1>
          <p className="max-w-3xl text-base leading-8 text-slate-300">
            The page focuses on current futures prices while the backend serves persisted technical indicators and
            historical volatility for the chart and risk view.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={syncing}
          className="inline-flex items-center justify-center rounded-full border border-amber-300/30 bg-amber-300/10 px-4 py-2 text-sm text-amber-100 transition hover:bg-amber-300/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {syncing ? 'Syncing...' : 'Sync now'}
        </button>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur">
          <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-4">
            <div>
              <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Latest prices</p>
              <p className="mt-2 text-lg font-semibold text-white">Tracked futures with day-over-day direction</p>
            </div>
            <p className="text-xs text-slate-400">Live from the backend</p>
          </div>

          {loadingPrices ? (
            <p className="mt-5 text-sm leading-6 text-slate-300">Loading latest prices...</p>
          ) : prices.length === 0 ? (
            <p className="mt-5 text-sm leading-6 text-slate-300">No prices are available yet. Use Sync now to fetch them.</p>
          ) : (
            <div className="mt-5 grid gap-3">
              {prices.map((price) => {
                const delta = formatChange(price)

                return (
                  <article key={price.ticker} className="rounded-2xl border border-white/10 bg-slate-950/55 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm text-slate-400">{getDisplayName(price)}</p>
                        <p className="mt-1 text-xs text-slate-500">{price.ticker}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-semibold text-amber-200">${price.price_usd.toFixed(2)}</p>
                        {delta.label ? (
                          <span className={`mt-2 inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${delta.tone}`}>
                            {delta.label}
                          </span>
                        ) : null}
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
                      <span>Price date: {price.price_date}</span>
                      {price.previous_price_usd !== null && price.previous_price_usd !== undefined && (
                        <span>Yesterday: ${price.previous_price_usd.toFixed(2)}</span>
                      )}
                    </div>
                  </article>
                )
              })}
            </div>
          )}
        </section>

        <section className="space-y-4">
          {!loadingHistory && history.length > 0 && (
            <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4 shadow-xl shadow-black/10 backdrop-blur">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Plot filters</p>
                  <p className="mt-2 text-sm text-slate-300">Choose which tickers appear in the line charts.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedTickers(history.map((item) => item.ticker))}
                  className="rounded-full border border-white/10 bg-slate-950/55 px-3 py-1.5 text-xs text-slate-200 transition hover:border-amber-300/30 hover:bg-amber-300/10"
                >
                  Show all
                </button>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {history.map((item) => {
                  const selected = selectedTickers.includes(item.ticker)
                  return (
                    <button
                      key={item.ticker}
                      type="button"
                      onClick={() => toggleTicker(item.ticker)}
                      className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs transition ${
                        selected
                          ? 'border-amber-300/40 bg-amber-300/15 text-amber-100'
                          : 'border-white/10 bg-slate-950/55 text-slate-400 hover:border-white/20 hover:text-slate-200'
                      }`}
                    >
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: getTickerColor(item.ticker), opacity: selected ? 1 : 0.35 }}
                      />
                      <span>{getSeriesDisplayName(item)}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {loadingHistory ? (
            <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-6 text-sm text-slate-300">
              Loading the 30-day chart...
            </div>
          ) : visibleHistory.length === 0 ? (
            <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-6 text-sm text-slate-300">
              Select at least one ticker to plot its line charts.
            </div>
          ) : (
            <div className="space-y-4">
              <PriceHistoryChart series={visibleHistory} />
              <VolatilityChart series={visibleHistory} />
            </div>
          )}
        </section>
      </div>
    </section>
  )
}
