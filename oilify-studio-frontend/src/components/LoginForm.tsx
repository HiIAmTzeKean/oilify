import React, { useState } from 'react'
import { buildUrl } from '../lib/api'

type Props = {
  onSubmit: (username: string, password: string) => Promise<void> | void
}

export const LoginForm: React.FC<Props> = ({ onSubmit }) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!username.trim() || !password) {
      setError('Please enter both username and password')
      return
    }
    setLoading(true)
    try {
      await onSubmit(username.trim(), password)
    } catch (err: any) {
      setError(err?.message ?? String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="w-full max-w-sm" onSubmit={handleSubmit}>
      <div className="space-y-4">
        {error && <div className="text-red-600 bg-red-50 p-2 rounded">{error}</div>}

        <label className="block">
          <span className="text-sm font-medium">Username</span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
            autoComplete="username"
            type="text"
            placeholder="you@example.com"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium">Password</span>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
            autoComplete="current-password"
            type="password"
            placeholder="••••••••"
          />
        </label>

        <div className="flex items-center justify-between">
          <label className="inline-flex items-center gap-2 text-sm">
            <input type="checkbox" className="rounded" />
            <span>Remember me</span>
          </label>
        </div>

        <div>
          <button
            type="submit"
            className="w-full inline-flex justify-center items-center rounded-md bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 font-medium disabled:opacity-60 mb-4"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </div>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-slate-50 dark:bg-slate-900 text-slate-500">Or</span>
          </div>
        </div>

        <div>
          <button
            type="button"
            onClick={() => window.location.href = buildUrl('/api/v1/auth/google')}
            className="w-full inline-flex justify-center items-center rounded-md bg-white hover:bg-gray-50 text-gray-900 border border-gray-300 px-4 py-2 font-medium"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
          </button>
        </div>
      </div>
    </form>
  )
}

export default LoginForm
