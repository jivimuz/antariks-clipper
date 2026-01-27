'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

interface Job {
  id: string;
  source_type: string;
  source_url?: string;
  status: string;
  step: string;
  progress: number;
  error?: string;
}

interface Clip {
  id: string;
  start_sec: number;
  end_sec: number;
  score: number;
  title: string;
  transcript_snippet: string;
  thumbnail_path: string;
}

interface Render {
  id: string;
  status: string;
  progress: number;
  output_path?: string;
  error?: string;
}

export default function JobDetailPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [renders, setRenders] = useState<Record<string, Render>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (jobId) {
      fetchJob();
      const interval = setInterval(fetchJob, 2000); // Poll every 2 seconds
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const fetchJob = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/jobs/${jobId}`);
      const data = await response.json();
      setJob(data);

      if (data.status === 'ready') {
        fetchClips();
      }
    } catch (error) {
      console.error('Failed to fetch job:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClips = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/jobs/${jobId}/clips`);
      const data = await response.json();
      setClips(data.clips);
    } catch (error) {
      console.error('Failed to fetch clips:', error);
    }
  };

  const handleRender = async (clipId: string, faceTracking: boolean, captions: boolean) => {
    try {
      const response = await fetch(`http://localhost:8000/api/clips/${clipId}/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ face_tracking: faceTracking, captions }),
      });
      const data = await response.json();

      // Start polling for render status
      pollRenderStatus(data.render_id);
    } catch (error) {
      console.error('Failed to create render:', error);
    }
  };

  const pollRenderStatus = async (renderId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/renders/${renderId}`);
        const data = await response.json();

        setRenders((prev) => ({ ...prev, [renderId]: data }));

        if (data.status === 'ready' || data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Failed to fetch render:', error);
        clearInterval(interval);
      }
    }, 2000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-purple-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading job...</p>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">Job not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <Link
              href="/jobs"
              className="text-purple-600 hover:text-purple-700 dark:text-purple-400 font-medium"
            >
              ← Back to Jobs
            </Link>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Job Details
            </h1>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Status</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                  {job.status}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Progress</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {job.progress}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Source Type</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                  {job.source_type}
                </p>
              </div>
              {job.step && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Current Step</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {job.step}
                  </p>
                </div>
              )}
            </div>

            {job.source_url && (
              <div className="mb-6">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Source URL</p>
                <p className="text-gray-900 dark:text-white break-all">{job.source_url}</p>
              </div>
            )}

            {job.status === 'processing' && (
              <div className="mb-6">
                <div className="w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
                    style={{ width: `${job.progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {job.error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400">
                Error: {job.error}
              </div>
            )}
          </div>

          {job.status === 'ready' && clips.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Highlight Clips ({clips.length})
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {clips.map((clip) => (
                  <div
                    key={clip.id}
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden"
                  >
                    {clip.thumbnail_path && (
                      <img
                        src={`http://localhost:8000/api/thumbnails/${clip.id}`}
                        alt={clip.title}
                        className="w-full h-48 object-cover"
                      />
                    )}
                    <div className="p-4">
                      <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-2">
                        {clip.title}
                      </h3>
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                        <span>
                          {formatTime(clip.start_sec)} - {formatTime(clip.end_sec)}
                        </span>
                        <span>•</span>
                        <span>{(clip.end_sec - clip.start_sec).toFixed(0)}s</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                        {clip.transcript_snippet}
                      </p>

                      <div className="space-y-2">
                        <button
                          onClick={() => handleRender(clip.id, false, false)}
                          className="w-full py-2 px-4 bg-purple-500 text-white rounded-lg hover:bg-purple-600 text-sm font-medium"
                        >
                          Render (Simple)
                        </button>
                        <button
                          onClick={() => handleRender(clip.id, true, false)}
                          className="w-full py-2 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm font-medium"
                        >
                          Render (Face Tracking)
                        </button>
                        <button
                          onClick={() => handleRender(clip.id, false, true)}
                          className="w-full py-2 px-4 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm font-medium"
                        >
                          Render (Captions)
                        </button>
                      </div>

                      {/* Show render status */}
                      {Object.entries(renders).map(
                        ([renderId, render]) =>
                          render && (
                            <div key={renderId} className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                              {render.status === 'processing' && (
                                <div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    Rendering... {render.progress}%
                                  </p>
                                  <div className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-full mt-2">
                                    <div
                                      className="h-full bg-blue-500 rounded-full transition-all"
                                      style={{ width: `${render.progress}%` }}
                                    ></div>
                                  </div>
                                </div>
                              )}
                              {render.status === 'ready' && (
                                <a
                                  href={`http://localhost:8000/api/renders/${renderId}/download`}
                                  download
                                  className="block w-full py-2 px-4 bg-green-500 text-white text-center rounded-lg hover:bg-green-600 text-sm font-medium"
                                >
                                  Download
                                </a>
                              )}
                              {render.status === 'failed' && (
                                <p className="text-sm text-red-600 dark:text-red-400">
                                  Render failed: {render.error}
                                </p>
                              )}
                            </div>
                          )
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
