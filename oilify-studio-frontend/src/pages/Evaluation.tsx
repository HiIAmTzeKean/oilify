import React, { useState, useMemo } from 'react'
import Fuse from 'fuse.js'
import { useEvaluationJobs } from '../hooks/useEvaluationJobs'
import EvaluationJobList from '../components/EvaluationJobList'
import SearchBar from '../components/SearchBar'
import StatusFilter from '../components/StatusFilter'

const Evaluation: React.FC = () => {
  const { streamJobs, loading, running, runJob, deleteJob } = useEvaluationJobs()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null)

  const statuses = Array.from(new Set(streamJobs.map(job => job.status)))

  const statusFilteredJobs = selectedStatus ? streamJobs.filter(job => job.status === selectedStatus) : streamJobs

  const filteredJobs = useMemo(() => {
    if (!searchQuery) return statusFilteredJobs
    const fuse = new Fuse(statusFilteredJobs, { keys: ['name'], threshold: 0.3 })
    return fuse.search(searchQuery).map(result => result.item)
  }, [statusFilteredJobs, searchQuery])

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">Evaluation</h1>
      <div className="mb-4 flex gap-4">
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search evaluation jobs by name..."
        />
        <StatusFilter
          statuses={statuses}
          selectedStatus={selectedStatus}
          onStatusChange={setSelectedStatus}
        />
      </div>
      <EvaluationJobList
        streamJobs={filteredJobs}
        loading={loading}
        running={running}
        onRunJob={runJob}
        onDeleteJob={deleteJob}
      />
    </div>
  )
}

export default Evaluation