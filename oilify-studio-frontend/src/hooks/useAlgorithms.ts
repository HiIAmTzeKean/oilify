import { useState, useEffect } from 'react'
import { apiFetch } from '../lib/api'
import { Algorithm } from '../types/algoTypes'

export const useAlgorithms = () => {
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchAlgorithms() {
      try {
        const response = await apiFetch('/api/v1/algorithm/list')
        const data = await response.json()
        setAlgorithms(data)
      } catch (err) {
        console.error('Failed to fetch algorithms:', err)
        setError('Failed to load algorithms')
      } finally {
        setLoading(false)
      }
    }
    fetchAlgorithms()
  }, [])

  return { algorithms, loading, error }
}