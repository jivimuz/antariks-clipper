import { useJobProcess } from '@/contexts/JobProcessContext';
import { useCallback } from 'react';

/**
 * Hook untuk tracking job processing
 * Gunakan ini saat membuat job baru untuk auto-start tracking
 */
export function useJobTracking() {
  const { addJob, removeJob } = useJobProcess();

  const trackJob = useCallback((jobId: string, sourceUrl?: string) => {
    addJob(jobId, sourceUrl);
  }, [addJob]);

  const stopTrackingJob = useCallback((jobId: string) => {
    removeJob(jobId);
  }, [removeJob]);

  return { trackJob, stopTrackingJob };
}
