"use client";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetch("http://localhost:8000/api/admin/users")
      .then(r => r.json())
      .then(data => { setUsers(data.users || []); toast.success("Users loaded!"); })
      .catch(() => { setError("Failed to load users"); toast.error("Failed to load users"); })
      .finally(() => setLoading(false));
  }, [refresh]);

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-white">
      <h1 className="text-2xl font-bold mb-6">Admin User Management</h1>
      {error && <div className="text-red-400 mb-4">{error}</div>}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="w-full bg-slate-900 rounded-xl overflow-hidden">
          <thead>
            <tr className="bg-slate-800 text-emerald-300">
              <th className="p-3 text-left">ID</th>
              <th className="p-3 text-left">Email</th>
              <th className="p-3 text-left">Created</th>
              <th className="p-3 text-left">Is Admin</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b border-slate-800">
                <td className="p-3 font-mono text-xs">{u.id}</td>
                <td className="p-3">{u.email}</td>
                <td className="p-3">{u.created_at || "-"}</td>
                <td className="p-3">{u.is_admin ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
