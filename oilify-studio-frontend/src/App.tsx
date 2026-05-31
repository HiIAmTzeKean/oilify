import React from 'react'
import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import OilPrices from './pages/OilPrices'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.18),_transparent_34%),linear-gradient(180deg,_#07111f_0%,_#0b1728_45%,_#111827_100%)] text-slate-50">
        <header className="border-b border-white/10 bg-slate-950/30 backdrop-blur">
          <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-6 px-6 py-4 sm:px-10 lg:px-12">
            <Link to="/" className="text-sm uppercase tracking-[0.35em] text-amber-300/80 transition hover:text-amber-200">
              Oilify
            </Link>
            <nav className="flex items-center gap-2 text-sm text-slate-300">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 transition ${isActive ? 'bg-white/10 text-white' : 'hover:bg-white/5 hover:text-white'}`
                }
              >
                Home
              </NavLink>
              <NavLink
                to="/prices"
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 transition ${isActive ? 'bg-white/10 text-white' : 'hover:bg-white/5 hover:text-white'}`
                }
              >
                Prices
              </NavLink>
            </nav>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl px-6 py-8 sm:px-10 lg:px-12">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/prices" element={<OilPrices />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
