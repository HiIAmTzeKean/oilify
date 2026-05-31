import React from 'react'

import { getLatestOilPrices, refreshOilPrices, type OilPrice } from './lib/api'

export default function App() {
  const [prices, setPrices] = React.useState<OilPrice[]>([])
  const [loading, setLoading] = React.useState(true)
  const [syncing, setSyncing] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const loadLatest = React.useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const latest = await getLatestOilPrices()
      setPrices(latest)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    void loadLatest()
  }, [loadLatest])

  async function handleRefresh() {
    setSyncing(true)
    setError(null)
    try {
      const refreshed = await refreshOilPrices()
      setPrices(refreshed)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.22),_transparent_34%),linear-gradient(180deg,_#07111f_0%,_#0b1728_45%,_#111827_100%)] text-slate-50">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8 sm:px-10 lg:px-12">
        <header className="flex items-center justify-between gap-4 border-b border-white/10 pb-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-amber-300/80">Oilify</p>
            <h1 className="mt-2 text-2xl font-semibold sm:text-3xl">Daily Oil Price Monitor</h1>
          </div>
          <button
            onClick={handleRefresh}
            disabled={syncing}
            className="rounded-full border border-amber-300/30 bg-amber-300/10 px-4 py-2 text-sm text-amber-100 transition hover:bg-amber-300/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {syncing ? 'Syncing...' : 'Sync now'}
          </button>
        </header>

        <section className="grid flex-1 gap-8 py-12 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-8">
            <div className="space-y-5">
              <p className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200/90">
                Prices are fetched from Yahoo Finance and upserted by day into PostgreSQL
              </p>
              <h2 className="max-w-2xl text-5xl font-semibold leading-tight sm:text-6xl">
                WTI and Brent,
                always current.
              </h2>
              <p className="max-w-2xl text-lg leading-8 text-slate-300">
                A scheduled backend job runs three times a day and updates the same daily row when triggered again.
                Use the manual sync button to force an immediate refresh.
              </p>
            </div>

            {error && (
              <div className="rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                {error}
              </div>
            )}
          </div>

          <div className="grid gap-4 rounded-[2rem] border border-white/10 bg-white/6 p-4 shadow-2xl shadow-black/25 backdrop-blur">
            <div className="rounded-[1.5rem] border border-white/10 bg-slate-950/60 p-6">
              <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Latest prices</p>
              {loading ? (
                <p className="mt-3 text-sm leading-6 text-slate-300">Loading latest oil prices...</p>
              ) : prices.length === 0 ? (
                <p className="mt-3 text-sm leading-6 text-slate-300">No oil prices stored yet. Click Sync now.</p>
              ) : (
                <div className="mt-3 grid gap-3">
                  {prices.map((price) => (
                    <article key={price.symbol} className="rounded-xl border border-white/10 bg-white/5 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm text-slate-400">{price.symbol} ({price.ticker})</p>
                        <p className="text-lg font-semibold text-amber-200">${price.price_usd.toFixed(2)}</p>
                      </div>
                      <p className="mt-2 text-xs text-slate-400">Date: {price.price_date}</p>
                      <p className="mt-1 text-xs text-slate-500">Fetched: {new Date(price.fetched_at).toLocaleString()}</p>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        <section id="details" className="grid gap-4 border-t border-white/10 py-8 sm:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h3 className="text-lg font-semibold">Scheduler</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Runs at 00:00, 08:00, and 16:00 UTC by default.
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h3 className="text-lg font-semibold">Storage</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Inserts once per symbol/day, then updates the same row on later runs.
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h3 className="text-lg font-semibold">Source</h3>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Yahoo Finance via Python client integration in the backend service.
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}
