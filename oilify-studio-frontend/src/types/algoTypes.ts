export interface StreamJob {
  id: number
  name: string
  description: string
  status: string
  dataset: string
  top_k: number
  metrics: string[]
  window_size: number
  created_at: string
  algorithms: Algorithm[]
}

export interface Algorithm {
  id?: number
  name: string
  description: string
  params?: string
}

export interface SelectedAlgorithm {
  id?: number
  clientKey: string
  name: string
  params: Record<string, any>
}