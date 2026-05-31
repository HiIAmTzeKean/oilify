import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import { useStreamFormData } from './useStreamFormData'
import { convertToSeconds } from '../lib/timeUtils'
import { CreateStreamFormData, CreateStreamState } from '../types/createStreamTypes'

export const useCreateStreamForm = () => {
  const navigate = useNavigate()

  const initialFormData: CreateStreamFormData = {
    name: '',
    description: '',
    dataset: '',
    topK: '',
    selectedMetrics: [],
    timestampSplitStart: '',
    windowSizeValue: '',
    windowSizeUnit: 'seconds'
  }

  const [state, setState] = useState<CreateStreamState>({
    formData: initialFormData,
    loading: false,
    streamCreated: false,
    createdStreamId: null,
    error: null
  })

  const {
    datasets,
    availableMetrics,
    startDate,
    endDate,
    selectedTimestamp,
    setSelectedTimestamp,
    fetchingDatasets,
    fetchingMetrics,
    fetchingTimestampRange,
    error: streamFormError,
    setError: setStreamFormError,
    fetchTimestampRange,
    resetTimestampData,
  } = useStreamFormData()

  useEffect(() => {
    if (selectedTimestamp) {
      setState(prev => ({
        ...prev,
        formData: {
          ...prev.formData,
          timestampSplitStart: selectedTimestamp.toISOString().split('T')[0]
        }
      }))
    } else {
      setState(prev => ({
        ...prev,
        formData: {
          ...prev.formData,
          timestampSplitStart: ''
        }
      }))
    }
  }, [selectedTimestamp])

  useEffect(() => {
    if (state.formData.dataset) {
      fetchTimestampRange(state.formData.dataset)
    } else {
      resetTimestampData()
    }
  }, [state.formData.dataset, fetchTimestampRange, resetTimestampData])

  const updateFormData = (updates: Partial<CreateStreamFormData>) => {
    setState(prev => ({
      ...prev,
      formData: { ...prev.formData, ...updates }
    }))
  }

  const handleMetricChange = (metric: string) => {
    if (metric && !state.formData.selectedMetrics.includes(metric)) {
      updateFormData({
        selectedMetrics: [...state.formData.selectedMetrics, metric]
      })
    }
  }

  const removeMetric = (metric: string) => {
    updateFormData({
      selectedMetrics: state.formData.selectedMetrics.filter(m => m !== metric)
    })
  }

  const validateForm = (): boolean => {
    const { name, dataset, topK, selectedMetrics, windowSizeValue } = state.formData

    if (!name || !dataset || !topK || selectedMetrics.length === 0 || !selectedTimestamp || !windowSizeValue) {
      setState(prev => ({ ...prev, error: 'Please fill in all required fields' }))
      return false
    }

    return true
  }

  const submitForm = async () => {
    if (!validateForm()) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const response = await apiFetch('/api/v1/stream/create_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: state.formData.name,
          description: state.formData.description,
          dataset: state.formData.dataset,
          top_k: parseInt(state.formData.topK),
          metrics: state.formData.selectedMetrics,
          timestamp_split_start: state.formData.timestampSplitStart,
          window_size: convertToSeconds(state.formData.windowSizeValue, state.formData.windowSizeUnit)
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        const detail = errorData?.detail ?? 'Failed to create stream'
        throw new Error(detail)
      }

      const result = await response.json()
      toast.success(`Stream created successfully! Stream ID: ${result.stream_job_id}`)

      setState(prev => ({
        ...prev,
        loading: false,
        streamCreated: true,
        createdStreamId: result.stream_job_id
      }))
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: err?.message ?? String(err)
      }))
    }
  }

  const resetForm = () => {
    setState({
      formData: initialFormData,
      loading: false,
      streamCreated: false,
      createdStreamId: null,
      error: null
    })
    resetTimestampData()
  }

  const goToAlgo = () => {
    navigate('/algo')
  }

  return {
    // State
    ...state,
    datasets,
    availableMetrics,
    startDate,
    endDate,
    selectedTimestamp,
    fetchingDatasets,
    fetchingMetrics,
    fetchingTimestampRange,
    streamFormError,

    // Actions
    updateFormData,
    handleMetricChange,
    removeMetric,
    submitForm,
    resetForm,
    goToAlgo,
    setSelectedTimestamp
  }
}