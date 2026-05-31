import React from 'react'

interface ErrorDisplayProps {
  error: string
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error }) => (
  <div className="text-red-600 bg-red-50 p-2 rounded mb-4">{error}</div>
)

export default ErrorDisplay