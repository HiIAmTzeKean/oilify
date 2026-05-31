import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { StreamJob } from '../types/evaluationTypes'

interface EvaluationJobItemProps {
  job: StreamJob
  running: boolean
  onRun: (job: StreamJob) => void
  onDelete: (jobId: number) => void
}

const EvaluationJobItem: React.FC<EvaluationJobItemProps> = ({ job, running, onRun, onDelete }) => {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'created': return 'bg-gray-100 text-gray-800'
      case 'ready': return 'bg-blue-100 text-blue-800'
      case 'running': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Not set'
    return new Date(dateString).toLocaleString()
  }

  const formatParameters = (params: string | null) => {
    if (!params) return 'None'
    try {
      const parsed = JSON.parse(params)
      return JSON.stringify(parsed, null, 2)
    } catch {
      return params
    }
  }

  const toggleExpanded = () => {
    setExpanded(!expanded)
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-slate-700">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{job.name}</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-1">{job.description}</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
            {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
          </span>
          {job.status === 'completed' && (
            <button
              onClick={() => navigate(`/evaluation-results/${job.id}`)}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors"
              title="View evaluation results"
            >
              View Results
            </button>
          )}
          {!job.completed_at ? (
            <button
              onClick={() => onRun(job)}
              disabled={running}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors disabled:opacity-50"
            >
              {running ? 'Starting...' : 'Run Job'}
            </button>
          ) : (
            <button
              onClick={() => onRun(job)}
              disabled={running}
              className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-md transition-colors disabled:opacity-50"
            >
              {running ? 'Rerunning...' : 'Rerun Job'}
            </button>
          )}
          <button
            onClick={() => onDelete(job.id)}
            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded-md transition-colors"
            title="Delete stream job"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
        <div>
          <span className="font-medium text-gray-700 dark:text-gray-300">Dataset:</span>
          <span className="ml-2 text-gray-900 dark:text-white">{job.dataset}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700 dark:text-gray-300">Top K:</span>
          <span className="ml-2 text-gray-900 dark:text-white">{job.top_k}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700 dark:text-gray-300">Window Size:</span>
          <span className="ml-2 text-gray-900 dark:text-white">{job.window_size}</span>
        </div>
        <div className="md:col-span-2 lg:col-span-3">
          <span className="font-medium text-gray-700 dark:text-gray-300">Metrics:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {job.metrics.map((metric) => (
              <span key={metric} className="px-2 py-1 bg-gray-100 dark:bg-slate-700 text-gray-800 dark:text-gray-200 text-xs rounded">
                {metric}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 dark:border-slate-600 pt-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700 dark:text-gray-300">Created:</span>
            <div className="text-gray-900 dark:text-white">{formatDate(job.created_at)}</div>
          </div>
          <div>
            <span className="font-medium text-gray-700 dark:text-gray-300">Started:</span>
            <div className="text-gray-900 dark:text-white">{formatDate(job.started_at)}</div>
          </div>
          <div>
            <span className="font-medium text-gray-700 dark:text-gray-300">Completed:</span>
            <div className="text-gray-900 dark:text-white">{formatDate(job.completed_at)}</div>
          </div>
        </div>
        {job.status === 'failed' && job.error_message && (
          <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-sm">
            <span className="font-medium text-red-700 dark:text-red-400">Error:</span>
            <p className="mt-1 text-red-600 dark:text-red-300 font-mono break-all">{job.error_message}</p>
          </div>
        )}
      </div>

      {job.algorithms.length > 0 && (
        <div className="border-t border-gray-200 dark:border-slate-600 pt-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-medium text-gray-700 dark:text-gray-300">Algorithms:</h3>
            <button
              onClick={toggleExpanded}
              className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm rounded hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              {expanded ? 'Hide Details' : 'Show Details'}
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {job.algorithms.map((algo, index) => (
              <span key={index} className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded-md">
                {algo.name}
              </span>
            ))}
          </div>
          {expanded && (
            <div className="mt-4 space-y-2">
              {job.algorithms.map((algo, index) => (
                <div key={index} className="bg-gray-50 dark:bg-slate-700 p-3 rounded-md">
                  <h4 className="font-semibold text-gray-900 dark:text-white">{algo.name}</h4>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">{algo.description}</p>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">Parameters: {formatParameters(algo.params)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EvaluationJobItem