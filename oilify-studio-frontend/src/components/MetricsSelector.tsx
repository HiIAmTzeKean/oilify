import React from 'react'

interface MetricsSelectorProps {
  availableMetrics: string[]
  selectedMetrics: string[]
  onMetricAdd: (metric: string) => void
  onMetricRemove: (metric: string) => void
  loading?: boolean
}

const MetricsSelector: React.FC<MetricsSelectorProps> = ({
  availableMetrics,
  selectedMetrics,
  onMetricAdd,
  onMetricRemove,
  loading = false
}) => (
  <label className="block">
    <span className="text-sm font-medium">
      Metrics <span className="text-red-500">*</span>
    </span>
    <select
      value=""
      onChange={(e) => e.target.value && onMetricAdd(e.target.value)}
      className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
      disabled={loading}
    >
      <option value="">
        {loading ? 'Loading metrics...' : 'Select metrics'}
      </option>
      {availableMetrics.map(metric => (
        <option
          key={metric}
          value={metric}
          disabled={selectedMetrics.includes(metric)}
        >
          {metric}
        </option>
      ))}
    </select>
    {selectedMetrics.length > 0 && (
      <div className="mt-2 flex flex-wrap gap-2">
        {selectedMetrics.map(metric => (
          <span key={metric} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
            {metric}
            <button
              type="button"
              onClick={() => onMetricRemove(metric)}
              className="ml-1 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200"
            >
              ×
            </button>
          </span>
        ))}
      </div>
    )}
  </label>
)

export default MetricsSelector