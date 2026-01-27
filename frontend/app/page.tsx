'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [sourceType, setSourceType] = useState<'youtube' | 'upload'>('youtube');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('source_type', sourceType);

      if (sourceType === 'youtube') {
        if (!youtubeUrl) {
          setError('Please enter a YouTube URL');
          setLoading(false);
          return;
        }
        formData.append('youtube_url', youtubeUrl);
      } else {
        if (!file) {
          setError('Please select a video file');
          setLoading(false);
          return;
        }
        formData.append('file', file);
      }

      const response = await fetch('http://localhost:8000/api/jobs', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create job');
      }

      const data = await response.json();
      router.push(`/jobs/${data.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
              Antariks Clipper
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              Auto-generate viral highlight clips for Reels & TikTok
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setSourceType('youtube')}
                className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                  sourceType === 'youtube'
                    ? 'bg-red-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                YouTube URL
              </button>
              <button
                onClick={() => setSourceType('upload')}
                className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                  sourceType === 'upload'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                Upload Video
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {sourceType === 'youtube' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    YouTube URL
                  </label>
                  <input
                    type="url"
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    disabled={loading}
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Video File
                  </label>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    disabled={loading}
                  />
                  {file && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      Selected: {file.name}
                    </p>
                  )}
                </div>
              )}

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 px-6 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold rounded-lg hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
              >
                {loading ? 'Processing...' : 'Generate Highlights'}
              </button>
            </form>

            <div className="mt-8 text-center">
              <a
                href="/jobs"
                className="text-purple-600 hover:text-purple-700 dark:text-purple-400 font-medium"
              >
                View All Jobs →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
