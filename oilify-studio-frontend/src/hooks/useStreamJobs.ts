import { useState, useEffect } from 'react'
import { apiFetch } from '../lib/api'
import { StreamJob } from '../types/algoTypes'

export const useStreamJobs = () => {
  const [streamJobs, setStreamJobs] = useState<StreamJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStreamJobs() {
      try {
        const response = await apiFetch('/api/v1/stream/list_available')
        const data = await response.json()
        setStreamJobs(data)
      } catch (err) {
        console.error('Failed to fetch stream jobs:', err)
        setError('Failed to load stream jobs')
      } finally {
        setLoading(false)
      }
    }
    fetchStreamJobs()
  }, [])

  const refreshStreamJobs = async () => {
    setLoading(true)
    try {
      const response = await apiFetch('/api/v1/stream/list_available')
      const data = await response.json()
      setStreamJobs(data)
    } catch (err) {
      console.error('Failed to refresh stream jobs:', err)
      setError('Failed to refresh stream jobs')
    } finally {
      setLoading(false)
    }
  }

  return { streamJobs, loading, error, refreshStreamJobs }
}