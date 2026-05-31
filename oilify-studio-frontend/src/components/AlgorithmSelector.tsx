import React from 'react'
import { Algorithm, SelectedAlgorithm } from '../types/algoTypes'
import LoadingSpinner from './LoadingSpinner'

interface AlgorithmSelectorProps {
  algorithms: Algorithm[]
  loading: boolean
  selectedAlgorithms: SelectedAlgorithm[]
  onToggle: (algorithmId: string) => void
}

const AlgorithmSelector: React.FC<AlgorithmSelectorProps> = ({
  algorithms,
  loading,
  selectedAlgorithms,
  onToggle
}) => (
  <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-md shadow">
    <h2 className="text-xl font-semibold mb-4">Configure Algorithms</h2>
    {loading ? (
      <LoadingSpinner message="Loading algorithms..." />
    ) : (
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {algorithms.map(algo => (
          <div
            key={algo.name}
            className={`p-2 rounded cursor-pointer ${
              selectedAlgorithms.some(selected => selected.name === algo.name)
                ? 'bg-blue-100 dark:bg-blue-900 border border-blue-300 dark:border-blue-600'
                : 'hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
            onClick={() => onToggle(algo.name)}
          >
            <div>
              <h3 className="font-medium">{algo.name}</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">{algo.description}</p>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
)

export default AlgorithmSelector