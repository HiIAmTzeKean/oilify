import React from 'react'

interface SuccessStateProps {
  streamId: number | null
  onGoToAlgo: () => void
  onCreateAnother: () => void
}

const SuccessState: React.FC<SuccessStateProps> = ({
  streamId,
  onGoToAlgo,
  onCreateAnother
}) => (
  <div className="text-center space-y-6">
    <div className="text-green-600">
      <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
    <div>
      <h2 className="text-xl font-semibold text-green-800 dark:text-green-200 mb-2">
        Stream Created Successfully!
      </h2>
      <p className="text-slate-600 dark:text-slate-400">
        Stream ID: <span className="font-mono font-semibold">{streamId}</span>
      </p>
    </div>
    <div className="flex flex-col sm:flex-row gap-4 justify-center">
      <button
        onClick={onGoToAlgo}
        className="inline-flex justify-center items-center rounded-md bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 font-medium transition-colors"
      >
        Go to Algorithm Page
      </button>
      <button
        onClick={onCreateAnother}
        className="inline-flex justify-center items-center rounded-md bg-slate-600 hover:bg-slate-700 text-white px-6 py-2 font-medium transition-colors"
      >
        Create Another Stream
      </button>
    </div>
  </div>
)

export default SuccessState