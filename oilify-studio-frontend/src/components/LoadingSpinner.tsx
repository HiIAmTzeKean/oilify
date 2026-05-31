import React from 'react'

interface LoadingSpinnerProps {
  message?: string
  size?: 'small' | 'large'
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'small'
}) => {
  const sizeClasses = size === 'large'
    ? 'h-12 w-12'
    : 'h-8 w-8'

  const containerClasses = size === 'large'
    ? 'flex justify-center items-center h-64'
    : 'flex items-center justify-center'

  return (
    <div className={containerClasses}>
      <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses}`}></div>
      <span className="ml-2">{message}</span>
    </div>
  )
}

export default LoadingSpinner