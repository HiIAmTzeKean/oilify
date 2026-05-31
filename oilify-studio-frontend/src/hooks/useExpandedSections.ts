import { useState } from 'react'
import { ResultType } from '../types/evaluationResultsTypes'

export const useExpandedSections = () => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    macro: true,
    micro: true,
    window: true,
    user: true,
  })

  const toggleSection = (type: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [type]: !prev[type]
    }))
  }

  return { expandedSections, toggleSection }
}