import React from 'react'

import PriceHistoryChart from '../components/PriceHistoryChart'
import {
  getLatestPrices,
  getPriceHistory,
  refreshPrices,
  type Price,
  type PriceHistorySeries,
} from '../lib/api'

const HISTORY_DAYS = 30

export default function Prices() {
  const [prices, setPrices] = React.useState<Price[]>([])
  const [history, setHistory] = React.useState<PriceHistorySeries[]>([])
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
          <h1 className="text-4xl font-semibold sm:text-5xl">Latest prices and 30-day history</h1>
          <p className="max-w-3xl text-base leading-8 text-slate-300">
            The page shows the current tracked prices, plus a line chart of the last 30 days fetched through the
            backend API.
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
              <p className="mt-2 text-lg font-semibold text-white">Tracked market instruments</p>
            </div>
            <p className="text-xs text-slate-400">Live from the backend</p>
          </div>

          {loadingPrices ? (
            <p className="mt-5 text-sm leading-6 text-slate-300">Loading latest prices...</p>
          ) : prices.length === 0 ? (
            <p className="mt-5 text-sm leading-6 text-slate-300">No prices are available yet. Use Sync now to fetch them.</p>
          ) : (
            <div className="mt-5 grid gap-3">
              {prices.map((price) => (
                <article key={price.symbol} className="rounded-2xl border border-white/10 bg-slate-950/55 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm text-slate-400">{price.symbol}</p>
                      <p className="mt-1 text-xs text-slate-500">{price.ticker}</p>
                    </div>
                    <p className="text-2xl font-semibold text-amber-200">${price.price_usd.toFixed(2)}</p>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
                    <span>Date: {price.price_date}</span>
                    <span>Fetched: {new Date(price.fetched_at).toLocaleString()}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="space-y-4">
          {loadingHistory ? (
            <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/55 p-6 text-sm text-slate-300">
              Loading the 30-day chart...
            </div>
          ) : (
            <PriceHistoryChart series={history} />
          )}

          <div className="grid gap-4 sm:grid-cols-3">
            <article className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <h2 className="text-lg font-semibold text-white">WTI</h2>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                West Texas Intermediate is shown as one tracked benchmark in the dashboard.
              </p>
            </article>
            <article className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <h2 className="text-lg font-semibold text-white">Brent</h2>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                Brent crude provides the comparison series in the chart.
              </p>
            </article>
            <article className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <h2 className="text-lg font-semibold text-white">30 days</h2>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                The chart request asks the backend for the latest 30 trading days by default.
              </p>
            </article>
          </div>
        </section>
      </div>
    </section>
  )
}
