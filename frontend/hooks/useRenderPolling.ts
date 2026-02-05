'use client';

import { useEffect, useCallback } from 'react';
import { useDownloads } from '@/contexts/DownloadContext';
import { getApiUrl } from '@/lib/api';
import toast from 'react-hot-toast';

interface UseRenderPollingOptions {
  onComplete?: (renderId: string, downloadUrl: string) => void;
  onError?: (renderId: string, error: string) => void;
}

export function useRenderPolling(options: UseRenderPollingOptions = {}) {
  const { downloads, updateDownload, addDownload } = useDownloads();
  const API_URL = getApiUrl();

  const pollRender = useCallback(async (renderId: string) => {
    try {
      const response = await fetch(`${API_URL}/api/renders/${renderId}`);
      if (!response.ok) throw new Error('Failed to fetch render status');
      
      const render = await response.json();
      
      updateDownload(renderId, {
        status: render.status,
        progress: render.progress || 0,
        error: render.error,
        downloadUrl: render.output_path ? `/api/renders/${renderId}/download` : undefined,
      });

      // If ready, trigger callback
      if (render.status === 'ready' && render.output_path) {
        options.onComplete?.(renderId, `/api/renders/${renderId}/download`);
        updateDownload(renderId, { status: 'completed' });
      }

      // If failed, trigger error callback
      if (render.status === 'failed') {
        options.onError?.(renderId, render.error || 'Render failed');
      }

      return render;
    } catch (error) {
      console.error('Poll render error:', error);
      updateDownload(renderId, {
        status: 'failed',
        error: 'Failed to check render status',
      });
      return null;
    }
  }, [API_URL, updateDownload, options]);

  // Auto-poll active renders
  useEffect(() => {
    const activeRenders = Array.from(downloads.values()).filter(
      d => d.status === 'queued' || d.status === 'processing'
    );

    if (activeRenders.length === 0) return;

    const intervals = activeRenders.map(download => {
      return setInterval(() => {
        pollRender(download.renderId);
      }, 2000); // Poll every 2 seconds
    });

    return () => {
      intervals.forEach(interval => clearInterval(interval));
    };
  }, [downloads, pollRender]);

  const startRender = useCallback(async (
    clipId: string,
    clipTitle: string,
    jobId: string,
    options: {
      face_tracking?: boolean;
      smart_crop?: boolean;
      captions?: boolean;
      watermark_text?: string;
    } = {}
  ) => {
    try {
      const response = await fetch(`${API_URL}/api/renders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clip_id: clipId, ...options }),
      });

      if (!response.ok) throw new Error('Failed to start render');
      
      const data = await response.json();
      const renderId = data.render_id;

      // Add to download manager
      addDownload({
        id: renderId,
        renderId,
        clipTitle,
        jobId,
        status: 'queued',
        progress: 0,
      });

      toast.success(`Render dimulai: ${clipTitle}`);
      return renderId;
    } catch (error: any) {
      toast.error(`Gagal memulai render: ${error.message}`);
      throw error;
    }
  }, [API_URL, addDownload]);

  return {
    startRender,
    pollRender,
  };
}
