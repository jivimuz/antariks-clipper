'use client';

import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Youtube, Upload, Sparkles, ArrowRight, AlertCircle, Loader2, Film, CheckCircle2, Shield } from 'lucide-react';
import { getApiEndpoint } from '@/lib/api';
import { isValidYouTubeUrl, validateVideoFile } from '@/lib/validation';
import { LicenseStatus } from '@/types/license';

function useIsLoggedIn() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      setIsLoggedIn(!!token);
    }
  }, []);
  return isLoggedIn;
}

function useLicenseStatus() {
  const [licenseStatus, setLicenseStatus] = useState<LicenseStatus | null>(null);
  useEffect(() => {
    // Use the unified validate endpoint
    fetch(getApiEndpoint('/api/license/validate'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
      .then(res => res.json())
      .then(data => {
        // Map the new response format to LicenseStatus
        if (data.valid) {
          setLicenseStatus({
            activated: true,
            valid: true,
            owner: data.owner,
            expires: data.expires
          });
        } else {
          setLicenseStatus({
            activated: false,
            valid: false
          });
        }
      })
      .catch(err => console.error('Failed to fetch license status:', err));
  }, []);
  return licenseStatus;
}

export default function Home() {
  const isLoggedIn = useIsLoggedIn();
  const licenseStatus = useLicenseStatus();
  const [menuOpen, setMenuOpen] = useState(false);
  const [sourceType, setSourceType] = useState<'youtube' | 'upload'>('youtube');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdJobId, setCreatedJobId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // Validate inputs
      if (sourceType === 'youtube') {
        if (!youtubeUrl) {
          setError('Please enter a YouTube URL');
          toast.error('Please enter a YouTube URL');
          setLoading(false);
          return;
        }
        if (!isValidYouTubeUrl(youtubeUrl)) {
          setError('Please enter a valid YouTube URL (e.g., https://www.youtube.com/watch?v=...)');
          toast.error('Invalid YouTube URL format');
          setLoading(false);
          return;
        }
      } else {
        if (!file) {
          setError('Please select a video file to upload');
          toast.error('Please select a video file to upload');
          setLoading(false);
          return;
        }
        const validation = validateVideoFile(file);
        if (!validation.isValid) {
          setError(validation.error || 'Invalid video file');
          toast.error(validation.error || 'Invalid video file');
          setLoading(false);
          return;
        }
      }

      const formData = new FormData();
      formData.append('source_type', sourceType);
      if (sourceType === 'youtube') {
        formData.append('youtube_url', youtubeUrl);
      } else {
        // TypeScript now knows file is not null due to the check above
        formData.append('file', file!);
      }
      // --- SaaS: Require license key ---
      const licenseKey = typeof window !== 'undefined' ? localStorage.getItem('license_key') : null;
      if (!licenseKey) {
        setError('License key required. Please enter your license in the Account page.');
        toast.error('License key required. Please enter your license in the Account page.');
        setLoading(false);
        return;
      }
      // Real API call
      const response = await fetch(getApiEndpoint('/api/jobs'), {
        method: 'POST',
        body: formData,
        headers: {
          'X-License-Key': licenseKey
        }
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to initiate job processing');
      }
      const data = await response.json();
      setCreatedJobId(data.job_id);
      toast.success('Job created successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      toast.error(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCreatedJobId(null);
    setYoutubeUrl('');
    setFile(null);
    setError('');
  };

  function handleLogout() {
    localStorage.removeItem('token');
    window.location.reload();
  }

  function handleLogin() {
    window.location.href = "/login";
  }

  return (
    <>
      {/* License Status Badge - Top Left */}
      {licenseStatus && licenseStatus.activated && licenseStatus.valid && (
        <div className="fixed top-4 left-4 z-50 bg-slate-900/80 backdrop-blur-sm border border-emerald-500/30 rounded-xl px-3 py-2 shadow-lg">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-emerald-400" />
            <div className="text-xs">
              <div className="text-emerald-400 font-semibold">
                Licensed to: {licenseStatus.owner}
              </div>
              <div className="text-slate-400">
                Expires: {licenseStatus.expires}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="fixed top-4 right-4 z-50 flex justify-end items-center">
        {isLoggedIn ? (
          <div className="relative flex gap-2">
            <button
              className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-2xl text-white border border-slate-700 hover:ring-2 hover:ring-emerald-400 transition-all"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="User menu"
            >
              <span role="img" aria-label="User">👤</span>
            </button>
            <a
              href="/settings"
              className="px-3 py-2 bg-emerald-700 hover:bg-emerald-600 rounded-xl text-white font-bold text-xs"
            >
              License Settings
            </a>
            {menuOpen && (
              <div className="absolute right-0 mt-2 w-32 bg-slate-900 border border-slate-700 rounded-xl shadow-lg z-50">
                <button
                  className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-slate-800 rounded-xl"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-sm"
            onClick={handleLogin}
          >
            Login
          </button>
        )}
      </div>

      <div className="min-h-screen bg-slate-950 relative overflow-hidden flex items-center justify-center p-2 sm:p-4 selection:bg-emerald-500/30 font-sans">
        {/* Background Ambient Effects */}
        <div className="absolute top-0 -left-4 w-96 h-96 bg-emerald-600/20 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-0 -right-4 w-96 h-96 bg-teal-600/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

        <div className="w-full max-w-2xl relative z-10 px-0 sm:px-4">
          
          {/* Header Section (Hidden on success to focus on result) */}
          {!createdJobId && (
            <div className="text-center mb-10 space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/50 border border-emerald-500/30 text-emerald-400 text-xs font-medium mb-4 backdrop-blur-sm animate-fade-in-up">
                <Sparkles size={12} />
                <span>AI-Powered Video Generation</span>
              </div>
              
              <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-white">
                Antariks <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">Clipper</span>
              </h1>
              <p className="text-slate-400 text-lg max-w-lg mx-auto leading-relaxed">
                Transform long videos into viral <span className="text-emerald-400 font-medium">Reels & TikToks</span> instantly using advanced AI analysis.
              </p>
            </div>
          )}

          {/* Main Card */}
          <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl sm:rounded-3xl shadow-2xl overflow-hidden ring-1 ring-white/5 transition-all duration-500">
            
            {createdJobId ? (
              // SUCCESS VIEW
                <div className="p-6 sm:p-12 text-center space-y-6 animate-in zoom-in-95 duration-300">
                <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 size={40} className="text-emerald-400" />
                </div>
                
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold text-white">Processing Started!</h2>
                  <p className="text-slate-400 max-w-sm mx-auto">
                    Your video is being analyzed. We'll notify you when your viral clips are ready.
                  </p>
                </div>

                <div className="bg-slate-950/50 rounded-xl p-4 border border-white/5 inline-block">
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Job ID</p>
                  <code className="text-emerald-400 font-mono text-lg">{createdJobId}</code>
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleReset}
                    className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-medium transition-colors border border-white/10"
                  >
                    Create Another Clip
                  </button>
                </div>
              </div>
            ) : (
              // FORM VIEW
              <>
                <div className="p-1">
                  {/* Toggle Switch */}
                  <div className="grid grid-cols-2 gap-1 p-1 bg-slate-950/50 rounded-2xl">
                    <button
                      onClick={() => setSourceType('youtube')}
                      aria-label="Select YouTube URL input"
                      className={`flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
                        sourceType === 'youtube'
                          ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <Youtube size={18} />
                      YouTube URL
                    </button>
                    <button
                      onClick={() => setSourceType('upload')}
                      aria-label="Select file upload input"
                      className={`flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
                        sourceType === 'upload'
                          ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20'
                          : 'text-slate-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <Upload size={18} />
                      Upload File
                    </button>
                  </div>
                </div>

                <div className="p-4 sm:p-8">
                  <form onSubmit={handleSubmit} className="space-y-8">
                    <div className="space-y-4">
                      {sourceType === 'youtube' ? (
                        <div className="group space-y-2">
                          <label className="block text-sm font-medium text-emerald-100/80 ml-1">
                            Paste YouTube Link
                          </label>
                          <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                              <Youtube size={20} />
                            </div>
                            <input
                              type="url"
                              aria-label="YouTube video URL"
                              value={youtubeUrl}
                              onChange={(e) => setYoutubeUrl(e.target.value)}
                              placeholder="https://www.youtube.com/watch?v=..."
                              className="w-full pl-12 pr-4 py-4 bg-slate-950/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-600 focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all outline-none"
                              disabled={loading}
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <label className="block text-sm font-medium text-emerald-100/80 ml-1">
                            Select Video File
                          </label>
                          <div className="relative group">
                            <input
                              type="file"
                              accept="video/*"
                              aria-label="Upload video file"
                              onChange={(e) => setFile(e.target.files?.[0] || null)}
                              className="hidden"
                              id="file-upload"
                              disabled={loading}
                            />
                            <label
                              htmlFor="file-upload"
                              className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
                                file 
                                  ? 'border-emerald-500/50 bg-emerald-900/10' 
                                  : 'border-slate-700 hover:border-emerald-500/50 hover:bg-slate-800/50'
                              }`}
                            >
                              {file ? (
                                <div className="flex flex-col items-center text-emerald-400">
                                  <Film size={24} className="mb-2" />
                                  <span className="font-medium text-sm">{file.name}</span>
                                  <span className="text-xs text-emerald-500/60 mt-1">Ready to process</span>
                                </div>
                              ) : (
                                <div className="flex flex-col items-center text-slate-500 group-hover:text-emerald-400 transition-colors">
                                  <Upload size={24} className="mb-2" />
                                  <span className="font-medium text-sm">Click to browse</span>
                                  <span className="text-xs text-slate-600 mt-1">MP4, MOV, or WebM</span>
                                </div>
                              )}
                            </label>
                          </div>
                        </div>
                      )}
                    </div>

                    {error && (
                      <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 animate-in fade-in slide-in-from-top-2">
                        <AlertCircle size={20} className="shrink-0 mt-0.5" />
                        <span className="text-sm font-medium">{error}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      aria-label="Generate highlights"
                      disabled={loading}
                      className="group relative w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold rounded-xl hover:from-emerald-500 hover:to-teal-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-900/20 hover:shadow-emerald-900/40 hover:-translate-y-0.5 active:translate-y-0 overflow-hidden"
                    >
                      {/* Button Shine Effect */}
                      <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 blur-md rounded-xl" />
                      <span className="relative z-10 flex items-center gap-2">
                        {loading ? (
                          <>
                            <Loader2 className="animate-spin" size={20} />
                            Processing Magic...
                          </>
                        ) : (
                          <>
                            Generate Highlights
                            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                          </>
                        )}
                      </span>
                    </button>
                  </form>
                </div>
              </>
            )}

            {/* Footer Links */}
            <div className="mt-4 sm:mt-8 text-center">
              <a
                href="/jobs"
                className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-emerald-400 transition-colors font-medium"
              >
                View History & Downloads
                <ArrowRight size={14} />
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}