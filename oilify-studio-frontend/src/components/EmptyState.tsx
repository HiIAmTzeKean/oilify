import React from 'react'

interface EmptyStateProps {
  message: string
}

const EmptyState: React.FC<EmptyStateProps> = ({ message }) => (
  <div className="text-center py-8">
    <p className="text-slate-500">{message}</p>
  </div>
)

export default EmptyState