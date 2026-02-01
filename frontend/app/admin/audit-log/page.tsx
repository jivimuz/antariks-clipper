"use client";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

export default function AdminAuditLogPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch("http://localhost:8000/api/admin/audit-logs")
      .then(r => r.json())
      .then(data => { setLogs(data.logs || []); toast.success("Audit logs loaded!"); })
      .catch(() => { setError("Failed to load audit logs"); toast.error("Failed to load audit logs"); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-white">
      <h1 className="text-2xl font-bold mb-6">Admin Audit Log</h1>
      {error && <div className="text-red-400 mb-4">{error}</div>}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="w-full bg-slate-900 rounded-xl overflow-hidden">
          <thead>
            <tr className="bg-slate-800 text-emerald-300">
              <th className="p-3 text-left">Time</th>
              <th className="p-3 text-left">User ID</th>
              <th className="p-3 text-left">Action</th>
              <th className="p-3 text-left">Detail</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id} className="border-b border-slate-800">
                <td className="p-3 font-mono text-xs">{log.created_at}</td>
                <td className="p-3">{log.user_id}</td>
                <td className="p-3">{log.action}</td>
                <td className="p-3">{log.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
