import { useState, useEffect } from 'react'
import { StreamJob, Algorithm, SelectedAlgorithm } from '../types/algoTypes'

export const useAlgoState = (streamJobs: StreamJob[]) => {
  const [selectedStreamJob, setSelectedStreamJob] = useState<number | null>(null)
  const [selectedAlgorithms, setSelectedAlgorithms] = useState<SelectedAlgorithm[]>([])
  const [originalAlgorithms, setOriginalAlgorithms] = useState<Algorithm[]>([])

  // Pre-populate selected algorithms when stream is selected
  useEffect(() => {
    if (selectedStreamJob) {
      const stream = streamJobs.find(job => job.id === selectedStreamJob)
      if (stream) {
        setOriginalAlgorithms(stream.algorithms)
        // Parse the saved parameters for existing algorithms
        setSelectedAlgorithms(stream.algorithms.map(algo => ({
          id: algo.id,
          clientKey: String(algo.id),
          name: algo.name,
          params: algo.params ? JSON.parse(algo.params) : {}
        })))
      }
    } else {
      setOriginalAlgorithms([])
      setSelectedAlgorithms([])
    }
  }, [selectedStreamJob, streamJobs])

  const resetState = () => {
    setSelectedStreamJob(null)
    setSelectedAlgorithms([])
    setOriginalAlgorithms([])
  }

  return {
    selectedStreamJob,
    setSelectedStreamJob,
    selectedAlgorithms,
    setSelectedAlgorithms,
    originalAlgorithms,
    resetState
  }
}