import React from 'react'
import { StreamJob, SelectedAlgorithm } from '../types/algoTypes'

interface StreamDetailsProps {
  selectedStream: StreamJob | undefined
  selectedAlgorithms: SelectedAlgorithm[]
}

const StreamDetails: React.FC<StreamDetailsProps> = ({
  selectedStream,
  selectedAlgorithms
}) => {
  if (!selectedStream) return null

  return (
    <div className="mt-8 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-md shadow">
      <h2 className="text-xl font-semibold mb-4">Selected Stream Details</h2>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <h3 className="font-medium">Stream: {selectedStream.name}</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">{selectedStream.description}</p>
          <p className="text-sm">Dataset: {selectedStream.dataset}</p>
          <p className="text-sm">Top K: {selectedStream.top_k}</p>
          <p className="text-sm">Window Size: {selectedStream.window_size}</p>
        </div>
        <div>
          <p className="text-sm font-medium">Metrics:</p>
          <div className="flex flex-wrap gap-1 mt-1">
            {selectedStream.metrics.map(metric => (
              <span key={metric} className="px-2 py-1 bg-slate-200 dark:bg-slate-700 text-xs rounded">
                {metric}
              </span>
            ))}
          </div>
          <p className="text-sm font-medium mt-3">Selected Algorithms ({selectedAlgorithms.length}):</p>
          <div className="flex flex-wrap gap-1 mt-1">
            {selectedAlgorithms.length > 0 ? (
              selectedAlgorithms.map(algo => (
                <span key={algo.name} className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded">
                  {algo.name}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500">No algorithms selected</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default StreamDetails