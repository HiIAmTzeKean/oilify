import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAlgoState } from '../useAlgoState'
import { StreamJob } from '../../types/algoTypes'

const makeStreamJob = (overrides: Partial<StreamJob> = {}): StreamJob => ({
  id: 1,
  name: 'Test Stream',
  description: '',
  status: 'active',
  dataset: 'ds1',
  top_k: 10,
  metrics: ['precision'],
  window_size: 3600,
  created_at: '2024-01-01T00:00:00Z',
  algorithms: [],
  ...overrides,
})

describe('useAlgoState', () => {
  it('starts with no stream selected and empty algorithm lists', () => {
    // Empty stable reference — no re-render churn from inline array literals.
    const noJobs: StreamJob[] = []
    const { result } = renderHook(() => useAlgoState(noJobs))

    expect(result.current.selectedStreamJob).toBeNull()
    expect(result.current.selectedAlgorithms).toEqual([])
    expect(result.current.originalAlgorithms).toEqual([])
  })

  it('populates algorithms when a stream job is selected', () => {
    const job = makeStreamJob({
      id: 5,
      algorithms: [
        { id: 10, name: 'AlgoA', description: 'desc', params: JSON.stringify({ k: 3 }) },
      ],
    })
    // Stable reference — if re-created each render, the effect's dep would
    // change on every update and cause an infinite effect/state loop.
    const jobs = [job]

    const { result } = renderHook(() => useAlgoState(jobs))

    act(() => {
      result.current.setSelectedStreamJob(5)
    })

    expect(result.current.originalAlgorithms).toEqual(job.algorithms)
    expect(result.current.selectedAlgorithms).toHaveLength(1)
    expect(result.current.selectedAlgorithms[0]).toEqual({
      id: 10,
      clientKey: '10',
      name: 'AlgoA',
      params: { k: 3 },
    })
  })

  it('defaults params to an empty object when an algorithm has no saved params', () => {
    const job = makeStreamJob({
      id: 7,
      algorithms: [{ id: 20, name: 'AlgoB', description: 'no params' }],
    })
    const jobs = [job]

    const { result } = renderHook(() => useAlgoState(jobs))

    act(() => {
      result.current.setSelectedStreamJob(7)
    })

    expect(result.current.selectedAlgorithms).toHaveLength(1)
    expect(result.current.selectedAlgorithms[0].params).toEqual({})
  })

  it('clears algorithms when the selected stream is set to null', () => {
    const job = makeStreamJob({
      id: 3,
      algorithms: [{ id: 1, name: 'AlgoC', description: '' }],
    })
    const jobs = [job]

    const { result } = renderHook(() => useAlgoState(jobs))

    act(() => {
      result.current.setSelectedStreamJob(3)
    })
    expect(result.current.selectedAlgorithms).toHaveLength(1)

    act(() => {
      result.current.setSelectedStreamJob(null)
    })

    expect(result.current.selectedAlgorithms).toEqual([])
    expect(result.current.originalAlgorithms).toEqual([])
  })

  it('resets all state when resetState is called', () => {
    const job = makeStreamJob({
      id: 9,
      algorithms: [{ id: 99, name: 'AlgoD', description: '' }],
    })
    const jobs = [job]

    const { result } = renderHook(() => useAlgoState(jobs))

    act(() => {
      result.current.setSelectedStreamJob(9)
    })
    expect(result.current.selectedAlgorithms).toHaveLength(1)

    act(() => {
      result.current.resetState()
    })

    expect(result.current.selectedStreamJob).toBeNull()
    expect(result.current.selectedAlgorithms).toEqual([])
    expect(result.current.originalAlgorithms).toEqual([])
  })

  it('does not crash when the selected stream job id is not in the list', () => {
    const noJobs: StreamJob[] = []

    const { result } = renderHook(() => useAlgoState(noJobs))

    act(() => {
      result.current.setSelectedStreamJob(999)
    })

    expect(result.current.selectedAlgorithms).toEqual([])
    expect(result.current.originalAlgorithms).toEqual([])
  })
})
