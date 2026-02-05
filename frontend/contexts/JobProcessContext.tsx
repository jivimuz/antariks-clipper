'use client';

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { getApiUrl } from '@/lib/api';

export interface ProcessingStep {
  name: string;
  label: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  progress: number;
  error?: string;
}

export interface JobProcessItem {
  jobId: string;
  sourceUrl?: string;
  status: 'queued' | 'processing' | 'ready' | 'failed' | 'cancelled';
  progress: number;
  currentStep?: string;
  steps: ProcessingStep[];
  error?: string;
  startedAt: number;
  estimatedTime?: number;
}

interface JobProcessContextType {
  jobs: Map<string, JobProcessItem>;
  addJob: (jobId: string, sourceUrl?: string) => void;
  removeJob: (jobId: string) => void;
}

const JobProcessContext = createContext<JobProcessContextType | undefined>(undefined);

const STEPS = [
  { name: 'download', label: 'Download' },
  { name: 'normalize', label: 'Normalize' },
  { name: 'transcribe', label: 'Transcribe' },
  { name: 'generate_highlights', label: 'Highlights' },
  { name: 'create_clips', label: 'Create Clips' }
];

const STEP_PROGRESS_MAP: Record<string, number> = {
  'download': 10,
  'acquire': 30,
  'normalize': 38,
  'transcribe': 60,
  'generate_highlights': 70,
  'create_clips': 80,
  'ready': 100
};

export function JobProcessProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<Map<string, JobProcessItem>>(new Map());
  const pollIntervalsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const API_URL = getApiUrl();

  // Initialize steps array
  const initializeSteps = (): ProcessingStep[] => {
    return STEPS.map(step => ({
      name: step.name,
      label: step.label,
      status: 'pending',
      progress: 0
    }));
  };

  // Polling function untuk satu job
  const pollJobStatus = useCallback(async (jobId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
      if (!res.ok) {
        if (res.status === 404) {
          return 'stop';
        }
        return 'continue';
      }

      const job = await res.json();
      
      setJobs(prev => {
        const newMap = new Map(prev);
        const existing = newMap.get(jobId);
        if (existing) {
          // Update steps based on current progress
          const updatedSteps = existing.steps.map(step => {
            const stepProgress = STEP_PROGRESS_MAP[step.name] || 0;
            const currentProgress = STEP_PROGRESS_MAP[job.step] || job.progress || 0;

            let status: 'pending' | 'in-progress' | 'completed' | 'failed' = 'pending';
            let progress = 0;

            if (job.status === 'failed') {
              status = 'failed';
            } else if (stepProgress < currentProgress) {
              status = 'completed';
              progress = 100;
            } else if (stepProgress === currentProgress || job.step?.includes(step.name)) {
              status = 'in-progress';
              progress = job.progress || 0;
            }

            return {
              ...step,
              status,
              progress,
              error: status === 'failed' && step.status === 'in-progress' ? job.error : undefined
            };
          });

          newMap.set(jobId, {
            ...existing,
            status: job.status,
            progress: job.progress || 0,
            currentStep: job.step,
            steps: updatedSteps,
            error: job.error
          });
        }
        return newMap;
      });

      // Stop polling jika sudah selesai, gagal, atau dibatalkan
      if (['ready', 'failed', 'cancelled'].includes(job.status)) {
        return 'stop';
      }
      
      return 'continue';
    } catch (error) {
      console.error('Poll error:', error);
      return 'continue';
    }
  }, [API_URL]);

  // Start polling untuk job baru
  const startPolling = useCallback((jobId: string) => {
    const pollInterval = setInterval(async () => {
      const result = await pollJobStatus(jobId);
      if (result === 'stop') {
        clearInterval(pollInterval);
        pollIntervalsRef.current?.delete(jobId);
      }
    }, 1000); // Poll setiap 1 detik

    pollIntervalsRef.current?.set(jobId, pollInterval);
  }, [pollJobStatus]);

  const addJob = useCallback((jobId: string, sourceUrl?: string) => {
    setJobs(prev => {
      const newMap = new Map(prev);
      if (!newMap.has(jobId)) {
        newMap.set(jobId, {
          jobId,
          sourceUrl,
          status: 'queued',
          progress: 0,
          steps: initializeSteps(),
          startedAt: Date.now()
        });
      }
      return newMap;
    });

    // Start polling untuk job ini
    startPolling(jobId);
  }, [startPolling]);

  const removeJob = useCallback((jobId: string) => {
    // Clear polling interval
    const interval = pollIntervalsRef.current?.get(jobId);
    if (interval) {
      clearInterval(interval);
      pollIntervalsRef.current?.delete(jobId);
    }

    // Remove job dari state
    setJobs(prev => {
      const newMap = new Map(prev);
      newMap.delete(jobId);
      return newMap;
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      pollIntervalsRef.current?.forEach(interval => clearInterval(interval));
      pollIntervalsRef.current?.clear();
    };
  }, []);

  return (
    <JobProcessContext.Provider value={{ jobs, addJob, removeJob }}>
      {children}
    </JobProcessContext.Provider>
  );
}

export function useJobProcess() {
  const context = useContext(JobProcessContext);
  if (context === undefined) {
    throw new Error('useJobProcess must be used within JobProcessProvider');
  }
  return context;
}
