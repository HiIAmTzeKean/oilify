import React from 'react'

interface SelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder?: string
  required?: boolean
  disabled?: boolean
  loading?: boolean
}

const Select: React.FC<SelectProps> = ({
  label,
  value,
  onChange,
  options,
  placeholder = 'Select an option',
  required = false,
  disabled = false,
  loading = false
}) => (
  <label className="block">
    <span className="text-sm font-medium">
      {label} {required && <span className="text-red-500">*</span>}
    </span>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
      disabled={disabled || loading}
      required={required}
    >
      <option value="">
        {loading ? 'Loading...' : placeholder}
      </option>
      {options.map(option => (
        <option key={option} value={option}>{option}</option>
      ))}
    </select>
  </label>
)

export default Select