import { describe, it, expect } from 'vitest'
import { getResultTypeColor, getTableHeaders } from '../resultTypeConfig'
import { ResultType } from '../../types/evaluationResultsTypes'

describe('getResultTypeColor', () => {
  it.each([
    ['macro', 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'],
    ['micro', 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'],
    ['window', 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'],
    ['user', 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'],
  ])('returns the correct classes for type "%s"', (type, expected) => {
    expect(getResultTypeColor(type)).toBe(expected)
  })

  it('returns default classes for an unknown type', () => {
    expect(getResultTypeColor('unknown')).toBe(
      'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
    )
  })
})

describe('getTableHeaders', () => {
  const BASE = ['Algorithm', 'Metric', 'Score']

  it('includes Num Windows for macro', () => {
    expect(getTableHeaders('macro')).toEqual([...BASE, 'Num Windows'])
  })

  it('includes Num Users for micro', () => {
    expect(getTableHeaders('micro')).toEqual([...BASE, 'Num Users'])
  })

  it('includes Num Users and Timestamp for window', () => {
    expect(getTableHeaders('window')).toEqual([...BASE, 'Num Users', 'Timestamp'])
  })

  it('includes User ID and Timestamp for user', () => {
    expect(getTableHeaders('user')).toEqual([...BASE, 'User ID', 'Timestamp'])
  })

  it('returns only base headers for an unknown type', () => {
    // Cast to ResultType to exercise the default branch
    expect(getTableHeaders('unknown' as ResultType)).toEqual(BASE)
  })
})
