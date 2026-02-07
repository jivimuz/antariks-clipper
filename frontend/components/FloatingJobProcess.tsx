'use client';

import { useJobProcess } from '@/contexts/JobProcessContext';
import { X, Minimize2, Maximize2, AlertCircle, CheckCircle } from 'lucide-react';
import { useState } from 'react';

export default function FloatingJobProcess() {
  const { jobs, removeJob } = useJobProcess();
  const [isMinimized, setIsMinimized] = useState(true);
  const [isHidden, setIsHidden] = useState(true); // default sembunyi
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const jobArray = Array.from(jobs.values());
  const activeJobs = jobArray.filter(j => j.status === 'processing' || j.status === 'queued');
  const completedJobs = jobArray.filter(j => j.status === 'ready' || j.status === 'failed' || j.status === 'cancelled');

  // Auto-select first active job or first job
  const displayJob = selectedJobId 
    ? jobArray.find(j => j.jobId === selectedJobId)
    : activeJobs[0] || jobArray[0];

  if (jobArray.length === 0) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'queued':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
      case 'processing':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200';
      case 'ready':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 'cancelled':
        return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
      default:
        return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 text-white';
      case 'in-progress':
        return 'bg-blue-500 text-white';
      case 'failed':
        return 'bg-red-500 text-white';
      default:
        return 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300';
    }
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  if (isHidden) {
    return (
      <button
        onClick={() => setIsHidden(false)}
        className="fixed bottom-6 left-6 bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-full shadow-2xl z-40 transition-all duration-300"
        title="Tampilkan Job Process"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19l-7-7m0 0l7-7m-7 7h16" />
        </svg>
        {activeJobs.length > 0 && (
          <span className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded-full">
            {activeJobs.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <>
      <div className="fixed bottom-6 left-6 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl z-40 border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h3 className="font-semibold">Job Process</h3>
            {activeJobs.length > 0 && (
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                {activeJobs.length} aktif
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="hover:bg-white/20 p-1 rounded transition-colors"
              title={isMinimized ? 'Perbesar' : 'Perkecil'}
            >
              {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setIsHidden(true)}
              className="hover:bg-white/20 p-1 rounded transition-colors"
              title="Sembunyikan"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Job List Tabs */}
        {!isMinimized && jobArray.length > 1 && (
          <div className="border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
            <div className="flex gap-2 p-2">
              {jobArray.map((job) => (
                <button
                  key={job.jobId}
                  onClick={() => setSelectedJobId(job.jobId)}
                  className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap transition-colors ${
                    selectedJobId === job.jobId
                      ? 'bg-purple-600 text-white'
                      : `${getStatusColor(job.status)}`
                  }`}
                  title={job.sourceUrl}
                >
                  {job.jobId.substring(0, 8)}...
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        {!isMinimized && displayJob && (
          <div className="p-4 space-y-4">
            {/* Job Status */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                  Job: {displayJob.jobId.substring(0, 12)}...
                </h4>
                <span className={`text-xs font-medium px-2 py-1 rounded ${getStatusColor(displayJob.status)}`}>
                  {displayJob.status.charAt(0).toUpperCase() + displayJob.status.slice(1)}
                </span>
              </div>

              {displayJob.sourceUrl && (
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {displayJob.sourceUrl}
                </p>
              )}

              {displayJob.error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-2">
                  <p className="text-xs text-red-800 dark:text-red-200">{displayJob.error}</p>
                </div>
              )}
            </div>

            {/* Overall Progress */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-400">Overall Progress</span>
                <span className="font-semibold text-gray-900 dark:text-white">{displayJob.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${displayJob.progress}%` }}
                />
              </div>
            </div>

            {/* Steps */}
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-900 dark:text-white">Processing Steps</p>
              <div className="space-y-2">
                {displayJob.steps.map((step, index) => (
                  <div key={step.name} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${getStepColor(
                            step.status
                          )}`}
                        >
                          {step.status === 'completed' || step.status === 'failed' ? (
                            getStepIcon(step.status)
                          ) : step.status === 'in-progress' ? (
                            <span className="animate-spin">●</span>
                          ) : (
                            index + 1
                          )}
                        </div>
                        <span className="text-xs font-medium text-gray-900 dark:text-white">
                          {step.label}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {step.progress > 0 && `${step.progress}%`}
                      </span>
                    </div>

                    {/* Step progress bar - hanya untuk in-progress */}
                    {step.status === 'in-progress' && (
                      <div className="ml-8 w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1">
                        <div
                          className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${step.progress}%` }}
                        />
                      </div>
                    )}

                    {/* Error message */}
                    {step.error && (
                      <p className="ml-8 text-xs text-red-600 dark:text-red-400">{step.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Time Info */}
            <div className="text-xs text-gray-500 dark:text-gray-400 flex justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
              <span>
                Started: {new Date(displayJob.startedAt).toLocaleTimeString()}
              </span>
              {displayJob.status === 'ready' && (
                <span className="text-green-600 dark:text-green-400 font-semibold">✓ Selesai</span>
              )}
            </div>

            {/* Action Buttons */}
            {completedJobs.length > 0 && (
              <button
                onClick={() => {
                  completedJobs.forEach(job => removeJob(job.jobId));
                }}
                className="w-full px-3 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white text-xs font-medium rounded transition-colors"
              >
                Hapus {completedJobs.length} job selesai
              </button>
            )}
          </div>
        )}
      </div>
    </>
  );
}
