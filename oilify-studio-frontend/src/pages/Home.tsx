import React from 'react'

export default function Home() {
  return (
    <section className="space-y-8">
      <div className="space-y-4">
        <p className="text-sm uppercase tracking-[0.3em] text-amber-200/80">Oilify</p>
        <h1 className="text-4xl font-semibold sm:text-5xl">Fresh frontend, zero legacy dashboard wiring.</h1>
        <p className="max-w-3xl text-base leading-8 text-slate-300">
          This landing page replaces the old RecNextEval marketing copy with a simple starting point for Oilify.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-white">Backend-first</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            The new backend exposes a small API surface so future work can start from a controlled baseline.
          </p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-white">Brand reset</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            Oilify replaces the old project identity across the visible UI and repository metadata.
          </p>
        </article>
        <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <h2 className="text-lg font-semibold text-white">Less coupling</h2>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            The frontend no longer depends on the old auth flow or recommendation-evaluation routes.
          </p>
        </article>
      </div>
    </section>
  )
}
