import React from 'react'
import { EvaluationResult, ResultType } from '../types/evaluationResultsTypes'
import ResultsTable from './ResultsTable'

interface ResultsSectionProps {
  type: ResultType
  data: EvaluationResult[]
  expanded: boolean
  onToggle: () => void
}

const ResultsSection: React.FC<ResultsSectionProps> = ({ type, data, expanded, onToggle }) => {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md border border-gray-200 dark:border-slate-700">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 dark:hover:bg-slate-700 rounded-lg transition-colors duration-200"
      >
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white capitalize">
          {type} Results ({data.length})
        </h2>
        <svg
          className={`w-5 h-5 text-gray-500 dark:text-gray-400 transform transition-transform duration-200 ${
            expanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-6 pb-6">
          <ResultsTable results={data} type={type} />
        </div>
      )}
    </div>
  )
}

export default ResultsSection