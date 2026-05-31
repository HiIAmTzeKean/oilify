import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useEvaluationResults } from '../hooks/useEvaluationResults'
import { useExpandedSections } from '../hooks/useExpandedSections'
import ResultsSection from '../components/ResultsSection'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorDisplay from '../components/ErrorDisplay'
import EmptyState from '../components/EmptyState'

const EvaluationResults: React.FC = () => {
  const { streamJobId } = useParams<{ streamJobId: string }>()
  const navigate = useNavigate()
  const { results, loading, error } = useEvaluationResults(streamJobId)
  const { expandedSections, toggleSection } = useExpandedSections()

  if (loading) {
    return <LoadingSpinner size="large" />
  }

  if (error) {
    return <ErrorDisplay error={error} />
  }

  const hasResults = results.macro.length > 0 || results.micro.length > 0 ||
                    results.window.length > 0 || results.user.length > 0

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Evaluation Results
        </h1>
        <button
          onClick={() => navigate('/evaluation')}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
        >
          Back to Evaluation
        </button>
      </div>

      {!hasResults ? (
        <EmptyState message="No evaluation results found for this stream job." />
      ) : (
        <div className="space-y-6">
          {[
            { type: 'macro' as const, data: results.macro },
            { type: 'micro' as const, data: results.micro },
            { type: 'window' as const, data: results.window },
            { type: 'user' as const, data: results.user }
          ].map(({ type, data }) => {
            if (data.length === 0) return null

            return (
              <ResultsSection
                key={type}
                type={type}
                data={data}
                expanded={expandedSections[type]}
                onToggle={() => toggleSection(type)}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

export default EvaluationResults