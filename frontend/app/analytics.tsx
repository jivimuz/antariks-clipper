"use client";
import { useEffect, useState } from "react";

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/analytics")
      .then((res) => res.json())
      .then((d) => setData(d))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-10 text-center text-emerald-400">Loading analytics...</div>;
  if (!data) return <div className="p-10 text-center text-red-400">Failed to load analytics.</div>;

  return (
    <div className="max-w-3xl mx-auto p-8 text-white">
      <h1 className="text-3xl font-bold mb-6">Analytics</h1>
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-800 rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-emerald-400">{data.total_jobs}</div>
          <div className="text-slate-400 mt-2">Total Jobs</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-blue-400">{data.total_clips}</div>
          <div className="text-slate-400 mt-2">Total Clips</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-teal-400">{data.total_renders}</div>
          <div className="text-slate-400 mt-2">Total Renders</div>
        </div>
      </div>
      <h2 className="text-xl font-semibold mb-2 mt-8">Latest Jobs</h2>
      <ul className="mb-8">
        {data.latest_jobs.map((job: any) => (
          <li key={job.id} className="mb-1 text-slate-300">
            <span className="font-mono text-emerald-400">{job.id.slice(0,8)}</span> - {job.status} - {job.source_type}
          </li>
        ))}
      </ul>
      <h2 className="text-xl font-semibold mb-2 mt-8">Latest Clips</h2>
      <ul>
        {data.latest_clips.map((clip: any) => (
          <li key={clip.id} className="mb-1 text-slate-300">
            <span className="font-mono text-blue-400">{clip.id.slice(0,8)}</span> - {clip.title} ({clip.start_sec} - {clip.end_sec}s)
          </li>
        ))}
      </ul>
    </div>
  );
}
