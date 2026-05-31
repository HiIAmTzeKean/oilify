import React from 'react'
import { StreamJob } from '../types/algoTypes'
import LoadingSpinner from './LoadingSpinner'
import EmptyState from './EmptyState'

interface StreamJobSelectorProps {
  streamJobs: StreamJob[]
  loading: boolean
  selectedStreamJob: number | null
  onSelect: (id: number) => void
}

const StreamJobSelector: React.FC<StreamJobSelectorProps> = ({
  streamJobs,
  loading,
  selectedStreamJob,
  onSelect
}) => (
  <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-md shadow">
    <h2 className="text-xl font-semibold mb-4">Select Stream Job</h2>
    {loading ? (
      <LoadingSpinner message="Loading stream jobs..." />
    ) : streamJobs.length === 0 ? (
      <EmptyState message="No stream jobs available. Create a stream first." />
    ) : (
      <div className="space-y-2">
        {streamJobs.map(job => (
          <div
            key={job.id}
            className={`p-3 border rounded cursor-pointer ${
              selectedStreamJob === job.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
            onClick={() => onSelect(job.id)}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-medium">{job.name}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">{job.description}</p>
                <p className="text-xs text-slate-500">Dataset: {job.dataset}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`px-2 py-1 text-xs rounded ${
                    job.status === 'created'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                      : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  }`}>
                    {job.status}
                  </span>
                  <span className="text-xs text-slate-500">
                    {job.algorithms.length} algorithm{job.algorithms.length !== 1 ? 's' : ''} added
                  </span>
                </div>
              </div>
            </div>
            {job.algorithms.length > 0 && (
              <div className="mt-2">
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Added Algorithms:</p>
                <div className="flex flex-wrap gap-1">
                  {job.algorithms.map(algo => (
                    <span key={algo.name} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded">
                      {algo.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    )}
  </div>
)

export default StreamJobSelector