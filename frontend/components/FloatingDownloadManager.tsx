'use client';

import { useDownloads } from '@/contexts/DownloadContext';
import { Download, X, CheckCircle, Loader2, AlertCircle, Minimize2, Maximize2, Trash2, FileText, Share2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getApiUrl } from '@/lib/api';
import { toast } from 'react-hot-toast';

interface RenderFile {
  id: string;
  clipTitle: string;
  filename: string;
  created_at: string;
  filesize?: number;
}

export default function FloatingDownloadManager() {
  const { downloads, removeDownload, clearCompleted } = useDownloads();
  const [isMinimized, setIsMinimized] = useState(true);
  const [isHidden, setIsHidden] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<{ renderId: string; clipTitle: string; action: 'cancel' | 'delete' } | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [activeTab, setActiveTab] = useState<'current' | 'saved'>('current');
  const [savedFiles, setSavedFiles] = useState<RenderFile[]>([]);
  const [loadingSavedFiles, setLoadingSavedFiles] = useState(false);
  const API_URL = getApiUrl();

  // Load saved renders from API
  useEffect(() => {
    const loadSavedFiles = async () => {
      try {
        setLoadingSavedFiles(true);
        const res = await fetch(`${API_URL}/api/renders`);
        if (res.ok) {
          const data = await res.json();
          // Filter only completed/ready renders
          const files = data.filter((r: any) => (r.status === 'ready' || r.status === 'completed') && r.output_path)
            .map((r: any) => ({
              id: r.id,
              clipTitle: r.job_detail?.clip_title || 'Unknown',
              filename: r.output_path?.split('/').pop() || 'unknown',
              created_at: r.created_at,
              filesize: r.filesize
            }));
          setSavedFiles(files);
        }
      } catch (error) {
        console.error('Error loading saved files:', error);
      } finally {
        setLoadingSavedFiles(false);
      }
    };

    loadSavedFiles();
  }, [API_URL]);

  const downloadArray = Array.from(downloads.values());
  const activeDownloads = downloadArray.filter(d => 
    d.status !== 'completed' && d.status !== 'failed'
  );
  const completedDownloads = downloadArray.filter(d => 
    d.status === 'completed' || d.status === 'failed'
  );

  const handleDownload = (item: any) => {
    if (item.downloadUrl) {
      window.open(`${API_URL}${item.downloadUrl}`, '_blank');
    }
  };

  const handleDownloadSavedFile = (file: RenderFile) => {
    window.open(`${API_URL}/api/renders/${file.id}/download`, '_blank');
  };

  const sanitizeFilename = (name: string) =>
    name.replace(/[^a-z0-9._-]+/gi, '_').slice(0, 80) || 'clip';

  const shareVideoFile = async (url: string, filename: string, title: string) => {
    try {
      if (!navigator.share || !navigator.canShare) {
        toast.error('Share video tidak didukung di perangkat ini');
        return;
      }

      const res = await fetch(url);
      if (!res.ok) {
        toast.error('Gagal menyiapkan video untuk dibagikan');
        return;
      }

      const blob = await res.blob();
      const file = new File([blob], filename, { type: blob.type || 'video/mp4' });

      if (!navigator.canShare({ files: [file] })) {
        toast.error('Share video tidak didukung di perangkat ini');
        return;
      }

      await navigator.share({ title, files: [file] });
      toast.success('Video dibagikan');
    } catch (error) {
      console.error('Share error:', error);
      toast.error('Gagal membagikan video');
    }
  };

  const handleShare = (item: any) => {
    if (!item.downloadUrl) return;
    const url = `${API_URL}${item.downloadUrl}`;
    const filename = `${sanitizeFilename(item.clipTitle || 'clip')}.mp4`;
    shareVideoFile(url, filename, item.clipTitle || 'Clip');
  };

  const handleShareSavedFile = (file: RenderFile) => {
    const url = `${API_URL}/api/renders/${file.id}/download`;
    const filename = sanitizeFilename(file.filename || file.clipTitle || 'clip.mp4');
    shareVideoFile(url, filename, file.clipTitle || 'Clip');
  };

  const handleDeleteSavedFile = async (file: RenderFile) => {
    try {
      const res = await fetch(`${API_URL}/api/renders/${file.id}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to delete file');
        return;
      }

      setSavedFiles(prev => prev.filter(f => f.id !== file.id));
      toast.success('File dihapus');
    } catch (error) {
      console.error('Error:', error);
      toast.error('Terjadi kesalahan');
    }
  };

  const handleRemoveClick = (renderId: string, clipTitle: string, status: string) => {
    // Determine action based on status
    if (status === 'queued' || status === 'processing') {
      setConfirmDialog({ renderId, clipTitle, action: 'cancel' });
    } else if (status === 'ready' || status === 'completed' || status === 'failed') {
      setConfirmDialog({ renderId, clipTitle, action: 'delete' });
    }
  };

  const handleConfirmAction = async () => {
    if (!confirmDialog) return;

    setIsCancelling(true);
    try {
      if (confirmDialog.action === 'cancel') {
        // Cancel the render job
        const res = await fetch(`${API_URL}/api/renders/${confirmDialog.renderId}/cancel`, {
          method: 'POST'
        });
        
        if (!res.ok) {
          const err = await res.json();
          toast.error(err.detail || 'Failed to cancel render');
          setConfirmDialog(null);
          return;
        }

        removeDownload(confirmDialog.renderId);
        toast.success('Render dibatalkan');
      } else if (confirmDialog.action === 'delete') {
        // Delete the render file
        const res = await fetch(`${API_URL}/api/renders/${confirmDialog.renderId}`, {
          method: 'DELETE'
        });
        
        if (!res.ok) {
          const err = await res.json();
          toast.error(err.detail || 'Failed to delete file');
          setConfirmDialog(null);
          return;
        }

        removeDownload(confirmDialog.renderId);
        toast.success('File dihapus');
      }
      
      setConfirmDialog(null);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Terjadi kesalahan');
    } finally {
      setIsCancelling(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'queued':
        return <Loader2 className="w-4 h-4 animate-spin text-yellow-500" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'ready':
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Loader2 className="w-4 h-4 animate-spin text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'queued': return 'Antrian';
      case 'processing': return 'Proses';
      case 'ready': return 'Siap';
      case 'downloading': return 'Download';
      case 'completed': return 'Selesai';
      case 'failed': return 'Gagal';
      default: return status;
    }
  };

  if (isHidden) {
    return (
      <button
        onClick={() => setIsHidden(false)}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-2xl z-50 transition-all duration-300"
        title="Tampilkan Clip Manager"
      >
        <Download className="w-6 h-6" />
        {activeDownloads.length > 0 && (
          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">
            {activeDownloads.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <>
      <div className="fixed bottom-6 right-6 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl z-50 border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Download className="w-5 h-5" />
          <h3 className="font-semibold">Clip Manager</h3>
          {activeDownloads.length > 0 && (
            <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
              {activeDownloads.length} aktif
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {completedDownloads.length > 0 && (
            <button
              onClick={clearCompleted}
              className="hover:bg-white/20 p-1 rounded transition-colors"
              title="Hapus yang selesai"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
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

      {/* Tabs */}
      {!isMinimized && (
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('current')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'current'
                ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
            }`}
          >
            <span className="flex items-center justify-center gap-1">
              <Download className="w-4 h-4" />
              Current
              {activeDownloads.length > 0 && (
                <span className="bg-blue-600 text-white text-xs px-1.5 rounded-full">
                  {activeDownloads.length}
                </span>
              )}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'saved'
                ? 'border-b-2 border-blue-600 text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
            }`}
          >
            <span className="flex items-center justify-center gap-1">
              <FileText className="w-4 h-4" />
              Saved
              {savedFiles.length > 0 && (
                <span className="bg-green-600 text-white text-xs px-1.5 rounded-full">
                  {savedFiles.length}
                </span>
              )}
            </span>
          </button>
        </div>
      )}

      {/* Content */}
      {!isMinimized && (
        <div className="max-h-96 overflow-y-auto">
          {activeTab === 'current' ? (
            // Current Downloads
            <>
              {downloadArray.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Download className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Tidak ada download aktif</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {downloadArray.map((item) => (
                    <div
                      key={item.renderId}
                      className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {getStatusIcon(item.status)}
                            <p className="font-medium text-sm truncate text-gray-900 dark:text-white">
                              {item.clipTitle}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                            <span className="font-medium">{getStatusText(item.status)}</span>
                            {item.status === 'processing' && (
                              <span>• {item.progress}%</span>
                            )}
                          </div>
                          {item.error && (
                            <p className="text-xs text-red-500 mt-1">{item.error}</p>
                          )}
                          {/* Progress bar */}
                          {(item.status === 'processing' || item.status === 'queued') && (
                            <div className="mt-2 w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              <div
                                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                style={{ width: `${item.progress}%` }}
                              />
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {(item.status === 'ready' || item.status === 'completed') && item.downloadUrl && (
                            <button
                              onClick={() => handleDownload(item)}
                              className="bg-green-600 hover:bg-green-700 text-white p-2 rounded transition-colors"
                              title="Download"
                            >
                              <Download className="w-4 h-4" />
                            </button>
                          )}
                          {(item.status === 'ready' || item.status === 'completed') && item.downloadUrl && (
                            <button
                              onClick={() => handleShare(item)}
                              className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded transition-colors"
                              title="Share"
                            >
                              <Share2 className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleRemoveClick(item.renderId, item.clipTitle, item.status)}
                            className="hover:bg-gray-200 dark:hover:bg-gray-600 p-2 rounded transition-colors text-gray-600 dark:text-gray-300"
                            title={['queued', 'processing'].includes(item.status) ? 'Batalkan' : 'Hapus'}
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            // Saved Files
            <>
              {loadingSavedFiles ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-6 h-6 mx-auto mb-2 animate-spin text-gray-500" />
                  <p className="text-sm text-gray-500">Loading files...</p>
                </div>
              ) : savedFiles.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Tidak ada file yang tersimpan</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {savedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                            <p className="font-medium text-sm truncate text-gray-900 dark:text-white">
                              {file.clipTitle}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                            <span>{file.filename}</span>
                            {file.filesize && (
                              <>
                                <span>•</span>
                                <span>{(file.filesize / (1024 * 1024)).toFixed(2)} MB</span>
                              </>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            {new Date(file.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleDownloadSavedFile(file)}
                            className="bg-green-600 hover:bg-green-700 text-white p-2 rounded transition-colors"
                            title="Download"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleShareSavedFile(file)}
                            className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded transition-colors"
                            title="Share"
                          >
                            <Share2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteSavedFile(file)}
                            className="hover:bg-gray-200 dark:hover:bg-gray-600 p-2 rounded transition-colors text-gray-600 dark:text-gray-300"
                            title="Hapus"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>

    {/* Confirm Dialog */}
    {confirmDialog && (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6 max-w-sm mx-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {confirmDialog.action === 'cancel' ? 'Batalkan Download?' : 'Hapus File?'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {confirmDialog.action === 'cancel' 
              ? `Anda ingin membatalkan render untuk "${confirmDialog.clipTitle}"?`
              : `Anda ingin menghapus file "${confirmDialog.clipTitle}"? Tindakan ini tidak bisa dibatalkan.`
            }
          </p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setConfirmDialog(null)}
              disabled={isCancelling}
              className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors disabled:opacity-50"
            >
              Batal
            </button>
            <button
              onClick={handleConfirmAction}
              disabled={isCancelling}
              className={`px-4 py-2 rounded-lg text-white font-medium flex items-center gap-2 transition-colors disabled:opacity-50 ${
                confirmDialog.action === 'cancel'
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {isCancelling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Memproses...
                </>
              ) : (
                confirmDialog.action === 'cancel' ? 'Batalkan' : 'Hapus'
              )}
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}