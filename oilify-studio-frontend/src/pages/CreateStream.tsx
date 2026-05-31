import React from 'react'
import { useCreateStreamForm } from '../hooks/useCreateStreamForm'
import TextInput from '../components/TextInput'
import Select from '../components/Select'
import MetricsSelector from '../components/MetricsSelector'
import TimestampRangeSelector from '../components/TimestampRangeSelector'
import WindowSizeInput from '../components/WindowSizeInput'
import SuccessState from '../components/SuccessState'
import ErrorDisplay from '../components/ErrorDisplay'

const CreateStream: React.FC = () => {
  const {
    // State
    formData,
    loading,
    streamCreated,
    createdStreamId,
    error,
    datasets,
    availableMetrics,
    startDate,
    endDate,
    selectedTimestamp,
    fetchingDatasets,
    fetchingMetrics,
    fetchingTimestampRange,
    streamFormError,

    // Actions
    updateFormData,
    handleMetricChange,
    removeMetric,
    submitForm,
    resetForm,
    goToAlgo,
    setSelectedTimestamp
  } = useCreateStreamForm()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await submitForm()
  }

  return (
    <div className="max-w-xl mx-auto mt-12">
      <h1 className="text-3xl font-bold mb-4">Create Stream</h1>
      <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-md shadow">
        {streamCreated ? (
          <SuccessState
            streamId={createdStreamId}
            onGoToAlgo={goToAlgo}
            onCreateAnother={resetForm}
          />
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              {(error || streamFormError) && (
                <ErrorDisplay error={error || streamFormError || ''} />
              )}

              <TextInput
                label="Stream Name"
                value={formData.name}
                onChange={(value) => updateFormData({ name: value })}
                placeholder="Enter stream name"
                required
              />

              <label className="block">
                <span className="text-sm font-medium">Description</span>
                <textarea
                  value={formData.description}
                  onChange={(e) => updateFormData({ description: e.target.value })}
                  className="mt-1 block w-full rounded-md border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm focus:ring-2 focus:ring-blue-400 p-2"
                  placeholder="Enter stream description (optional)"
                  rows={3}
                />
              </label>

              <Select
                label="Dataset"
                value={formData.dataset}
                onChange={(value) => updateFormData({ dataset: value })}
                options={datasets}
                placeholder="Select a dataset"
                required
                disabled={fetchingDatasets}
                loading={fetchingDatasets}
              />

              <TextInput
                label="Top K"
                value={formData.topK}
                onChange={(value) => updateFormData({ topK: value })}
                placeholder="Enter top k value"
                type="number"
                min="1"
                required
              />

              <MetricsSelector
                availableMetrics={availableMetrics}
                selectedMetrics={formData.selectedMetrics}
                onMetricAdd={handleMetricChange}
                onMetricRemove={removeMetric}
                loading={fetchingMetrics}
              />

              <TimestampRangeSelector
                startDate={startDate}
                endDate={endDate}
                selectedTimestamp={selectedTimestamp}
                onTimestampChange={setSelectedTimestamp}
                loading={fetchingTimestampRange}
              />

              <WindowSizeInput
                value={formData.windowSizeValue}
                unit={formData.windowSizeUnit}
                onValueChange={(value) => updateFormData({ windowSizeValue: value })}
                onUnitChange={(unit) => updateFormData({ windowSizeUnit: unit })}
                required
              />

              <div>
                <button
                  type="submit"
                  className="w-full inline-flex justify-center items-center rounded-md bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 font-medium disabled:opacity-60"
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Stream'}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default CreateStream