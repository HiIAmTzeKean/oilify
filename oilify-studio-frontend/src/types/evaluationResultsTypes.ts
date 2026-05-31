export interface EvaluationResult {
  id: number
  algorithm?: string
  metric?: string
  score?: number
  num_window?: number
  num_user?: number
  user_id?: number
  timestamp?: string
}

export interface EvaluationResultsData {
  macro: EvaluationResult[]
  micro: EvaluationResult[]
  window: EvaluationResult[]
  user: EvaluationResult[]
}

export type ResultType = 'macro' | 'micro' | 'window' | 'user'