import { apiFetch } from '../lib/api'
import { SelectedAlgorithm, Algorithm } from '../types/algoTypes'

export const fetchAlgorithmParams = async (algorithmId: string): Promise<Record<string, any>> => {
  try {
    const response = await apiFetch(`/api/v1/algorithm/get_params/${algorithmId}`)
    return await response.json()
  } catch (err) {
    console.error('Failed to fetch params:', err)
    return {}
  }
}

export const updateAlgorithmsForStream = async (
  selectedStreamJob: number,
  selectedAlgorithms: SelectedAlgorithm[],
  originalAlgorithms: Algorithm[]
) => {
  // Determine algorithms to delete: in original but whose id is no longer in selected
  const selectedIds = new Set(selectedAlgorithms.map(s => s.id).filter(Boolean))
  const algorithmsToDelete = originalAlgorithms.filter(o => o.id && !selectedIds.has(o.id))

  for (const algo of algorithmsToDelete) {
    await apiFetch(`/api/v1/stream/${selectedStreamJob}/remove_algorithm/${algo.id}`, {
      method: 'DELETE'
    })
  }

  // Strip clientKey before sending — backend only needs id, name, params
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const payload = selectedAlgorithms.map(({ clientKey: _ck, ...rest }) => rest)

  const response = await apiFetch(`/api/v1/stream/${selectedStreamJob}/add_algorithms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ algorithms: payload })
  })

  if (!response.ok) {
    throw new Error('Failed to update algorithms')
  }

  return await response.json()
}