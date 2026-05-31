import React from 'react'
import { SelectedAlgorithm } from '../types/algoTypes'

interface AlgorithmParametersProps {
  selectedAlgorithms: SelectedAlgorithm[]
  onParamChange: (index: number, key: string, value: any) => void
  onRemove: (index: number) => void
}

const AlgorithmParameters: React.FC<AlgorithmParametersProps> = ({
  selectedAlgorithms,
  onParamChange,
  onRemove
}) => (
  <div className="mt-8 p-6 bg-green-50 dark:bg-green-900/20 rounded-md shadow">
    <h2 className="text-xl font-semibold mb-4">Configure Algorithm Parameters</h2>
    <div className="space-y-4">
      {selectedAlgorithms.map((selectedAlgo, index) => (
        <div key={selectedAlgo.clientKey} className="p-4 bg-white dark:bg-slate-800 rounded border relative">
          <button
            type="button"
            onClick={() => onRemove(index)}
            className="absolute top-2 right-2 text-slate-400 hover:text-red-500 dark:text-slate-500 dark:hover:text-red-400"
            aria-label={`Remove ${selectedAlgo.name}`}
          >
            &#x2715;
          </button>
          <h3 className="font-medium mb-2">{selectedAlgo.name}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(selectedAlgo.params).map(([key, value]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  {key}
                </label>
                <input
                  type={typeof value === 'number' ? 'number' : 'text'}
                  value={value}
                  onChange={(e) => {
                    const newValue = typeof value === 'number' ? parseFloat(e.target.value) : e.target.value
                    onParamChange(index, key, newValue)
                  }}
                  className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
)

export default AlgorithmParameters