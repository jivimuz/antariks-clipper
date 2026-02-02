'use client';

import { useEffect, useState } from 'react';
import { ArrowLeft, Clock, CheckCircle2, AlertCircle, Loader2, Youtube, FileVideo, ChevronRight, Calendar, ChevronLeft, Trash2 } from 'lucide-react';
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

interface PaginationData {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState<PaginationData>({
    page: 1,
    limit: 20,
    total: 0,
    total_pages: 0,
  });
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  useEffect(() => {
    fetchJobs(pagination.page);
  }, []);

  const fetchJobs = async (page: number = 1) => {
    setLoading(true);
    try {
      const response = await fetch(getApiEndpoint(`/api/jobs?page=${page}&limit=${pagination.limit}`));
      const data = await response.json();
      setJobs(data.jobs);
      setPagination({
        page: data.page,
        limit: data.limit,
        total: data.total,
        total_pages: data.total_pages,
      });
    } catch (error) {
      toast.error('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    // First click shows confirmation
    if (deleteConfirmId !== jobId) {
      setDeleteConfirmId(jobId);
      return;
    }

    // Second click performs deletion
    setDeletingJobId(jobId);
    try {
      const response = await fetch(getApiEndpoint(`/api/jobs/${jobId}`), {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete job');
      }

      const result = await response.json();
      toast.success(`Job deleted successfully! ${result.files_deleted} files removed.`);
      
      // Refresh the job list
      await fetchJobs(pagination.page);
    } catch (error) {
      toast.error('Failed to delete job');
      console.error('Delete error:', error);
    } finally {
      setDeletingJobId(null);
      setDeleteConfirmId(null);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      fetchJobs(newPage);
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
            <>
              <div className="space-y-4">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className="relative bg-slate-900/40 backdrop-blur-md border border-white/5 hover:border-emerald-500/20 rounded-2xl p-6 transition-all duration-300 overflow-hidden"
                  >
                    <div className="relative flex flex-col md:flex-row md:items-center gap-6">
                      
                      {/* Icon & Source Info */}
                      <a
                        href={`/jobs/${job.id}`}
                        className="flex-1 min-w-0 group"
                      >
                        <div className="flex items-start gap-4">
                          <div className={`p-3 rounded-xl shrink-0 ${
                            job.source_type === 'youtube' 
                              ? 'bg-red-500/10 text-red-400' 
                              : 'bg-blue-500/10 text-blue-400'
                          }`}>
                            {job.source_type === 'youtube' ? <Youtube size={24} /> : <FileVideo size={24} />}
                          </div>
                          
                          <div className="space-y-1 min-w-0 flex-1">
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
                            
                            <h3 className="text-lg font-semibold text-white truncate pr-4 group-hover:text-emerald-400 transition-colors">
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
                      </a>

                      {/* Actions Section */}
                      <div className="w-full md:w-auto shrink-0 flex items-center gap-4">
                         {job.status === 'processing' ? (
                          <div className="flex-1 md:w-64 space-y-2">
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
                           <a 
                             href={`/jobs/${job.id}`}
                             className="flex items-center justify-end gap-2 text-emerald-400 text-sm font-medium hover:text-emerald-300 transition-colors"
                           >
                              <span>View Clips</span>
                              <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center hover:bg-emerald-500 hover:text-white transition-colors">
                                  <ChevronRight size={16} />
                              </div>
                           </a>
                         ) : null}
                         
                         {/* Delete Button */}
                         <button
                           onClick={(e) => {
                             e.preventDefault();
                             handleDeleteJob(job.id);
                           }}
                           disabled={deletingJobId === job.id}
                           className={`p-2 rounded-lg transition-all ${
                             deleteConfirmId === job.id
                               ? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
                               : 'bg-slate-800/50 text-slate-400 hover:bg-red-500/10 hover:text-red-400 border border-slate-700/50 hover:border-red-500/20'
                           }`}
                           title={deleteConfirmId === job.id ? "Click again to confirm" : "Delete job"}
                         >
                           {deletingJobId === job.id ? (
                             <Loader2 size={18} className="animate-spin" />
                           ) : (
                             <Trash2 size={18} />
                           )}
                         </button>
                      </div>

                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination Controls */}
              {pagination.total_pages > 1 && (
                <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900/40 backdrop-blur-md border border-white/5 rounded-xl p-4">
                  <div className="text-sm text-slate-400">
                    Showing {((pagination.page - 1) * pagination.limit) + 1} - {Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total} jobs
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePageChange(pagination.page - 1)}
                      disabled={pagination.page === 1}
                      className="p-2 rounded-lg bg-slate-800/50 text-slate-400 hover:bg-emerald-500/10 hover:text-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all border border-slate-700/50 hover:border-emerald-500/20"
                    >
                      <ChevronLeft size={18} />
                    </button>
                    
                    <div className="flex items-center gap-1">
                      {[...Array(pagination.total_pages)].map((_, i) => {
                        const page = i + 1;
                        // Show first, last, current, and adjacent pages
                        if (
                          page === 1 ||
                          page === pagination.total_pages ||
                          Math.abs(page - pagination.page) <= 1
                        ) {
                          return (
                            <button
                              key={page}
                              onClick={() => handlePageChange(page)}
                              className={`min-w-[40px] h-10 px-3 rounded-lg font-medium transition-all ${
                                page === pagination.page
                                  ? 'bg-emerald-500 text-white'
                                  : 'bg-slate-800/50 text-slate-400 hover:bg-emerald-500/10 hover:text-emerald-400 border border-slate-700/50 hover:border-emerald-500/20'
                              }`}
                            >
                              {page}
                            </button>
                          );
                        } else if (
                          page === pagination.page - 2 ||
                          page === pagination.page + 2
                        ) {
                          return <span key={page} className="text-slate-600 px-1">...</span>;
                        }
                        return null;
                      })}
                    </div>
                    
                    <button
                      onClick={() => handlePageChange(pagination.page + 1)}
                      disabled={pagination.page === pagination.total_pages}
                      className="p-2 rounded-lg bg-slate-800/50 text-slate-400 hover:bg-emerald-500/10 hover:text-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all border border-slate-700/50 hover:border-emerald-500/20"
                    >
                      <ChevronRight size={18} />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}