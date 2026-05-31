import React from 'react'

interface TimestampRangeSelectorProps {
  startDate: Date | null
  endDate: Date | null
  selectedTimestamp: Date | null
  onTimestampChange: (date: Date) => void
  loading?: boolean
}

const TimestampRangeSelector: React.FC<TimestampRangeSelectorProps> = ({
  startDate,
  endDate,
  selectedTimestamp,
  onTimestampChange,
  loading = false
}) => {
  return (
    <label className="block">
      <span className="text-sm font-medium">
        Timestamp Split Start <span className="text-red-500">*</span>
      </span>
      {loading ? (
        <div className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 p-2 flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-slate-500 mr-2"></div>
          Loading timestamp range...
        </div>
      ) : startDate && endDate && selectedTimestamp ? (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>{startDate.toLocaleDateString()}</span>
            <span>{endDate.toLocaleDateString()}</span>
          </div>
          <input
            type="range"
            min={startDate.getTime()}
            max={endDate.getTime()}
            value={selectedTimestamp.getTime()}
            onChange={(e) => onTimestampChange(new Date(parseInt(e.target.value)))}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700"
          />
          <div className="text-center mt-2 text-sm font-medium">
            Selected: {selectedTimestamp.toLocaleDateString()}
          </div>
        </div>
      ) : (
        <div className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 p-2">
          Select a dataset first
        </div>
      )}
    </label>
  )
}

export default TimestampRangeSelector