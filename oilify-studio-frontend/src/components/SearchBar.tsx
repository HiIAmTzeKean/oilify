import React from 'react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

const SearchBar: React.FC<SearchBarProps> = ({ value, onChange, placeholder = "Search..." }) => {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
  )
}

export default SearchBar