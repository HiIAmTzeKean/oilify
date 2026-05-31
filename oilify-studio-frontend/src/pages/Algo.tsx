import React, { useState } from 'react'
import { toast } from 'react-toastify'
import { useStreamJobs } from '../hooks/useStreamJobs'
import { useAlgorithms } from '../hooks/useAlgorithms'
import { useAlgoState } from '../hooks/useAlgoState'
import { fetchAlgorithmParams, updateAlgorithmsForStream } from '../utils/algoUtils'
import StreamJobSelector from '../components/StreamJobSelector'
import AlgorithmSelector from '../components/AlgorithmSelector'
import AlgorithmParameters from '../components/AlgorithmParameters'
import StreamDetails from '../components/StreamDetails'
import ErrorDisplay from '../components/ErrorDisplay'

const Algo: React.FC = () => {
  const { streamJobs, loading: fetchingStreams, error: streamError, refreshStreamJobs } = useStreamJobs()
  const { algorithms, loading: fetchingAlgorithms, error: algoError } = useAlgorithms()
  const {
    selectedStreamJob,
    setSelectedStreamJob,
    selectedAlgorithms,
    setSelectedAlgorithms,
    originalAlgorithms,
    resetState
  } = useAlgoState(streamJobs)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleAlgorithmToggle = async (algorithmId: string) => {
    const params = await fetchAlgorithmParams(algorithmId)
    setSelectedAlgorithms(prev => [
      ...prev,
      { name: algorithmId, params, id: undefined, clientKey: crypto.randomUUID() },
    ])
  }

  const handleRemoveAlgorithm = (index: number) => {
    setSelectedAlgorithms(prev => prev.filter((_, i) => i !== index))
  }

  const handleParamChange = (index: number, key: string, value: any) => {
    setSelectedAlgorithms(prev => prev.map((algo, i) =>
      i === index ? { ...algo, params: { ...algo.params, [key]: value } } : algo
    ))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!selectedStreamJob || selectedAlgorithms.length === 0) {
      setError('Please select a stream job and at least one algorithm')
      return
    }

    setLoading(true)
    try {
      await updateAlgorithmsForStream(selectedStreamJob, selectedAlgorithms, originalAlgorithms)
      toast.success('Algorithms updated successfully!')
      resetState()
      await refreshStreamJobs()
    } catch (err: any) {
      setError(err?.message ?? String(err))
    } finally {
      setLoading(false)
    }
  }

  const selectedStream = streamJobs.find(job => job.id === selectedStreamJob)

  return (
    <div className="max-w-4xl mx-auto mt-12">
      <h1 className="text-3xl font-bold mb-4">Configure Algorithms for Stream</h1>
      <div className="grid md:grid-cols-2 gap-8">
        <StreamJobSelector
          streamJobs={streamJobs}
          loading={fetchingStreams}
          selectedStreamJob={selectedStreamJob}
          onSelect={setSelectedStreamJob}
        />
        <AlgorithmSelector
          algorithms={algorithms}
          loading={fetchingAlgorithms}
          selectedAlgorithms={selectedAlgorithms}
          onToggle={handleAlgorithmToggle}
        />
      </div>

      {selectedAlgorithms.length > 0 && (
        <AlgorithmParameters
          selectedAlgorithms={selectedAlgorithms}
          onParamChange={handleParamChange}
          onRemove={handleRemoveAlgorithm}
        />
      )}

      <StreamDetails
        selectedStream={selectedStream}
        selectedAlgorithms={selectedAlgorithms}
      />

      <div className="mt-8">
        {(error || streamError || algoError) && (
          <ErrorDisplay error={error || streamError || algoError || ''} />
        )}
        <button
          onClick={handleSubmit}
          disabled={loading || !selectedStreamJob || selectedAlgorithms.length === 0}
          className="w-full inline-flex justify-center items-center rounded-md bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 font-medium disabled:opacity-60"
        >
          {loading ? 'Updating Algorithms...' : 'Update Algorithms'}
        </button>
      </div>
    </div>
  )
}

export default Algo