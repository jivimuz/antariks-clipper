'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Job {
  id: string;
  source_type: string;
  source_url?: string;
  status: string;
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
      const response = await fetch('http://localhost:8000/api/jobs');
      const data = await response.json();
      setJobs(data.jobs);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <Link
              href="/"
              className="text-purple-600 hover:text-purple-700 dark:text-purple-400 font-medium"
            >
              ← Back to Home
            </Link>
          </div>

          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">
            All Jobs
          </h1>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading jobs...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-12 text-center">
              <p className="text-gray-600 dark:text-gray-400 text-lg">
                No jobs yet. Create your first highlight!
              </p>
              <Link
                href="/"
                className="inline-block mt-6 px-6 py-3 bg-purple-500 text-white font-semibold rounded-lg hover:bg-purple-600"
              >
                Create Job
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="block bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                            job.status
                          )}`}
                        >
                          {job.status}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {job.source_type}
                        </span>
                      </div>
                      {job.source_url && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 truncate max-w-2xl">
                          {job.source_url}
                        </p>
                      )}
                      {job.step && (
                        <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                          Step: {job.step}
                        </p>
                      )}
                      {job.error && (
                        <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                          Error: {job.error}
                        </p>
                      )}
                    </div>
                    <div className="ml-4">
                      {job.status === 'processing' && (
                        <div className="text-right">
                          <div className="text-2xl font-bold text-purple-600">
                            {job.progress}%
                          </div>
                          <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full mt-2">
                            <div
                              className="h-full bg-purple-500 rounded-full transition-all"
                              style={{ width: `${job.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
