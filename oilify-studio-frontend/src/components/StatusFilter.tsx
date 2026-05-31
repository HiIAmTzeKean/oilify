import React from 'react'

interface StatusFilterProps {
  statuses: string[]
  selectedStatus: string | null
  onStatusChange: (status: string | null) => void
}

const StatusFilter: React.FC<StatusFilterProps> = ({ statuses, selectedStatus, onStatusChange }) => {
  return (
    <select
      value={selectedStatus || ''}
      onChange={(e) => onStatusChange(e.target.value || null)}
      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">All Statuses</option>
      {statuses.map(status => (
        <option key={status} value={status}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </option>
      ))}
    </select>
  )
}

export default StatusFilter