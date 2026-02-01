'use client';

import { useEffect, useState } from 'react';
import { ArrowLeft, Clock, CheckCircle2, AlertCircle, Loader2, Youtube, FileVideo, ChevronRight, Calendar } from 'lucide-react';
import toast from "react-hot-toast";
import { getApiEndpoint } from '@/lib/api';
import Breadcrumb from '@/components/Breadcrumb';
import { SkeletonJobList } from '@/components/Skeleton';

interface Job {
  id: string;
  source_type: string;
  source_url?: string;
  status: 'ready' | 'processing' | 'failed';
  step: string;
  progress: number;
  error?: string;
  created_at: string;
}



export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch(getApiEndpoint('/api/jobs'));
      const data = await response.json();
      setJobs(data.jobs);
      toast.success("Jobs loaded!");
    } catch (error) {
      toast.error('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]';
      case 'processing':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]';
      case 'failed':
        return 'bg-red-500/10 text-red-400 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)]';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready': return <CheckCircle2 size={16} />;
      case 'processing': return <Loader2 size={16} className="animate-spin" />;
      case 'failed': return <AlertCircle size={16} />;
      default: return <Clock size={16} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden font-sans selection:bg-emerald-500/30">
      {/* Background Ambient Effects */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-teal-600/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      <div className="container mx-auto px-4 py-16 relative z-10">
        <div className="max-w-5xl mx-auto">
          
          {/* Breadcrumb */}
          <Breadcrumb items={[{ label: 'Jobs' }]} />
          
          {/* Header */}
          <div className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <h1 className="text-4xl font-bold text-white tracking-tight">
                Processing <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">Queue</span>
              </h1>
              <p className="text-slate-400 mt-2 text-lg">Track your video generation status and history.</p>
            </div>
          </div>

          {/* Content */}
          {loading ? (
            <SkeletonJobList />
          ) : jobs.length === 0 ? (
            <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-16 text-center shadow-2xl">
              <div className="w-20 h-20 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-6">
                <Clock size={40} className="text-slate-600" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">No jobs found</h3>
              <p className="text-slate-400 mb-8 max-w-md mx-auto">
                You haven't generated any clips yet. Start your first job to see it appear here.
              </p>
              <a
                href="/"
                className="inline-flex items-center px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition-all shadow-lg shadow-emerald-900/20 hover:shadow-emerald-900/40"
              >
                Create New Job
              </a>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                 <a
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="block group relative bg-slate-900/40 hover:bg-slate-900/60 backdrop-blur-md border border-white/5 hover:border-emerald-500/20 rounded-2xl p-6 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-900/10 cursor-pointer overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/0 via-emerald-500/0 to-emerald-500/0 group-hover:via-emerald-500/5 transition-all duration-500" />
                  
                  <div className="relative flex flex-col md:flex-row md:items-center gap-6">
                    
                    {/* Icon & Source Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-xl shrink-0 ${
                          job.source_type === 'youtube' 
                            ? 'bg-red-500/10 text-red-400' 
                            : 'bg-blue-500/10 text-blue-400'
                        }`}>
                          {job.source_type === 'youtube' ? <Youtube size={24} /> : <FileVideo size={24} />}
                        </div>
                        
                        <div className="space-y-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                             <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase tracking-wider ${getStatusColor(job.status)}`}>
                              {getStatusIcon(job.status)}
                              {job.status}
                            </span>
                            <span className="text-xs text-slate-500 flex items-center gap-1">
                              <Calendar size={12} />
                              {new Date(job.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          
                          <h3 className="text-lg font-semibold text-white truncate pr-4">
                            {job.source_url || `Uploaded File: ${job.id}`}
                          </h3>
                          
                          {job.error ? (
                            <p className="text-sm text-red-400 flex items-center gap-1.5">
                              <AlertCircle size={14} />
                              {job.error}
                            </p>
                          ) : (
                             <p className="text-sm text-slate-400 font-mono">ID: {job.id}</p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Progress Section */}
                    <div className="w-full md:w-64 shrink-0 flex flex-col justify-center">
                       {job.status === 'processing' ? (
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs font-medium uppercase tracking-wide">
                            <span className="text-emerald-400 animate-pulse">{job.step.replace('_', ' ')}</span>
                            <span className="text-white">{job.progress}%</span>
                          </div>
                          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-emerald-600 to-teal-400 transition-all duration-500 relative"
                              style={{ width: `${job.progress}%` }}
                            >
                                <div className="absolute inset-0 bg-white/20 animate-[shimmer_1.5s_infinite]" />
                            </div>
                          </div>
                        </div>
                       ) : job.status === 'ready' ? (
                         <div className="flex items-center justify-end gap-2 text-emerald-400 text-sm font-medium">
                            <span>View Clips</span>
                            <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                                <ChevronRight size={16} />
                            </div>
                         </div>
                       ) : (
                         <div className="flex justify-end">
                            <button className="text-xs text-slate-500 hover:text-white underline underline-offset-4">
                                Retry Job
                            </button>
                         </div>
                       )}
                    </div>

                  </div>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}