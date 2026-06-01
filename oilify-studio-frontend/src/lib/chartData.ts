type ChartPointDate = {
  timestamp?: string
}

const DATE_ONLY_REGEX = /^\d{4}-\d{2}-\d{2}$/

export const getPointDate = (point: ChartPointDate): string | undefined => {
  const rawDate = point.timestamp
  if (typeof rawDate !== 'string') {
    return undefined
  }

  const trimmed = rawDate.trim()
  return trimmed.length > 0 ? trimmed : undefined
}

export const hasPointDate = (point: ChartPointDate): boolean => {
  return getPointDate(point) !== undefined
}

export const getSortedPointDates = (points: ChartPointDate[]): string[] => {
  return Array.from(new Set(points.map((point) => getPointDate(point)).filter(Boolean))).sort() as string[]
}

export const sortPointsByDate = <T extends ChartPointDate>(points: T[]): T[] => {
  return points
    .filter((point) => hasPointDate(point))
    .slice()
    .sort((left, right) => (getPointDate(left) ?? '').localeCompare(getPointDate(right) ?? ''))
}

export const parseChartDate = (value: string): Date | undefined => {
  if (!value) {
    return undefined
  }

  const trimmed = value.trim()
  const candidate = DATE_ONLY_REGEX.test(trimmed) ? `${trimmed}T00:00:00Z` : trimmed
  const dateValue = new Date(candidate)
  return Number.isNaN(dateValue.getTime()) ? undefined : dateValue
}

export const formatChartDate = (value: string): string => {
  const dateValue = parseChartDate(value)
  return dateValue ? new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(dateValue) : 'Invalid date'
}