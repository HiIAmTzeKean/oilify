import { useState, useEffect } from 'react'
import { apiFetch } from '../lib/api'
import { EvaluationResultsData } from '../types/evaluationResultsTypes'

export const useEvaluationResults = (streamJobId: string | undefined) => {
  const [results, setResults] = useState<EvaluationResultsData>({
    macro: [],
    micro: [],
    window: [],
    user: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchResults = async () => {
      if (!streamJobId) return

      try {
        setLoading(true)
        const response = await apiFetch(`/api/v1/evaluator/${streamJobId}/results`)
        if (!response.ok) {
          throw new Error('Failed to fetch evaluation results')
        }
        const data: EvaluationResultsData = await response.json()
        setResults(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [streamJobId])

  return { results, loading, error }
}