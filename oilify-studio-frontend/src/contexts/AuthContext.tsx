import React, { createContext, useContext, useEffect, useState } from 'react'
import { apiFetch } from '../lib/api'

type AuthContextType = {
  username: string | null
  setUsername: (u: string | null) => void
  userId: number | null
  setUserId: (id: number | null) => void
  loading: boolean
  logout: () => void
  login: (username: string, password: string) => Promise<void>
  handleOAuthCallback: (token: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [username, setUsername] = useState<string | null>(null)
  const [userId, setUserId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // On mount, try to fetch current user if token present
    const token = typeof window !== 'undefined' ? localStorage.getItem('recnexteval_access_token') : null
    if (!token) {
      setLoading(false)
      return
    }

    let cancelled = false

    ;(async () => {
      try {
        const res = await apiFetch('/api/v1/auth/me')
        const data = await res.json()
        if (!cancelled) {
          setUsername(data.username ?? null)
          setUserId(Number(data.user_id))
        }
      } catch (err) {
        // token may be invalid; clear stored token
        localStorage.removeItem('recnexteval_access_token')
        if (!cancelled) {
          setUsername(null)
          setUserId(null)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  const logout = () => {
    localStorage.removeItem('recnexteval_access_token')
    setUsername(null)
    setUserId(null)
  }

  const login = async (username: string, password: string) => {
    const body = new URLSearchParams()
    body.append('username', username)
    body.append('password', password)

    const res = await apiFetch('/api/v1/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    })

    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `Login failed: ${res.status}`)
    }

    const data = await res.json()
    const token = data?.access_token
    if (!token) throw new Error('No token returned from server')

    localStorage.setItem('recnexteval_access_token', token)

    const meRes = await apiFetch('/api/v1/auth/me')
    const meData = await meRes.json()
    setUsername(meData.username ?? username)
    setUserId(Number(meData.user_id))
  }

  const handleOAuthCallback = async (token: string) => {
    localStorage.setItem('recnexteval_access_token', token)
    const meRes = await apiFetch('/api/v1/auth/me')
    const meData = await meRes.json()
    setUsername(meData.username ?? 'User')
    setUserId(Number(meData.user_id))
  }

  return (
    <AuthContext.Provider value={{ username, setUsername, userId, setUserId, loading, logout, login, handleOAuthCallback }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export default AuthContext
