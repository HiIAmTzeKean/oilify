export interface CreateStreamFormData {
  name: string
  description: string
  dataset: string
  topK: string
  selectedMetrics: string[]
  timestampSplitStart: string
  windowSizeValue: string
  windowSizeUnit: string
}

export interface CreateStreamState {
  formData: CreateStreamFormData
  loading: boolean
  streamCreated: boolean
  createdStreamId: number | null
  error: string | null
}