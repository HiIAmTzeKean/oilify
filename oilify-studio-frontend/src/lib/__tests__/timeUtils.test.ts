import { describe, it, expect } from 'vitest'
import { convertToSeconds } from '../timeUtils'

describe('convertToSeconds', () => {
  it('converts hours to seconds', () => {
    expect(convertToSeconds('2', 'hours')).toBe(7200)
  })

  it('converts days to seconds', () => {
    expect(convertToSeconds('3', 'days')).toBe(259200)
  })

  it('returns the value as-is for the seconds unit', () => {
    expect(convertToSeconds('45', 'seconds')).toBe(45)
  })

  it('returns the value as-is for an unknown unit', () => {
    expect(convertToSeconds('10', 'minutes')).toBe(10)
  })

  it('returns 0 for a non-numeric value', () => {
    expect(convertToSeconds('abc', 'hours')).toBe(0)
  })

  it('returns 0 for an empty string', () => {
    expect(convertToSeconds('', 'days')).toBe(0)
  })

  it('handles single-digit values', () => {
    expect(convertToSeconds('1', 'hours')).toBe(3600)
    expect(convertToSeconds('1', 'days')).toBe(86400)
  })
})
