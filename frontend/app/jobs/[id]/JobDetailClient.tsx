'use client';

import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { 
  ArrowLeft, Play, CheckCircle2, Clock, AlertCircle, 
  Settings2, Download, Check, X, Wand2, FileText, 
  ScanFace, Share2, MoreVertical, Loader2, Youtube, FileVideo,
  ChevronLeft, ChevronRight, Users, Copy, Hash
} from 'lucide-react';
import { getApiUrl, getApiEndpoint } from '@/lib/api';
import Breadcrumb from '@/components/Breadcrumb';
import { SkeletonClipGrid } from '@/components/Skeleton';
import { useDownloads } from '@/contexts/DownloadContext';

interface Job {
  id: string;
  status: string;
  step: string;
  progress: number;
  error?: string;
  source_type: string;
  source_url?: string;
}

interface Clip {
  id: string;
  start_sec: number;
  end_sec: number;
  score: number;
  title: string;
  transcript_snippet: string;
  caption_text?: string;
  hashtags_text?: string;
}

interface Render {
  id: string;
  status: string;
  progress: number;
  output_path?: string;
  error?: string;
  clip_id?: string;
}

interface NewClip {
  start_sec: string;
  end_sec: string;
  title: string;
}

interface JobDetailClientProps {
  jobId?: string;
  params?: { id: string };
}

