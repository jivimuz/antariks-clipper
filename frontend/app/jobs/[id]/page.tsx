'use client';

import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  ArrowLeft, Play, CheckCircle2, Clock, AlertCircle, 
  Settings2, Download, Check, X, Wand2, FileText, 
  ScanFace, Share2, MoreVertical, Loader2, Youtube, FileVideo,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { getApiUrl, getApiEndpoint } from '@/lib/api';

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



export default function JobDetailPage() {
  const API_URL = getApiUrl();
  const params = useParams();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<Job | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [selectedClips, setSelectedClips] = useState<Set<string>>(new Set());
  const [previewClipId, setPreviewClipId] = useState<string | null>(null);
  const [faceTracking, setFaceTracking] = useState(true);
  const [captions, setCaptions] = useState(false);
  const [watermarkText, setWatermarkText] = useState("");
  const [rendering, setRendering] = useState(false);
  
  // State untuk mencegah spam tombol render satuan
  const [isSubmittingSingle, setIsSubmittingSingle] = useState(false);
  
  const [renders, setRenders] = useState<Record<string, Render>>({});

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


  // Fetch job (Real Logic)
  useEffect(() => {
    const fetchJob = async () => {
      try {
        const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
        const data = await res.json();
        setJob(data);
      } catch (error) {
        console.error("Error fetching job:", error);
      }
    };
    
    fetchJob();
    const interval = setInterval(fetchJob, 2000);
    return () => clearInterval(interval);
  }, [jobId]);

  // Fetch clips when job is ready (Real Logic)
  useEffect(() => {
    if (job?.status === 'ready') {
      fetch(`${API_URL}/api/jobs/${jobId}/clips`)
        .then(res => res.json())
        .then(data => setClips(data.clips || []))
        .catch(err => console.error("Error fetching clips:", err));
    }
  }, [job?.status, jobId]);

  // Track previous job status to avoid duplicate toasts
  const prevStatus = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!job) return;
    if (job.status !== prevStatus.current) {
      if (job.status === "ready") toast.success("Job finished!");
      if (job.status === "failed") toast.error("Job failed");
      prevStatus.current = job.status;
    }
  }, [job?.status]);

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
    setRendering(true);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/render-selected?${new URLSearchParams({
        clip_ids: Array.from(selectedClips).join(',')
      })}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          face_tracking: faceTracking,
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
        pollRenderStatus(renderId);
      }
      toast.success(`Rendering ${data.render_ids.length} clips started!`);
    } catch (error) {
      console.error('Render error:', error);
      toast.error('Error starting render');
    } finally {
      setTimeout(() => setRendering(false), 3000);
    }
  };

  const pollRenderStatus = async (renderId: string) => {
    let notified = false;
    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/api/renders/${renderId}`);
        const render = await res.json();
        setRenders(prev => ({ ...prev, [renderId]: render }));
        if ((render.status === 'ready' || render.status === 'failed') && !notified) {
          notified = true;
          if (render.status === 'ready') {
            toast.success('Render finished!');
          } else if (render.status === 'failed') {
            toast.error('Render failed.');
          }
        }
        if (render.status !== 'ready' && render.status !== 'failed') {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error("Polling error", error);
      }
    };
    poll();
  };

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

  if (!job) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-emerald-500 animate-spin" />
          <p className="text-emerald-400 font-medium animate-pulse">Syncing Job Data...</p>
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
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 sm:gap-6 mb-6 sm:mb-10">
          <div>
            <Link href="/jobs" className="inline-flex items-center text-slate-400 hover:text-emerald-400 mb-2 transition-colors group text-sm font-medium" aria-label="Back to Jobs">
              <ArrowLeft size={16} className="mr-2 group-hover:-translate-x-1 transition-transform" />
              Back to Jobs
            </Link>
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
        {job.status === 'processing' && (
          <div className="bg-slate-900/50 border border-blue-500/20 rounded-2xl p-8 mb-8 text-center backdrop-blur-sm">
            <div className="max-w-md mx-auto">
               <div className="flex justify-between text-sm font-medium mb-2">
                 <span className="text-blue-400 flex items-center gap-2"><Loader2 size={14} className="animate-spin" /> Processing...</span>
                 <span className="text-white">{job.progress}%</span>
               </div>
               <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <div className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-300" style={{ width: `${job.progress}%` }} />
               </div>
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
                           >
                             <source
                               src={`${API_URL}/api/clips/${previewClipId}/preview?face_tracking=${faceTracking}`}
                               type="video/mp4"
                             />
                             Your browser does not support the video tag.
                           </video>
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

                        {/* Action Bar inside Preview */}
                        <div className="mt-auto border-t border-white/5 pt-6 flex flex-wrap items-center justify-between gap-4">
                           <div className="flex items-center gap-3">
                             {/* Download link for render if available */}
                             {(() => {
                               // Cari render untuk clip ini
                               const render = Object.values(renders).find(r => r && r.status === 'ready' && r.clip_id === activeClip.id);
                               const url = render && getRenderDownloadUrl(render, API_URL);
                               return url ? (
                                 <a href={url} target="_blank" rel="noopener noreferrer" className="ml-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-xl font-bold text-sm">Download</a>
                               ) : null;
                             })()}

                              <button
                                aria-label="Render this clip"
                                onClick={async () => {
                                  if (isSubmittingSingle) return;
                                  setIsSubmittingSingle(true);
                                  try {
                                    const res = await fetch(`${API_URL}/api/clips/${activeClip.id}/render`, {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify({ face_tracking: faceTracking, captions, watermark_text: watermarkText })
                                    });
                                    if (!res.ok) {
                                      const err = await res.json();
                                      toast.error(err.detail || 'Failed to start render');
                                      return;
                                    }
                                    const data = await res.json();
                                    pollRenderStatus(data.render_id);
                                    toast.success('Render started!');
                                  } catch (err) {
                                    console.error(err);
                                    toast.error('Error starting render');
                                  } finally {
                                    setIsSubmittingSingle(false);
                                  }
                                }}
                                disabled={isSubmittingSingle}
                                className={`px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center gap-2 ${
                                  isSubmittingSingle 
                                    ? 'bg-indigo-600/50 cursor-not-allowed opacity-70' 
                                    : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                                }`}
                             >
                                {isSubmittingSingle ? <Loader2 size={18} className="animate-spin" /> : <Wand2 size={18} />} 
                                {isSubmittingSingle ? 'Processing...' : 'Render This'}
                             </button>
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
                    disabled={selectedClips.size === 0 || rendering}
                    className={`
                      relative group overflow-hidden pl-4 pr-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all
                      ${selectedClips.size > 0 || rendering
                        ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-900/30 hover:shadow-emerald-900/50 hover:-translate-y-0.5' 
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'}
                      ${rendering ? 'opacity-80' : ''}
                    `}
                  >
                    {rendering ? <Loader2 className="animate-spin" size={18} /> : <Wand2 size={18} />}
                    {rendering ? 'Rendering...' : `Render ${selectedClips.size} Clips`}
                  </button>
               </div>
            </div>

            {/* Clips Grid */}
            <div className="grid grid-cols-1 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
              {clips.map((clip) => (
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