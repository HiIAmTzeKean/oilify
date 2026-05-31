import React from 'react'

interface WindowSizeInputProps {
  value: string
  unit: string
  onValueChange: (value: string) => void
  onUnitChange: (unit: string) => void
  required?: boolean
}

const WindowSizeInput: React.FC<WindowSizeInputProps> = ({
  value,
  unit,
  onValueChange,
  onUnitChange,
  required = false
}) => (
  <label className="block">
    <span className="text-sm font-medium">
      Window Size {required && <span className="text-red-500">*</span>}
    </span>
    <div className="mt-1 flex">
      <input
        type="number"
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        className="block w-full rounded-l-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
        placeholder="Enter window size"
        min="1"
        step="1"
        required={required}
      />
      <select
        value={unit}
        onChange={(e) => onUnitChange(e.target.value)}
        className="rounded-r-md border-l-0 border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
      >
        <option value="seconds">seconds</option>
        <option value="hours">hours</option>
        <option value="days">days</option>
      </select>
    </div>
  </label>
)

export default WindowSizeInput