import React from 'react'
import { StreamJob } from '../types/evaluationTypes'
import EvaluationJobItem from './EvaluationJobItem'
import LoadingSpinner from './LoadingSpinner'
import EmptyState from './EmptyState'

interface EvaluationJobListProps {
  streamJobs: StreamJob[]
  loading: boolean
  running: boolean
  onRunJob: (job: StreamJob) => void
  onDeleteJob: (jobId: number) => void
}

const EvaluationJobList: React.FC<EvaluationJobListProps> = ({
  streamJobs,
  loading,
  running,
  onRunJob,
  onDeleteJob
}) => {
  if (loading) {
    return <LoadingSpinner message="Loading evaluation jobs..." />
  }

  if (streamJobs.length === 0) {
    return <EmptyState message="No evaluation jobs available." />
  }

  return (
    <div className="space-y-4">
      {streamJobs.map(job => (
        <EvaluationJobItem
          key={job.id}
          job={job}
          running={running}
          onRun={onRunJob}
          onDelete={onDeleteJob}
        />
      ))}
    </div>
  )
}

export default EvaluationJobList