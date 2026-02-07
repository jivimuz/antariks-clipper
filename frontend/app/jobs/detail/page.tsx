'use client';

import { useEffect, useState } from 'react';
import JobDetailClient from '../[id]/JobDetailClient';
import { Loader2, ArrowLeft } from 'lucide-react';

export default function JobDetailPage() {
  const [jobId, setJobId] = useState<string | null>(null);
  
  useEffect(() => {
    const storedJobId = localStorage.getItem('selectedJobId');
    
    if (storedJobId) {
      setJobId(storedJobId);
    } else {
      console.error('[JobDetail] No jobId found, redirecting...');
      setTimeout(() => {
        window.location.href = '/jobs';
      }, 2000);
    }
  }, []);
  
  if (!jobId) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-emerald-400 mx-auto" />
          <p className="text-slate-400">Loading job details...</p>
          <button
            onClick={() => window.location.href = '/jobs'}
            className="text-sm text-slate-500 hover:text-emerald-400 flex items-center gap-2 mx-auto"
          >
            <ArrowLeft size={16} />
            Back to Jobs
          </button>
        </div>
      </div>
    );
  }

  return <JobDetailClient jobId={jobId} />;
}