export default function JobDetailPage({ jobId: propJobId, params }: JobDetailClientProps) {
  const API_URL = getApiUrl();
  const { addDownload, updateDownload } = useDownloads();
  
  // Extract jobId from multiple sources
  const [jobId, setJobId] = useState<string | null>(propJobId || null);
  
  useEffect(() => {
    // Priority 1: Direct prop
    if (propJobId) {
      setJobId(propJobId);
      return;
    }
    
    // Priority 2: Params from Next.js
    if (params?.id && params.id !== 'placeholder') {
      setJobId(params.id);
      return;
    }
    
    // Priority 3: Extract from pathname
    const pathMatch = window.location.pathname.match(/\/jobs\/([^/?]+)/);
    if (pathMatch && pathMatch[1] && pathMatch[1] !== 'placeholder') {
      setJobId(pathMatch[1]);
      return;
    }
    
    // Priority 4: Query string
    const urlParams = new URLSearchParams(window.location.search);
    const jobIdFromQuery = urlParams.get('jobId');
    if (jobIdFromQuery) {
      setJobId(jobIdFromQuery);
      return;
    }
    
    console.error('[JobDetail] Could not extract jobId');
  }, [propJobId, params]);
  
  // Early return if jobId not available
  if (!jobId) {
    return (
      <div className="min-h-screen bg-[#0A0B0F] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading job details...</p>
        </div>
      </div>
    );
  }
  
  
  const [job, setJob] = useState<Job | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [selectedClips, setSelectedClips] = useState<Set<string>>(new Set());
  const [previewClipId, setPreviewClipId] = useState<string | null>(null);
  const [previewLoadedByClipId, setPreviewLoadedByClipId] = useState<Record<string, boolean>>({});
  const [previewError, setPreviewError] = useState<Record<string, string>>({});
  const [faceTracking, setFaceTracking] = useState(true);
  const [smartCrop, setSmartCrop] = useState(false);
  const [captions, setCaptions] = useState(false);
  const [watermarkText, setWatermarkText] = useState("");
  const [rendering, setRendering] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // State untuk mencegah spam tombol render satuan
  const [isSubmittingSingle, setIsSubmittingSingle] = useState(false);
  
  const [renders, setRenders] = useState<Record<string, Render>>({});
  const [autoDownloadQueue, setAutoDownloadQueue] = useState<Set<string>>(new Set());

  // AI Caption generation state
  const [generatingCaption, setGeneratingCaption] = useState<string | null>(null);
  const [generatedCaptions, setGeneratedCaptions] = useState<Record<string, string>>({});
  const [generatedHashtags, setGeneratedHashtags] = useState<Record<string, string>>({});
  const [captionStyle, setCaptionStyle] = useState<string>("engaging");

  const getRenderForClip = (clipId: string) => {
    return Object.values(renders).find(r => r && r.clip_id === clipId);
  };

  const isRenderBlocked = (clipId: string) => {
    const status = getRenderForClip(clipId)?.status;
    return status === 'queued' || status === 'processing' || status === 'ready';
  };

  // State for batch create clips
  const [batchClips, setBatchClips] = useState<NewClip[]>([{ start_sec: '', end_sec: '', title: '' }]);
  const [batchLoading, setBatchLoading] = useState(false);

  const handleBatchClipChange = (idx: number, field: keyof NewClip, value: string) => {
    setBatchClips(prev => prev.map((clip, i) => i === idx ? { ...clip, [field]: value } : clip));
  };
  const addBatchClipRow = () => setBatchClips(prev => [...prev, { start_sec: '', end_sec: '', title: '' }]);
  const removeBatchClipRow = (idx: number) => setBatchClips(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev);

  const submitBatchClips = async () => {
    setBatchLoading(true);
    try {
      const clipsPayload = batchClips
        .filter(c => c.start_sec && c.end_sec)
        .map(c => ({
          start_sec: parseFloat(c.start_sec),
          end_sec: parseFloat(c.end_sec),
          title: c.title || `Clip ${c.start_sec}-${c.end_sec}`
        }));
      if (clipsPayload.length === 0) {
        toast.error('Please fill at least one valid clip row');
        return;
      }
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/clips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clips: clipsPayload })
      });
      if (res.ok) {
        setBatchClips([{ start_sec: '', end_sec: '', title: '' }]);
        // Refresh clips
        fetch(`${API_URL}/api/jobs/${jobId}/clips`).then(r => r.json()).then(data => setClips(data.clips || []));
        toast.success('Clips created successfully!');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to create clips');
      }
    } catch (e) {
      console.error(e);
      toast.error('Error creating clips');
    } finally {
      setBatchLoading(false);
    }
  };

  // State for regenerate highlights
  const [regenerating, setRegenerating] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateClipCount, setRegenerateClipCount] = useState<string>('');

  // State for filters and sorting
  const [sortBy, setSortBy] = useState<'score' | 'duration' | 'time'>('score');
  const [minScore, setMinScore] = useState<number>(0);
  const [showFilters, setShowFilters] = useState(false);

  // Filter and sort clips
  const filteredAndSortedClips = clips
    .filter(clip => clip.score >= minScore)
    .sort((a, b) => {
      if (sortBy === 'score') return b.score - a.score;
      if (sortBy === 'duration') return (b.end_sec - b.start_sec) - (a.end_sec - a.start_sec);
      if (sortBy === 'time') return a.start_sec - b.start_sec;
      return 0;
    });

  const regenerateHighlights = async () => {
    if (regenerating) return;
    
    // Validate clip count if provided
    let clipCount = null;
    if (regenerateClipCount) {
      clipCount = parseInt(regenerateClipCount, 10);
      if (isNaN(clipCount) || clipCount < 5 || clipCount > 50) {
        toast.error('Please enter a valid clip count between 5 and 50');
        return;
      }
    }
    
    setRegenerating(true);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/regenerate-highlights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clip_count: clipCount,
          adaptive: true
        })
      });
      
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to regenerate highlights');
        return;
      }
      
      const data = await res.json();
      toast.success(`Regenerated ${data.created} highlights!`);
      
      // Refresh clips
      const clipsRes = await fetch(`${API_URL}/api/jobs/${jobId}/clips`);
      const clipsData = await clipsRes.json();
      setClips(clipsData.clips || []);
      setSelectedClips(new Set());
      setShowRegenerateModal(false);
      setRegenerateClipCount('');
    } catch (error) {
      console.error('Regenerate error:', error);
      toast.error('Error regenerating highlights');
    } finally {
      setRegenerating(false);
    }
  };


  // Fetch job (Real Logic)
  useEffect(() => {
    const fetchJob = async () => {
      try {
        const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
        
        if (!res.ok) {
          console.error('[JobDetail] Failed to fetch job:', res.status, res.statusText);
          setError(`Failed to load job: ${res.status} ${res.statusText}`);
          setLoading(false);
          return;
        }
        
        const data = await res.json();
        setJob(data);
        setError(null);
        setLoading(false);
      } catch (error) {
        console.error("[JobDetail] Error fetching job:", error);
        setError(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        setLoading(false);
      }
    };
    
    fetchJob();
    const interval = setInterval(fetchJob, 2000);
    return () => clearInterval(interval);
  }, [jobId, API_URL]);

  // Fetch clips when job is ready (Real Logic)
  useEffect(() => {
    if (job?.status === 'ready') {
      fetch(`${API_URL}/api/jobs/${jobId}/clips`)
        .then(res => res.json())
        .then(data => setClips(data.clips || []))
        .catch(err => console.error("Error fetching clips:", err));
    }
  }, [job?.status, jobId]);

  useEffect(() => {
    if (job?.status === 'ready') {
      fetch(`${API_URL}/api/jobs/${jobId}/renders`)
        .then(res => res.json())
        .then(data => {
          const list = data.renders || [];
          const map: Record<string, Render> = {};
          for (const r of list) {
            map[r.id] = r;
          }
          setRenders(map);
        })
        .catch(err => console.error("Error fetching renders:", err));
    }
  }, [job?.status, jobId]);

  // Track previous job status to avoid duplicate toasts
  const prevStatus = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!job) return;
    if (job.status !== prevStatus.current) {
      if (job.status === "ready") toast.success("Job finished!");
      if (job.status === "failed") toast.error("Job failed");
      if (job.status === "cancelled") toast.success("Job cancelled");
      prevStatus.current = job.status;
    }
  }, [job?.status]);

  useEffect(() => {
    if (!previewClipId) return;
    setPreviewLoadedByClipId(prev => ({ ...prev, [previewClipId]: false }));
  }, [previewClipId]);

  const toggleClipSelection = (clipId: string) => {
    setSelectedClips(prev => {
      const newSet = new Set(prev);
      if (newSet.has(clipId)) {
        newSet.delete(clipId);
      } else {
        newSet.add(clipId);
      }
      return newSet;
    });
  };

  const selectAllClips = () => {
    setSelectedClips(new Set(clips.map(c => c.id)));
  };

  const deselectAllClips = () => {
    setSelectedClips(new Set());
  };

  const renderSelectedClips = async () => {
    if (selectedClips.size === 0 || rendering) return; // Prevent spam

    const blocked = new Set(
      Object.values(renders)
        .filter(r => r && (r.status === 'queued' || r.status === 'processing' || r.status === 'ready'))
        .map(r => r.clip_id)
        .filter(Boolean) as string[]
    );
    const eligibleClipIds = Array.from(selectedClips).filter(id => !blocked.has(id));

    if (eligibleClipIds.length === 0) {
      toast.error('Semua highlight sudah dirender atau sedang diproses.');
      return;
    }

    setRendering(true);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/render-selected?${new URLSearchParams({
        clip_ids: eligibleClipIds.join(',')
      })}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          face_tracking: faceTracking,
          smart_crop: smartCrop,
          captions: captions,
          watermark_text: watermarkText
        })
      });
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to start rendering');
        return;
      }
      const data = await res.json();
      for (const renderId of data.render_ids) {
        // Find corresponding clip
        const clipIndex = data.render_ids.indexOf(renderId);
        const clipId = eligibleClipIds[clipIndex];
        const clip = clips.find(c => c.id === clipId);
        
        // Add to download manager
        addDownload({
          id: renderId,
          renderId,
          clipTitle: clip?.title || `Clip ${clipIndex + 1}`,
          jobId,
          status: 'queued',
          progress: 0,
        });
      }
      if (data.skipped?.length) {
        toast.success(`Render ${data.render_ids.length} clip dimulai, ${data.skipped.length} dilewati.`);
      } else {
        toast.success(`Rendering ${data.render_ids.length} clips started!`);
      }
    } catch (error) {
      console.error('Render error:', error);
      toast.error('Error starting render');
    } finally {
      setTimeout(() => setRendering(false), 3000);
    }
  };

  const pollRenderStatus = async (renderId: string, autoDownload = false) => {
    let notified = false;
    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/api/renders/${renderId}`);
        const render = await res.json();
        setRenders(prev => ({ ...prev, [renderId]: render }));
        
        // Update download manager
        updateDownload(renderId, {
          status: render.status,
          progress: render.progress || 0,
          error: render.error,
          downloadUrl: render.output_path ? `/api/renders/${renderId}/download` : undefined,
        });
        
        if ((render.status === 'ready' || render.status === 'failed' || render.status === 'cancelled') && !notified) {
          notified = true;
          
          if (render.status === 'ready') {
            toast.success('Render finished!');
            
            // Auto-download jika diminta
            if (autoDownload && render.output_path) {
              setTimeout(() => {
                const downloadUrl = `${API_URL}/api/renders/${renderId}/download`;
                toast.success('Starting download...');
                window.open(downloadUrl, '_blank');
                
                // Cleanup setelah 3 detik
                setTimeout(() => {
                  toast.success('Cleaning up...');
                  fetch(`${API_URL}/api/renders/${renderId}`, { method: 'DELETE' })
                    .then(() => {
                      setRenders(prev => {
                        const newRenders = { ...prev };
                        delete newRenders[renderId];
                        return newRenders;
                      });
                      setAutoDownloadQueue(prev => {
                        const newQueue = new Set(prev);
                        newQueue.delete(renderId);
                        return newQueue;
                      });
                      toast.success('Render cleaned up!');
                    })
                    .catch(err => {
                      console.error('Cleanup error:', err);
                      toast.error('Failed to clean up');
                    });
                }, 3000);
              }, 500);
            }
          } else if (render.status === 'failed') {
            toast.error('Render failed.');
            setAutoDownloadQueue(prev => {
              const newQueue = new Set(prev);
              newQueue.delete(renderId);
              return newQueue;
            });
          } else if (render.status === 'cancelled') {
            toast.success('Render cancelled!');
            setAutoDownloadQueue(prev => {
              const newQueue = new Set(prev);
              newQueue.delete(renderId);
              return newQueue;
            });
          }
        }
        
        if (render.status !== 'ready' && render.status !== 'failed' && render.status !== 'cancelled') {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error("Polling error", error);
      }
    };
    poll();
  };

  const handleCancelJob = async () => {
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/cancel`, {
        method: 'POST'
      });

      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to cancel job');
        return;
      }

      toast.success('Job cancelled');
      const jobRes = await fetch(`${API_URL}/api/jobs/${jobId}`);
      const jobData = await jobRes.json();
      setJob(jobData);
    } catch (error) {
      console.error('Cancel job error:', error);
      toast.error('Error cancelling job');
    }
  };

  const handleCancelRender = async (renderId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/renders/${renderId}/cancel`, {
        method: 'POST'
      });
      
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to cancel render');
        return;
      }
      
      toast.success('Render cancelled!');
      setAutoDownloadQueue(prev => {
        const newQueue = new Set(prev);
        newQueue.delete(renderId);
        return newQueue;
      });
      
      // Refresh render status
      const renderRes = await fetch(`${API_URL}/api/renders/${renderId}`);
      const render = await renderRes.json();
      setRenders(prev => ({ ...prev, [renderId]: render }));
    } catch (error) {
      console.error('Cancel render error:', error);
      toast.error('Error cancelling render');
    }
  };

  const handleDeleteRender = async (renderId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/renders/${renderId}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || 'Failed to delete render');
        return;
      }
      
      toast.success('Render deleted!');
      setRenders(prev => {
        const newRenders = { ...prev };
        delete newRenders[renderId];
        return newRenders;
      });
    } catch (error) {
      console.error('Delete render error:', error);
      toast.error('Error deleting render');
    }
  };

  const handleGenerateCaption = async (clipId: string) => {
    if (generatingCaption === clipId) return;
    
    setGeneratingCaption(clipId);
    try {
      // Generate caption
      const captionRes = await fetch(`${API_URL}/api/clips/${clipId}/generate-caption?style=${captionStyle}&max_length=150`, {
        method: 'POST'
      });
      
      if (!captionRes.ok) {
        const err = await captionRes.json();
        toast.error(err.detail || 'Failed to generate caption');
        return;
      }
      
      const captionData = await captionRes.json();
      setGeneratedCaptions(prev => ({ ...prev, [clipId]: captionData.caption }));
      
      // Generate hashtags bersamaan
      const hashtagRes = await fetch(`${API_URL}/api/clips/${clipId}/generate-hashtags?count=10`, {
        method: 'POST'
      });
      
      if (hashtagRes.ok) {
        const hashtagData = await hashtagRes.json();
        setGeneratedHashtags(prev => ({ ...prev, [clipId]: hashtagData.hashtags }));
      }
      
      toast.success('Caption & hashtags generated!');
    } catch (error) {
      console.error('Generate caption/hashtags error:', error);
      toast.error('Error generating caption & hashtags');
    } finally {
      setGeneratingCaption(null);
    }
  };

  const handleCopyCaption = (caption: string) => {
    navigator.clipboard.writeText(caption);
    toast.success('Caption copied to clipboard!');
  };

  const eligibleSelectedCount = Array.from(selectedClips).filter(id => !isRenderBlocked(id)).length;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 9) return 'bg-emerald-500 text-white shadow-[0_0_10px_rgba(16,185,129,0.4)]';
    if (score >= 7) return 'bg-blue-500 text-white';
    return 'bg-amber-500 text-white';
  };

  if (!jobId) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4">
          <AlertCircle className="w-12 h-12 text-amber-500" />
          <p className="text-amber-400 font-medium">Job ID tidak ditemukan.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <AlertCircle className="w-16 h-16 text-red-500" />
          <p className="text-red-400 font-semibold text-xl">Error Loading Job</p>
          <p className="text-slate-400">{error}</p>
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => window.location.href = '/jobs'}
              className="px-6 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition"
            >
              Back to Jobs
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (loading || !job) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-emerald-500 animate-spin" />
          <p className="text-emerald-400 font-medium animate-pulse">Loading Job Data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-emerald-500/30 relative overflow-x-hidden">
      {/* Background Ambient Effects */}
      <div className="absolute top-0 left-0 w-[600px] h-[600px] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-teal-600/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      <div className="relative z-10 max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
        
        {/* Breadcrumb */}
        <Breadcrumb items={[
          { label: 'Jobs', href: '/jobs' },
          { label: `Job #${job.id.slice(0, 8)}` }
        ]} />
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 sm:gap-6 mb-6 sm:mb-10">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
                Job Details <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">#{job.id.slice(0, 8)}</span>
              </h1>
              <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                 job.status === 'ready' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                 job.status === 'processing' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 
                 'bg-red-500/10 text-red-400 border-red-500/20'
              }`}>
                {job.status}
              </div>
            </div>
            {job.step && <p className="text-slate-500 text-sm mt-1">Current Step: {job.step.replace('_', ' ')}</p>}
          </div>
          
          <div className="flex items-center gap-4 bg-slate-900/60 backdrop-blur-md p-2 rounded-xl border border-white/5">
            <div className="px-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Source</p>
              <div className="flex items-center gap-2 text-white">
                {job.source_type === 'youtube' ? <Youtube size={14} /> : <FileVideo size={14} />}
                <span className="text-sm font-medium truncate max-w-[200px]">{job.source_type}</span>
              </div>
            </div>
          </div>
        </div>
        {/* S3 Upload Link */}
        {/* S3 Upload Link */}

        {job && (job as any).s3_url && (
          <div className="mt-2">
            <a href={(job as any).s3_url} target="_blank" rel="noopener noreferrer" className="text-emerald-400 underline text-sm">Uploaded Video (S3)</a>
          </div>
        )}

        {/* Job Processing State with Modern Progress Bar */}
        {['processing', 'queued'].includes(job.status) && (
          <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-8 mb-8 text-center backdrop-blur-sm">
            <div className="max-w-md mx-auto">
               <div className="flex justify-between text-sm font-medium mb-2">
                 <span className="text-blue-400 flex items-center gap-2"><Loader2 size={14} className="animate-spin" /> Processing...</span>
                 <span className="text-white">{job.progress}%</span>
               </div>
               <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <div className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-300" style={{ width: `${job.progress}%` }} />
               </div>
               <button
                 onClick={handleCancelJob}
                 className="mt-4 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold transition-colors"
               >
                 Cancel Job
               </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {job.error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-2xl mb-8 flex items-center gap-4 backdrop-blur-sm">
            <AlertCircle size={24} className="shrink-0" />
            <div>
              <h3 className="font-bold">Error Occurred</h3>
              <p className="text-sm opacity-90">{job.error}</p>
            </div>
          </div>
        )}

        {/* Batch Create Clips Form */}
        {job.status === 'ready' && (
          <div className="mb-6 sm:mb-10 bg-slate-900/70 border border-white/10 rounded-2xl p-4 sm:p-6">
            <h2 className="text-lg font-bold mb-4 text-white">Batch Create Clips</h2>
            <div className="space-y-2 sm:space-y-3">
              {batchClips.map((clip, idx) => (
                <div key={idx} className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
                  <input type="number" step="0.01" min="0" placeholder="Start (sec)" aria-label="Clip start time in seconds" value={clip.start_sec} onChange={e => handleBatchClipChange(idx, 'start_sec', e.target.value)} className="px-2 py-1 rounded bg-slate-800 text-white w-24" />
                  <input type="number" step="0.01" min="0" placeholder="End (sec)" aria-label="Clip end time in seconds" value={clip.end_sec} onChange={e => handleBatchClipChange(idx, 'end_sec', e.target.value)} className="px-2 py-1 rounded bg-slate-800 text-white w-24" />
                  <input type="text" placeholder="Title (optional)" aria-label="Clip title" value={clip.title} onChange={e => handleBatchClipChange(idx, 'title', e.target.value)} className="px-2 py-1 rounded bg-slate-800 text-white flex-1" />
                  <button onClick={() => removeBatchClipRow(idx)} className="text-red-400 px-2 py-1 rounded hover:bg-red-900/30" aria-label="Remove clip row">Remove</button>
                </div>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-2 mt-4">
              <button onClick={addBatchClipRow} className="bg-emerald-700 hover:bg-emerald-600 text-white px-4 py-2 rounded font-bold" aria-label="Add new clip row">Add Row</button>
              <button onClick={submitBatchClips} disabled={batchLoading} className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-2 rounded font-bold disabled:opacity-60" aria-label="Save all clips">{batchLoading ? 'Saving...' : 'Save Clips'}</button>
            </div>
          </div>
        )}

        {/* Regenerate Highlights Section */}
        {job.status === 'ready' && (
          <div className="mb-6 sm:mb-10 bg-gradient-to-br from-slate-900/70 to-slate-800/50 border border-white/10 rounded-2xl p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold mb-2 text-white flex items-center gap-2">
                  <Wand2 size={20} className="text-emerald-400" />
                  Regenerate Highlights
                </h2>
                <p className="text-sm text-slate-400">
                  Generate new highlight clips with custom parameters. Current: {clips.length} clips
                </p>
              </div>
              <button
                onClick={() => setShowRegenerateModal(true)}
                className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white px-6 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all shadow-lg"
              >
                <Wand2 size={16} />
                Regenerate
              </button>
            </div>
          </div>
        )}

        {/* Regenerate Modal */}
        {showRegenerateModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowRegenerateModal(false)}>
            <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Wand2 size={20} className="text-emerald-400" />
                Regenerate Highlights
              </h3>
              <p className="text-sm text-slate-400 mb-6">
                This will delete all existing clips and generate new ones. This action cannot be undone.
              </p>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Number of clips (leave empty for auto)
                </label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  placeholder="Auto (based on video length)"
                  value={regenerateClipCount}
                  onChange={(e) => setRegenerateClipCount(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg bg-slate-800 text-white border border-white/10 focus:border-emerald-500 focus:outline-none"
                />
                <p className="text-xs text-slate-500 mt-2">
                  Auto: 5-50 clips based on video duration
                </p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowRegenerateModal(false)}
                  className="flex-1 px-4 py-2 rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition-colors"
                  disabled={regenerating}
                >
                  Cancel
                </button>
                <button
                  onClick={regenerateHighlights}
                  disabled={regenerating}
                  className="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold hover:from-emerald-500 hover:to-teal-500 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {regenerating ? (
                    <>
                      <Loader2 className="animate-spin" size={16} />
                      Generating...
                    </>
                  ) : (
                    'Generate'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        {job.status === 'ready' && clips.length > 0 && (
          <>
            {/* Preview Player Section */}
            {previewClipId && (() => {
               const activeClip = clips.find(c => c.id === previewClipId);
               if (!activeClip) return null;
               const currentIndex = clips.findIndex(c => c.id === previewClipId);
               
               return (
                <div className="mb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl shadow-black/50">
                    <div className="flex flex-col lg:flex-row h-full">
                      
                      {/* Video Player - Left Side */}
                      <div className="lg:w-1/3 bg-black flex items-center justify-center p-6 relative group">
                        <div className="relative aspect-[9/16] h-[500px] rounded-xl overflow-hidden shadow-2xl border border-white/5 bg-slate-800">
                           {/* REAL VIDEO PLAYER RESTORED */}
                           <video
                             key={previewClipId + faceTracking + captions} // Force remount on setting change
                             controls
                             autoPlay
                             className="w-full h-full object-cover"
                             onLoadedData={() => {
                               setPreviewLoadedByClipId(prev => ({ ...prev, [previewClipId]: true }));
                               setPreviewError(prev => {
                                 const newErrors = { ...prev };
                                 delete newErrors[previewClipId];
                                 return newErrors;
                               });
                             }}
                             onError={(e) => {
                               console.error('[Preview] Video error for clip:', previewClipId);
                               console.error('[Preview] Video source:', `${API_URL}/api/clips/${previewClipId}/preview?face_tracking=${faceTracking}`);
                               setPreviewLoadedByClipId(prev => ({ ...prev, [previewClipId]: false }));
                               setPreviewError(prev => ({ 
                                 ...prev, 
                                 [previewClipId]: 'Failed to load video preview' 
                               }));
                             }}
                           >
                             <source
                               src={`${API_URL}/api/clips/${previewClipId}/preview?face_tracking=${faceTracking}`}
                               type="video/mp4"
                             />
                             Your browser does not support the video tag.
                           </video>
                           
                           {/* Error Overlay */}
                           {previewError[previewClipId] && (
                             <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90">
                               <div className="text-center p-6">
                                 <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                                 <p className="text-red-400 font-medium mb-2">Video Preview Error</p>
                                 <p className="text-slate-400 text-sm mb-4">{previewError[previewClipId]}</p>
                                 <button 
                                   onClick={() => {
                                     setPreviewError(prev => {
                                       const newErrors = { ...prev };
                                       delete newErrors[previewClipId];
                                       return newErrors;
                                     });
                                   }}
                                   className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm transition-colors"
                                 >
                                   Retry
                                 </button>
                               </div>
                             </div>
                           )}
                           
                           {/* Loading State */}
                           {!previewLoadedByClipId[previewClipId] && !previewError[previewClipId] && (
                             <div className="absolute inset-0 flex items-center justify-center bg-slate-800">
                               <div className="text-center">
                                 <Loader2 className="w-12 h-12 text-blue-400 mx-auto mb-4 animate-spin" />
                                 <p className="text-slate-400 text-sm">Loading preview...</p>
                               </div>
                             </div>
                           )}
                        </div>
                      </div>

                      {/* Info Panel - Right Side */}
                      <div className="lg:w-2/3 p-8 flex flex-col">
                        <div className="flex justify-between items-start mb-6">
                           <div>
                             <h2 className="text-2xl font-bold text-white mb-2">{activeClip.title}</h2>
                             <div className="flex items-center gap-3 text-sm">
                               <span className={`px-2 py-0.5 rounded text-white font-bold text-xs ${getScoreColor(activeClip.score)}`}>
                                 Score: {activeClip.score.toFixed(1)}
                               </span>
                               <span className="flex items-center gap-1 text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                                 <Clock size={12} />
                                 {formatTime(activeClip.end_sec - activeClip.start_sec)}
                               </span>
                             </div>
                           </div>
                           <button 
                             onClick={() => setPreviewClipId(null)}
                             className="p-2 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                           >
                             <X size={24} />
                           </button>
                        </div>

                        {/* Transcript */}
                        <div className="bg-slate-800/50 rounded-xl p-5 mb-6 border border-white/5 flex-1 overflow-y-auto max-h-[200px]">
                           <h4 className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-3 flex items-center gap-2">
                             <FileText size={14} /> Transcript Snippet
                           </h4>
                           <p className="text-slate-300 leading-relaxed text-lg font-light">
                             "{activeClip.transcript_snippet}"
                           </p>
                        </div>

                        {/* Caption & Hashtags Panel */}
                        <div className="bg-gradient-to-br from-emerald-900/20 to-blue-900/20 rounded-xl p-5 mb-6 border border-emerald-500/20 space-y-4">
                          {/* AI Caption Generator */}
                          <div>
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="text-xs uppercase tracking-wider text-emerald-400 font-semibold flex items-center gap-2">
                                <FileText size={14} /> AI Caption Generator
                              </h4>
                              <div className="flex items-center gap-2">
                                <select
                                  value={captionStyle}
                                  onChange={(e) => setCaptionStyle(e.target.value)}
                                  className="px-2 py-1 bg-slate-800 text-white text-xs rounded-lg border border-white/10 focus:border-emerald-500 focus:outline-none"
                                >
                                  <option value="engaging">Engaging</option>
                                  <option value="professional">Professional</option>
                                  <option value="casual">Casual</option>
                                  <option value="funny">Funny</option>
                                  <option value="viral">Viral</option>
                                </select>
                                <button
                                  onClick={() => handleGenerateCaption(activeClip.id)}
                                  disabled={generatingCaption === activeClip.id}
                                  className="px-3 py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-lg text-white text-xs font-medium flex items-center gap-1.5 transition-all disabled:opacity-50"
                                >
                                  {generatingCaption === activeClip.id ? (
                                    <>
                                      <Loader2 size={12} className="animate-spin" /> Generating...
                                    </>
                                  ) : (
                                    <>
                                      <Wand2 size={12} /> Generate
                                    </>
                                  )}
                                </button>
                              </div>
                            </div>
                            
                            {generatedCaptions[activeClip.id] && (
                              <div className="space-y-3">
                                {/* Caption Display */}
                                <div className="relative bg-slate-900/50 rounded-lg p-4 border border-emerald-500/20">
                                  <p className="text-slate-200 leading-relaxed text-sm whitespace-pre-line mb-3">
                                    {generatedCaptions[activeClip.id]}
                                  </p>
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={() => handleCopyCaption(generatedCaptions[activeClip.id])}
                                      className="px-3 py-1.5 bg-emerald-700/50 hover:bg-emerald-600/70 rounded-lg text-emerald-100 text-xs font-medium flex items-center gap-1.5 transition-colors"
                                    >
                                      <Copy size={12} /> Copy
                                    </button>
                                    <button
                                      onClick={() => handleGenerateCaption(activeClip.id)}
                                      className="px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600/70 rounded-lg text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors"
                                    >
                                      <Wand2 size={12} /> Regenerate
                                    </button>
                                  </div>
                                </div>

                                {/* Hashtags Display */}
                                {generatedHashtags[activeClip.id] && (
                                  <div className="relative bg-slate-900/50 rounded-lg p-4 border border-blue-500/20">
                                    <p className="text-slate-200 text-sm break-words">
                                      {generatedHashtags[activeClip.id]}
                                    </p>
                                    <div className="flex items-center gap-2 mt-3">
                                      <button
                                        onClick={() => {
                                          navigator.clipboard.writeText(generatedHashtags[activeClip.id]);
                                          toast.success('Hashtags copied!');
                                        }}
                                        className="px-3 py-1.5 bg-blue-700/50 hover:bg-blue-600/70 rounded-lg text-blue-100 text-xs font-medium flex items-center gap-1.5 transition-colors"
                                      >
                                        <Copy size={12} /> Copy
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                            
                            {!generatedCaptions[activeClip.id] && generatingCaption !== activeClip.id && (
                              <p className="text-slate-500 text-xs italic">
                                Click "Generate" to create an AI-powered caption for social media
                              </p>
                            )}
                          </div>

                          {/* Original Caption Section (if exists) */}
                          {activeClip.caption_text && (
                            <div className="pt-4 border-t border-white/5">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="text-xs uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-2">
                                  <FileText size={14} /> Original Caption
                                </h4>
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(activeClip.caption_text || '');
                                    toast.success('Caption copied to clipboard!');
                                  }}
                                  className="px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600/70 rounded-lg text-slate-100 text-xs font-medium flex items-center gap-1.5 transition-colors"
                                >
                                  <Copy size={12} /> Copy
                                </button>
                              </div>
                              <p className="text-slate-300 leading-relaxed text-sm whitespace-pre-line">
                                {activeClip.caption_text}
                              </p>
                            </div>
                          )}

                          {/* Hashtags Section */}
                          {activeClip.hashtags_text && (
                            <div className="pt-4 border-t border-white/5">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="text-xs uppercase tracking-wider text-blue-400 font-semibold flex items-center gap-2">
                                  <Hash size={14} /> Hashtags
                                </h4>
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(activeClip.hashtags_text || '');
                                    toast.success('Hashtags copied to clipboard!');
                                  }}
                                  className="px-3 py-1.5 bg-blue-700/50 hover:bg-blue-600/70 rounded-lg text-blue-100 text-xs font-medium flex items-center gap-1.5 transition-colors"
                                >
                                  <Copy size={12} /> Copy Hashtags
                                </button>
                              </div>
                              <p className="text-blue-200 leading-relaxed text-sm font-medium">
                                {activeClip.hashtags_text}
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Action Bar inside Preview */}
                        <div className="mt-auto border-t border-white/5 pt-6 flex flex-wrap items-center justify-between gap-4">
                           <div className="flex items-center gap-3">
                              {(() => {
                                const renderStatus = getRenderForClip(activeClip.id)?.status;
                                const renderRecord = getRenderForClip(activeClip.id);
                                
                                // 1 KLIK untuk semua: Render -> Auto-download -> Cleanup
                                const handleRenderOrDownload = async () => {
                                  // Cek apakah sudah ada render yang ready, langsung download + cleanup
                                  if (renderStatus === 'ready' && renderRecord?.id) {
                                    const downloadUrl = `${API_URL}/api/renders/${renderRecord.id}/download`;
                                    
                                    toast.success('Download starting...');
                                    const win =window.open(downloadUrl, '_blank');
                                    setTimeout(() => {
                                        if (win) win.close();
                                      }, 1000);
                                    setTimeout(() => {
                                      toast.success('Cleaning up...');
                                      fetch(`${API_URL}/api/renders/${renderRecord.id}`, { method: 'DELETE' })
                                        .then(() => {
                                          setRenders(prev => {
                                            const newRenders = { ...prev };
                                            delete newRenders[renderRecord.id];
                                            return newRenders;
                                          });
                                          toast.success('Cleaned up!');
                                        })
                                        .catch(err => toast.error('Failed to clean up'));
                                    }, 3000);
                                    return;
                                  }
                                  
                                  // Jika sudah processing, jangan submit lagi
                                  if (isSubmittingSingle || renderStatus === 'queued' || renderStatus === 'processing') return;
                                  
                                  // Start render dengan auto-download
                                  setIsSubmittingSingle(true);
                                  try {
                                    const res = await fetch(`${API_URL}/api/clips/${activeClip.id}/render`, {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify({ face_tracking: faceTracking, smart_crop: smartCrop, captions, watermark_text: watermarkText })
                                    });
                                    if (!res.ok) {
                                      const err = await res.json();
                                      toast.error(err.detail || 'Failed to start render');
                                      return;
                                    }
                                    const data = await res.json();
                                    
                                    // Add to download manager
                                    addDownload({
                                      id: data.render_id,
                                      renderId: data.render_id,
                                      clipTitle: activeClip.title,
                                      jobId,
                                      status: 'queued',
                                      progress: 0,
                                    });
                                    
                                    // Tandai untuk auto-download
                                    setAutoDownloadQueue(prev => new Set(prev).add(data.render_id));
                                    
                                    toast.success('Render started! Will auto-download when ready.');
                                  } catch (err) {
                                    console.error(err);
                                    toast.error('Error starting render');
                                  } finally {
                                    setIsSubmittingSingle(false);
                                  }
                                };

                                const isProcessing = renderStatus === 'queued' || renderStatus === 'processing';
                                const isReady = renderStatus === 'ready';
                                const isFailed = renderStatus === 'failed';
                                const isCancelled = renderStatus === 'cancelled';
                                const renderProgress = renderRecord?.progress || 0;
                                const isInAutoDownloadQueue = renderRecord?.id ? autoDownloadQueue.has(renderRecord.id) : false;
                                const isPreviewLoaded = previewClipId ? !!previewLoadedByClipId[previewClipId] : false;
                                
                                let label = 'Render & Download';
                                let icon = <Wand2 size={18} />;
                                let isDisabled = false;

                                if (isProcessing) {
                                  label = `Rendering ${Math.round(renderProgress)}%`;
                                  icon = <Loader2 size={18} className="animate-spin" />;
                                  isDisabled = true;
                                } else if (!isPreviewLoaded) {
                                  label = 'Loading preview...';
                                  icon = <Loader2 size={18} className="animate-spin" />;
                                  isDisabled = true;
                                } else if (isReady && isInAutoDownloadQueue) {
                                  // Sedang menunggu auto-download
                                  label = 'Downloading...';
                                  icon = <Download size={18} className="animate-pulse" />;
                                  isDisabled = true;
                                } else if (isReady && !isInAutoDownloadQueue) {
                                  // Render sudah ready tapi bukan dari auto-download (legacy)
                                  label = 'Download & Cleanup';
                                  icon = <Download size={18} />;
                                }

                                return (
                                  <div className="flex items-center gap-2">
                                    <div className="flex flex-col gap-2">
                                      <button
                                        aria-label={label}
                                        onClick={handleRenderOrDownload}
                                        disabled={isDisabled}
                                        className={`px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center gap-2 ${
                                          isDisabled
                                            ? 'bg-indigo-600/50 cursor-not-allowed opacity-70'
                                            : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                                        }`}
                                      >
                                        {icon}
                                        {label}
                                      </button>
                                      {isProcessing && (
                                        <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                                          <div 
                                            className="bg-indigo-500 h-full transition-all duration-500 ease-out"
                                            style={{ width: `${renderProgress}%` }}
                                          />
                                        </div>
                                      )}
                                    </div>
                                    
                                    {/* Cancel/Delete Button */}
                                    {renderRecord && (
                                      <>
                                        {/* Cancel button for queued/processing */}
                                        {isProcessing && !isInAutoDownloadQueue && (
                                          <button
                                            onClick={() => handleCancelRender(renderRecord.id)}
                                            className="px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-semibold flex items-center gap-2 transition-all"
                                            aria-label="Cancel render"
                                          >
                                            <X size={18} />
                                            Cancel
                                          </button>
                                        )}
                                        
                                        {/* Delete button for ready/failed/cancelled (tidak bisa delete saat downloading) */}
                                        {(isReady || isFailed || isCancelled) && !isInAutoDownloadQueue && (
                                          <button
                                            onClick={() => handleDeleteRender(renderRecord.id)}
                                            className="px-4 py-2.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-white font-semibold flex items-center gap-2 transition-all"
                                            aria-label="Delete render"
                                          >
                                            <X size={18} />
                                            Delete
                                          </button>
                                        )}
                                      </>
                                    )}
                                  </div>
                                );
                              })()}
                           </div>

                           <div className="flex items-center gap-2">
                              <button 
                                aria-label="Previous clip"
                                onClick={() => {
                                  if (currentIndex > 0) setPreviewClipId(clips[currentIndex - 1].id);
                                }}
                                disabled={currentIndex === 0}
                                className="px-4 py-2 bg-slate-800 rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium flex items-center"
                              >
                                <ChevronLeft size={16} className="mr-1" /> Prev
                              </button>
                              <span className="text-slate-500 text-sm font-mono px-2">
                                {currentIndex + 1} / {clips.length}
                              </span>
                              <button 
                                aria-label="Next clip"
                                onClick={() => {
                                  if (currentIndex < clips.length - 1) setPreviewClipId(clips[currentIndex + 1].id);
                                }}
                                disabled={currentIndex === clips.length - 1}
                                className="px-4 py-2 bg-slate-800 rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium flex items-center"
                              >
                                Next <ChevronRight size={16} className="ml-1" />
                              </button>
                           </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
               );
            })()}

            {/* Sticky Controls Toolbar */}
            <div className="sticky top-2 sm:top-4 z-20 bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-2 sm:p-4 mb-6 sm:mb-8 shadow-xl flex flex-col sm:flex-row flex-wrap items-center justify-between gap-3 sm:gap-4 transition-all">
               <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-6 w-full sm:w-auto">
                  {/* Filters / Toggles */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-4 bg-slate-950/50 p-1 rounded-xl border border-white/5 w-full sm:w-auto">
                                        <input
                                          type="text"
                                          placeholder="Watermark text (optional)"
                                          aria-label="Watermark text"
                                          value={watermarkText}
                                          onChange={e => setWatermarkText(e.target.value)}
                                          className="px-3 py-1.5 rounded-lg bg-slate-800 text-white text-sm w-48"
                                          style={{ minWidth: 0 }}
                                        />
                    <button 
                      aria-label="Toggle face tracking"
                      onClick={() => setFaceTracking(!faceTracking)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                        faceTracking ? 'bg-emerald-500/10 text-emerald-400' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      <ScanFace size={16} />
                      Face Tracking
                      <div className={`w-2 h-2 rounded-full ${faceTracking ? 'bg-emerald-500' : 'bg-slate-600'}`} />
                    </button>
                    <button 
                      aria-label="Toggle smart crop"
                      onClick={() => setSmartCrop(!smartCrop)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                        smartCrop ? 'bg-purple-500/10 text-purple-400' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      <Users size={16} />
                      Smart Crop
                      <div className={`w-2 h-2 rounded-full ${smartCrop ? 'bg-purple-500' : 'bg-slate-600'}`} />
                    </button>
                    <div className="w-px h-4 bg-slate-800"></div>
                    <button 
                      aria-label="Toggle AI captions"
                      onClick={() => setCaptions(!captions)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                        captions ? 'bg-blue-500/10 text-blue-400' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      <FileText size={16} />
                      AI Captions
                      <div className={`w-2 h-2 rounded-full ${captions ? 'bg-blue-500' : 'bg-slate-600'}`} />
                    </button>
                  </div>
               </div>

               <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 w-full sm:w-auto mt-2 sm:mt-0">
                  <div className="text-sm text-slate-400 mr-2">
                    <span className="text-white font-bold">{selectedClips.size}</span> selected
                  </div>
                  {selectedClips.size < clips.length ? (
                     <button 
                       onClick={selectAllClips} 
                       disabled={rendering}
                       className="text-xs font-medium text-slate-400 hover:text-white underline decoration-slate-600 underline-offset-4 disabled:opacity-50 disabled:cursor-not-allowed"
                     >
                       Select All
                     </button>
                  ) : (
                    <button 
                      onClick={deselectAllClips} 
                      disabled={rendering}
                      className="text-xs font-medium text-slate-400 hover:text-white underline decoration-slate-600 underline-offset-4 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                       Deselect All
                     </button>
                  )}
                  
                  <button
                    onClick={renderSelectedClips}
                    disabled={eligibleSelectedCount === 0 || rendering}
                    className={`
                      relative group overflow-hidden pl-4 pr-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all
                      ${eligibleSelectedCount > 0 || rendering
                        ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-900/30 hover:shadow-emerald-900/50 hover:-translate-y-0.5' 
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'}
                      ${rendering ? 'opacity-80' : ''}
                    `}
                  >
                    {rendering ? <Loader2 className="animate-spin" size={18} /> : <Wand2 size={18} />}
                    {rendering
                      ? 'Rendering...'
                      : eligibleSelectedCount === 0
                        ? 'All Rendered'
                        : `Render ${eligibleSelectedCount} Clips`}
                  </button>
               </div>
            </div>

            {/* Filter and Sort Bar */}
            <div className="mb-6 bg-slate-900/60 backdrop-blur-md border border-white/10 rounded-xl p-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="text-sm font-medium text-slate-400 hover:text-white flex items-center gap-2"
                  >
                    <Settings2 size={16} />
                    {showFilters ? 'Hide Filters' : 'Show Filters'}
                  </button>
                  <div className="text-sm text-slate-400">
                    <span className="text-white font-bold">{filteredAndSortedClips.length}</span> of <span className="text-white font-bold">{clips.length}</span> clips
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <label className="text-sm text-slate-400">Sort by:</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'score' | 'duration' | 'time')}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 text-white text-sm border border-white/10 focus:border-emerald-500 focus:outline-none"
                  >
                    <option value="score">Score (High to Low)</option>
                    <option value="duration">Duration (Long to Short)</option>
                    <option value="time">Timeline (Start to End)</option>
                  </select>
                </div>
              </div>
              
              {showFilters && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Minimum Score: {minScore.toFixed(1)}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        step="0.5"
                        value={minScore}
                        onChange={(e) => setMinScore(parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                      />
                      <div className="flex justify-between text-xs text-slate-500 mt-1">
                        <span>0</span>
                        <span>5</span>
                        <span>10</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Clips Grid */}
            <div className="grid grid-cols-1 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
              {filteredAndSortedClips.map((clip) => (
                <div
                  key={clip.id}
                  onClick={() => setPreviewClipId(clip.id)}
                  className={`
                    group relative bg-slate-900 border rounded-2xl overflow-hidden cursor-pointer transition-all duration-300
                    hover:transform hover:-translate-y-1 hover:shadow-2xl hover:shadow-emerald-900/20
                    ${selectedClips.has(clip.id) 
                      ? 'border-emerald-500 ring-1 ring-emerald-500/50 shadow-lg shadow-emerald-900/10' 
                      : 'border-white/5 hover:border-white/20'}
                    min-h-[180px] sm:min-h-[220px]
                  `}
                >
                  {/* Thumbnail Container (9:16 Aspect) */}
                  <div className="aspect-[9/16] relative bg-slate-800 overflow-hidden w-full">
                    {/* REAL IMAGE SOURCE RESTORED */}
                    <img 
                      src={`${API_URL}/api/clips/${clip.id}/preview-frame?face_tracking=${faceTracking}`}
                      alt={clip.title}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 opacity-80 group-hover:opacity-100"
                      onError={(e) => {
                        console.error('[Thumbnail] Load error for clip:', clip.id);
                        console.error('[Thumbnail] Source:', `${API_URL}/api/clips/${clip.id}/preview-frame?face_tracking=${faceTracking}`);
                        // Set fallback placeholder
                        e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23334155" width="100" height="100"/%3E%3Ctext fill="%239ca3af" font-size="12" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3ENo Preview%3C/text%3E%3C/svg%3E';
                      }}
                    />
                    
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-90" />
                    
                    {/* Top Badges */}
                    <div className="absolute top-3 left-3 right-3 flex justify-between items-start">
                       <span className={`text-[10px] font-bold px-2 py-1 rounded backdrop-blur-md ${getScoreColor(clip.score)}`}>
                         {clip.score.toFixed(1)}
                       </span>
                       <div 
                         onClick={(e) => {
                            e.stopPropagation();
                            toggleClipSelection(clip.id);
                         }}
                         className={`w-8 h-8 rounded-full flex items-center justify-center backdrop-blur-md transition-all border ${
                            selectedClips.has(clip.id)
                              ? 'bg-emerald-500 text-white border-emerald-400'
                              : 'bg-black/40 text-white/30 border-white/10 hover:bg-black/60 hover:text-white'
                         }`}
                       >
                         {selectedClips.has(clip.id) ? <Check size={16} /> : <span className="text-xl leading-none mb-0.5">+</span>}
                       </div>
                    </div>

                    {/* Play Overlay */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                       <div className="w-12 h-12 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center pl-1">
                          <Play fill="white" className="text-white" size={20} />
                       </div>
                    </div>

                    {/* Bottom Info */}
                    <div className="absolute bottom-0 left-0 right-0 p-4">
                       <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1.5 font-medium">
                          <Clock size={12} />
                          {formatTime(clip.end_sec - clip.start_sec)}
                       </div>
                       <h3 className="text-white font-bold text-sm leading-snug line-clamp-2 mb-1 group-hover:text-emerald-400 transition-colors">
                         {clip.title}
                       </h3>
                    </div>
                  </div>

                  {/* Selection Indicator Bar */}
                  {selectedClips.has(clip.id) && (
                    <div className="h-1 w-full bg-emerald-500 absolute bottom-0 left-0 right-0 shadow-[0_-2px_10px_rgba(16,185,129,0.5)]" />
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
      
      {/* Floating Render Progress Indicator */}
      {(() => {
        const processingRenders = Object.values(renders).filter(r => r && (r.status === 'queued' || r.status === 'processing'));
        if (processingRenders.length === 0) return null;
        
        return (
          <div className="fixed bottom-6 right-6 z-50 bg-indigo-600 text-white px-6 py-4 rounded-2xl shadow-2xl border border-indigo-400/30 backdrop-blur-xl animate-in slide-in-from-bottom-4">
            <div className="flex items-center gap-3">
              <Loader2 size={20} className="animate-spin" />
              <div>
                <div className="font-bold text-sm">
                  {processingRenders.length} clip{processingRenders.length > 1 ? 's' : ''} rendering
                </div>
                <div className="text-xs text-indigo-200 mt-0.5">
                  {processingRenders.map(r => `${Math.round(r.progress || 0)}%`).join(', ')}
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

// Helper: get download link for render (S3 or local)
function getRenderDownloadUrl(render: Render, API_URL: string) {
  if (!render.output_path) return null;
  if (render.output_path.startsWith('http')) return render.output_path;
  // fallback to API download endpoint
  return `${API_URL}/api/renders/${render.id}/download`;
}
