import React from 'react'
import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <section className="space-y-10">
      <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
        <div className="space-y-5">
          <p className="text-sm uppercase tracking-[0.3em] text-amber-200/80">Oilify</p>
          <h1 className="max-w-4xl text-4xl font-semibold leading-tight sm:text-5xl lg:text-6xl">
            Live prices and a 30-day trend view in one modular dashboard.
          </h1>
          <p className="max-w-3xl text-base leading-8 text-slate-300">
            The dashboard page shows the latest tracked prices, plus a chart of the last 30 trading days fetched
            from the backend API.
          </p>
        </div>

        <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/20 backdrop-blur">
          <p className="text-sm uppercase tracking-[0.25em] text-slate-400">Quick start</p>
          <div className="mt-5 space-y-4">
            <Link
              to="/prices"
              className="flex items-center justify-between rounded-2xl border border-amber-300/30 bg-amber-300/10 px-5 py-4 text-sm text-amber-100 transition hover:bg-amber-300/20"
            >
              Open price dashboard
              <span aria-hidden="true">→</span>
            </Link>
            <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-5 text-sm leading-7 text-slate-300">
              The dashboard is split into a standalone page so the homepage stays lightweight and future views can be
              added without changing the data layer.
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-white">Latest prices</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            The backend exposes the current benchmark prices so the page can show the latest data immediately.
          </p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-white">30-day chart</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            Historical prices are grouped by symbol and rendered as a compact line chart.
          </p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-white">Modular pages</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            The app now has separate routes so the price view can evolve independently from the landing page.
          </p>
        </article>
      </div>
    </section>
  )
}
