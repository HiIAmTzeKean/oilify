import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { apiFetch } from '../lib/api'
import { StreamJob } from '../types/evaluationTypes'

export const useEvaluationJobs = () => {
  const [streamJobs, setStreamJobs] = useState<StreamJob[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const fetchStreamJobs = async () => {
    try {
      const response = await apiFetch('/api/v1/stream/list_all')
      const data = await response.json()
      setStreamJobs(data)
    } catch (error) {
      console.error('Failed to fetch stream jobs:', error)
      toast.error('Failed to load stream jobs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStreamJobs()
  }, [])

  useEffect(() => {
    const hasRunning = streamJobs.some(j => j.status === 'running')
    if (!hasRunning) return
    const id = setInterval(fetchStreamJobs, 3000)
    return () => clearInterval(id)
  }, [streamJobs])

  const runJob = async (job: StreamJob) => {
    setRunning(true)
    try {
      const endpoint = job.completed_at ? 'rerun' : 'run'
      const response = await apiFetch(`/api/v1/evaluator/${job.id}/${endpoint}`, {
        method: 'POST'
      })
      if (response.ok) {
        toast.success(`Job ${endpoint === 'rerun' ? 'rerun' : 'started'} successfully`)
        fetchStreamJobs() // Refresh the list
      } else {
        const error = await response.json()
        toast.error(error.detail || `Failed to ${endpoint} job`)
      }
    } catch (error) {
      console.error('Failed to run job:', error)
      toast.error('Failed to start job')
    } finally {
      setRunning(false)
    }
  }

  const deleteJob = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this stream job?')) {
      return
    }
    
    try {
      const response = await apiFetch(`/api/v1/stream/${jobId}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        toast.success('Stream job deleted successfully')
        fetchStreamJobs() // Refresh the list
      } else {
        toast.error('Failed to delete stream job')
      }
    } catch (error) {
      console.error('Failed to delete job:', error)
      toast.error('Failed to delete stream job')
    }
  }

  return { streamJobs, loading, running, runJob, deleteJob, refreshJobs: fetchStreamJobs }
}