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
  started_at?: string
  completed_at?: string
  error_message?: string
  algorithms: any[]
}