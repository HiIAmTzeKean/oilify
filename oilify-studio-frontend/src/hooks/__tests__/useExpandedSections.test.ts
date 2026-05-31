import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useExpandedSections } from '../useExpandedSections'

describe('useExpandedSections', () => {
  it('initialises all four sections as expanded', () => {
    const { result } = renderHook(() => useExpandedSections())

    expect(result.current.expandedSections).toEqual({
      macro: true,
      micro: true,
      window: true,
      user: true,
    })
  })

  it('collapses an expanded section when toggled', () => {
    const { result } = renderHook(() => useExpandedSections())

    act(() => result.current.toggleSection('macro'))

    expect(result.current.expandedSections.macro).toBe(false)
    expect(result.current.expandedSections.micro).toBe(true)
  })

  it('re-expands a collapsed section when toggled again', () => {
    const { result } = renderHook(() => useExpandedSections())

    act(() => result.current.toggleSection('window'))
    act(() => result.current.toggleSection('window'))

    expect(result.current.expandedSections.window).toBe(true)
  })

  it('toggles sections independently without affecting others', () => {
    const { result } = renderHook(() => useExpandedSections())

    act(() => {
      result.current.toggleSection('micro')
      result.current.toggleSection('user')
    })

    expect(result.current.expandedSections.micro).toBe(false)
    expect(result.current.expandedSections.user).toBe(false)
    expect(result.current.expandedSections.macro).toBe(true)
    expect(result.current.expandedSections.window).toBe(true)
  })
})
