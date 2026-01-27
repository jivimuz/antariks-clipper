'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

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
}

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<Job | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [selectedClips, setSelectedClips] = useState<Set<string>>(new Set());
  const [previewClipId, setPreviewClipId] = useState<string | null>(null);
  const [faceTracking, setFaceTracking] = useState(true);
  const [captions, setCaptions] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [renders, setRenders] = useState<Record<string, Render>>({});

  const API_URL = 'http://localhost:8000';

  // Fetch job
  useEffect(() => {
    const fetchJob = async () => {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
      const data = await res.json();
      setJob(data);
    };
    
    fetchJob();
    const interval = setInterval(fetchJob, 2000);
    return () => clearInterval(interval);
  }, [jobId]);

  // Fetch clips when job is ready
  useEffect(() => {
    if (job?.status === 'ready') {
      fetch(`${API_URL}/api/jobs/${jobId}/clips`)
        .then(res => res.json())
        .then(data => setClips(data.clips || []));
    }
  }, [job?.status, jobId]);

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
    if (selectedClips.size === 0) return;
    
    setRendering(true);
    try {
      const res = await fetch(`${API_URL}/api/jobs/${jobId}/render-selected?${new URLSearchParams({
        clip_ids: Array.from(selectedClips).join(',')
      })}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          face_tracking: faceTracking,
          captions: captions
        })
      });
      const data = await res.json();
      
      // Poll render status
      for (const renderId of data.render_ids) {
        pollRenderStatus(renderId);
      }
    } catch (error) {
      console.error('Render error:', error);
    }
    setRendering(false);
  };

  const pollRenderStatus = async (renderId: string) => {
    const poll = async () => {
      const res = await fetch(`${API_URL}/api/renders/${renderId}`);
      const render = await res.json();
      setRenders(prev => ({ ...prev, [renderId]: render }));
      
      if (render.status !== 'ready' && render.status !== 'failed') {
        setTimeout(poll, 2000);
      }
    };
    poll();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!job) return <div className="p-8">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <Link href="/jobs" className="text-blue-400 hover:underline mb-4 block">
        ← Back to Jobs
      </Link>

      {/* Job Status */}
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h1 className="text-2xl font-bold mb-4">Job: {job.id.slice(0, 8)}...</h1>
        
        <div className="flex items-center gap-4 mb-4">
          <span className={`px-3 py-1 rounded text-sm ${
            job.status === 'ready' ? 'bg-green-600' :
            job.status === 'failed' ? 'bg-red-600' :
            job.status === 'processing' ? 'bg-yellow-600' :
            'bg-gray-600'
          }`}>
            {job.status}
          </span>
          {job.step && <span className="text-gray-400">Step: {job.step}</span>}
        </div>

        {job.status === 'processing' && (
          <div className="w-full bg-gray-700 rounded h-4 mb-2">
            <div 
              className="bg-blue-500 h-4 rounded transition-all"
              style={{ width: `${job.progress}%` }}
            />
          </div>
        )}

        {job.error && (
          <div className="bg-red-900/50 text-red-300 p-3 rounded mt-4">
            Error: {job.error}
          </div>
        )}
      </div>

      {/* Preview Mode */}
      {job.status === 'ready' && clips.length > 0 && (
        <>
          {/* Controls */}
          <div className="bg-gray-800 rounded-lg p-4 mb-6 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="faceTracking"
                checked={faceTracking}
                onChange={(e) => setFaceTracking(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="faceTracking">Face Tracking</label>
            </div>
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="captions"
                checked={captions}
                onChange={(e) => setCaptions(e.target.checked)}
                className="w-4 h-4"
              />
              <label htmlFor="captions">Captions</label>
            </div>

            <div className="flex-1" />

            <button
              onClick={selectAllClips}
              className="px-3 py-1 bg-gray-700 rounded hover:bg-gray-600"
            >
              Select All
            </button>
            <button
              onClick={deselectAllClips}
              className="px-3 py-1 bg-gray-700 rounded hover:bg-gray-600"
            >
              Deselect All
            </button>
            
            <button
              onClick={renderSelectedClips}
              disabled={selectedClips.size === 0 || rendering}
              className={`px-4 py-2 rounded font-bold ${
                selectedClips.size === 0 || rendering
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-500'
              }`}
            >
              {rendering ? 'Rendering...' : `Render ${selectedClips.size} Clips`}
            </button>
          </div>

          {/* Preview Player */}
          {previewClipId && (
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Preview</h2>
                <button
                  onClick={() => setPreviewClipId(null)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕ Close
                </button>
              </div>
              <div className="flex justify-center">
                <video
                  key={previewClipId + faceTracking}
                  controls
                  autoPlay
                  className="max-h-[600px] rounded"
                  style={{ aspectRatio: '9/16' }}
                >
                  <source
                    src={`${API_URL}/api/clips/${previewClipId}/preview?face_tracking=${faceTracking}`}
                    type="video/mp4"
                  />
                </video>
              </div>
            </div>
          )}

          {/* Clips Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {clips.map((clip) => (
              <div
                key={clip.id}
                className={`bg-gray-800 rounded-lg overflow-hidden cursor-pointer transition-all ${
                  selectedClips.has(clip.id) ? 'ring-2 ring-green-500' : ''
                }`}
              >
                {/* Thumbnail with 9:16 aspect */}
                <div 
                  className="relative bg-gray-700"
                  style={{ aspectRatio: '9/16' }}
                  onClick={() => setPreviewClipId(clip.id)}
                >
                  <img
                    src={`${API_URL}/api/clips/${clip.id}/preview-frame?face_tracking=${faceTracking}`}
                    alt={clip.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-2 right-2 bg-black/70 px-2 py-1 rounded text-xs">
                    {formatTime(clip.end_sec - clip.start_sec)}
                  </div>
                  <div className="absolute top-2 left-2 bg-black/70 px-2 py-1 rounded text-xs">
                    Score: {clip.score.toFixed(1)}
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 bg-black/50 transition-opacity">
                    <span className="text-4xl">▶</span>
                  </div>
                </div>
                
                {/* Info */}
                <div className="p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <input
                      type="checkbox"
                      checked={selectedClips.has(clip.id)}
                      onChange={() => toggleClipSelection(clip.id)}
                      className="w-4 h-4"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <span className="text-sm font-medium truncate">{clip.title}</span>
                  </div>
                  <p className="text-xs text-gray-400 line-clamp-2">
                    {clip.transcript_snippet}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
