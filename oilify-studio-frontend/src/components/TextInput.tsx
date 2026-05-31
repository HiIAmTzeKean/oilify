import React from 'react'

interface TextInputProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
  type?: string
  min?: string
}

const TextInput: React.FC<TextInputProps> = ({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  type = 'text',
  min
}) => (
  <label className="block">
    <span className="text-sm font-medium">
      {label} {required && <span className="text-red-500">*</span>}
    </span>
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
      placeholder={placeholder}
      min={min}
      required={required}
    />
  </label>
)

export default TextInput