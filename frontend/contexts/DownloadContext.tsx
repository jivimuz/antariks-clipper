'use client';

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { getApiUrl } from '@/lib/api';

export interface DownloadItem {
  id: string;
  renderId: string;
  clipTitle: string;
  jobId: string;
  status: 'queued' | 'processing' | 'ready' | 'downloading' | 'completed' | 'failed';
  progress: number;
  downloadUrl?: string;
  error?: string;
  startedAt: number;
}

interface DownloadContextType {
  downloads: Map<string, DownloadItem>;
  addDownload: (item: Omit<DownloadItem, 'startedAt'>) => void;
  updateDownload: (renderId: string, updates: Partial<DownloadItem>) => void;
  removeDownload: (renderId: string) => void;
  clearCompleted: () => void;
}

const DownloadContext = createContext<DownloadContextType | undefined>(undefined);

export function DownloadProvider({ children }: { children: React.ReactNode }) {
  const [downloads, setDownloads] = useState<Map<string, DownloadItem>>(new Map());
  const pollIntervalsRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const API_URL = getApiUrl();

  // Polling function untuk satu render
  const pollRenderStatus = useCallback(async (renderId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/renders/${renderId}`);
      if (!res.ok) {
        // Render mungkin sudah dihapus
        if (res.status === 404) {
          setDownloads(prev => {
            const newMap = new Map(prev);
            const item = newMap.get(renderId);
            if (item) {
              newMap.set(renderId, { ...item, status: 'failed', error: 'Render not found' });
            }
            return newMap;
          });
          return 'stop';
        }
        return 'continue';
      }

      const render = await res.json();
      
      setDownloads(prev => {
        const newMap = new Map(prev);
        const existing = newMap.get(renderId);
        if (existing) {
          newMap.set(renderId, {
            ...existing,
            status: render.status,
            progress: render.progress || 0,
            error: render.error,
            downloadUrl: render.output_path ? `/api/renders/${renderId}/download` : undefined,
          });
        }
        return newMap;
      });

      // Stop polling jika sudah selesai, gagal, atau dibatalkan
      if (['ready', 'completed', 'failed', 'cancelled'].includes(render.status)) {
        return 'stop';
      }
      
      return 'continue';
    } catch (error) {
      console.error('Poll error:', error);
      return 'continue';
    }
  }, [API_URL]);

  // Start polling untuk render baru
  const startPolling = useCallback((renderId: string) => {
    // Jangan start kalau sudah ada polling
    if (pollIntervalsRef.current.has(renderId)) {
      return;
    }

    const poll = async () => {
      const result = await pollRenderStatus(renderId);
      if (result === 'stop') {
        stopPolling(renderId);
      }
    };

    // Poll immediately
    poll();

    // Setup interval untuk polling berikutnya
    const intervalId = setInterval(poll, 2000);
    pollIntervalsRef.current.set(renderId, intervalId);
  }, [pollRenderStatus]);

  // Stop polling
  const stopPolling = useCallback((renderId: string) => {
    const intervalId = pollIntervalsRef.current.get(renderId);
    if (intervalId) {
      clearInterval(intervalId);
      pollIntervalsRef.current.delete(renderId);
    }
  }, []);

  // Resume polling untuk downloads yang ada saat component mount
  useEffect(() => {
    downloads.forEach((item, renderId) => {
      if (item.status === 'queued' || item.status === 'processing') {
        // Cek apakah sudah dipoll
        if (!pollIntervalsRef.current.has(renderId)) {
          startPolling(renderId);
        }
      }
    });
  }, [downloads, startPolling]);

  const addDownload = useCallback((item: Omit<DownloadItem, 'startedAt'>) => {
    setDownloads(prev => {
      const newMap = new Map(prev);
      newMap.set(item.renderId, { ...item, startedAt: Date.now() });
      return newMap;
    });
    
    // Start polling untuk render ini
    if (item.status === 'queued' || item.status === 'processing') {
      startPolling(item.renderId);
    }
  }, [startPolling]);

  const updateDownload = useCallback((renderId: string, updates: Partial<DownloadItem>) => {
    setDownloads(prev => {
      const newMap = new Map(prev);
      const existing = newMap.get(renderId);
      if (existing) {
        newMap.set(renderId, { ...existing, ...updates });
      }
      return newMap;
    });
  }, []);

  const removeDownload = useCallback((renderId: string) => {
    stopPolling(renderId);
    setDownloads(prev => {
      const newMap = new Map(prev);
      newMap.delete(renderId);
      return newMap;
    });
  }, [stopPolling]);

  const clearCompleted = useCallback(() => {
    setDownloads(prev => {
      const newMap = new Map(prev);
      Array.from(newMap.entries()).forEach(([key, item]) => {
        if (item.status === 'completed' || item.status === 'failed') {
          stopPolling(key);
          newMap.delete(key);
        }
      });
      return newMap;
    });
  }, [stopPolling]);

  // Cleanup semua polling saat unmount
  useEffect(() => {
    return () => {
      pollIntervalsRef.current.forEach(intervalId => clearInterval(intervalId));
      pollIntervalsRef.current.clear();
    };
  }, []);

  return (
    <DownloadContext.Provider value={{ downloads, addDownload, updateDownload, removeDownload, clearCompleted }}>
      {children}
    </DownloadContext.Provider>
  );
}

export function useDownloads() {
  const context = useContext(DownloadContext);
  if (!context) {
    throw new Error('useDownloads must be used within DownloadProvider');
  }
  return context;
}
