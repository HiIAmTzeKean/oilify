import { ResultType } from '../types/evaluationResultsTypes'

export const getResultTypeColor = (type: string) => {
  switch (type) {
    case 'macro': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    case 'micro': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    case 'window': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    case 'user': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
  }
}

export const getTableHeaders = (type: ResultType) => {
  const baseHeaders = ['Algorithm', 'Metric', 'Score']

  switch (type) {
    case 'macro':
      return [...baseHeaders, 'Num Windows']
    case 'micro':
      return [...baseHeaders, 'Num Users']
    case 'window':
      return [...baseHeaders, 'Num Users', 'Timestamp']
    case 'user':
      return [...baseHeaders, 'User ID', 'Timestamp']
    default:
      return baseHeaders
  }
}