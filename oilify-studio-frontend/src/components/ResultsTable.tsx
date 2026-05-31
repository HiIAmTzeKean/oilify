import React from 'react'
import { EvaluationResult, ResultType } from '../types/evaluationResultsTypes'

interface ResultsTableProps {
  results: EvaluationResult[]
  type: ResultType
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, type }) => {
  const renderTableCell = (result: EvaluationResult, column: string) => {
    switch (column) {
      case 'Algorithm':
        return result.algorithm || 'N/A'
      case 'Metric':
        return result.metric || 'N/A'
      case 'Score':
        return result.score !== undefined ? result.score.toFixed(4) : 'N/A'
      case 'Num Windows':
        return result.num_window || 'N/A'
      case 'Num Users':
        return result.num_user || 'N/A'
      case 'User ID':
        return result.user_id || 'N/A'
      case 'Timestamp':
        return result.timestamp || 'N/A'
      default:
        return 'N/A'
    }
  }

  const headers = [
    'Algorithm', 'Metric', 'Score',
    ...(type === 'macro' ? ['Num Windows'] : []),
    ...(type === 'micro' ? ['Num Users'] : []),
    ...(type === 'window' ? ['Num Users', 'Timestamp'] : []),
    ...(type === 'user' ? ['User ID', 'Timestamp'] : [])
  ]

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-slate-600">
        <thead className="bg-gray-50 dark:bg-slate-700">
          <tr>
            {headers.map(header => (
              <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-slate-600">
          {results.map((result) => (
            <tr key={result.id} className="hover:bg-gray-50 dark:hover:bg-slate-700">
              {headers.map(header => (
                <td key={header} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                  {renderTableCell(result, header)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ResultsTable