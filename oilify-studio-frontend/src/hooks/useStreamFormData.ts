import { useState, useEffect, useCallback } from 'react'
import { apiFetch } from '../lib/api'

export const useStreamFormData = () => {
  const [datasets, setDatasets] = useState<string[]>([])
  const [availableMetrics, setAvailableMetrics] = useState<string[]>([])
  const [startDate, setStartDate] = useState<Date | null>(null)
  const [endDate, setEndDate] = useState<Date | null>(null)
  const [selectedTimestamp, setSelectedTimestamp] = useState<Date | null>(null)
  const [fetchingDatasets, setFetchingDatasets] = useState(true)
  const [fetchingMetrics, setFetchingMetrics] = useState(true)
  const [fetchingTimestampRange, setFetchingTimestampRange] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchDatasets() {
      try {
        const response = await apiFetch('/api/v1/dataset/get_dataset')
        const data = await response.json()
        setDatasets(data)
      } catch (err) {
        console.error('Failed to fetch datasets:', err)
        setError('Failed to load datasets')
      } finally {
        setFetchingDatasets(false)
      }
    }
    fetchDatasets()
  }, [])

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const response = await apiFetch('/api/v1/metric/get_metric')
        const data = await response.json()
        setAvailableMetrics(data)
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
        setError('Failed to load metrics')
      } finally {
        setFetchingMetrics(false)
      }
    }
    fetchMetrics()
  }, [])

  const fetchTimestampRange = useCallback(async (dataset: string) => {
    setFetchingTimestampRange(true)
    try {
      const response = await apiFetch(`/api/v1/dataset/${dataset}/get_timestamp_range`)
      const data = await response.json()
      const start = new Date(data.start_timestamp)
      const end = new Date(data.end_timestamp)
      setStartDate(start)
      setEndDate(end)
      setSelectedTimestamp(start) // Default to start date
    } catch (err) {
      console.error('Failed to fetch timestamp range:', err)
      setError('Failed to load timestamp range')
    } finally {
      setFetchingTimestampRange(false)
    }
  }, [])

  const resetTimestampData = useCallback(() => {
    setStartDate(null)
    setEndDate(null)
    setSelectedTimestamp(null)
  }, [])

  return {
    datasets,
    availableMetrics,
    startDate,
    endDate,
    selectedTimestamp,
    setSelectedTimestamp,
    fetchingDatasets,
    fetchingMetrics,
    fetchingTimestampRange,
    error,
    setError,
    fetchTimestampRange,
    resetTimestampData,
  }
}