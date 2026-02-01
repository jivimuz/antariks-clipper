"use client";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { getApiEndpoint } from "@/lib/api";

export default function AdminLicensesPage() {
  const [licenses, setLicenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ user_email: "", max_usage: 10 });
  const [creating, setCreating] = useState(false);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetch(getApiEndpoint("/api/admin/licenses"))
      .then(r => r.json())
      .then(data => { setLicenses(data.licenses || []); toast.success("Licenses loaded!"); })
      .catch(() => { setError("Failed to load licenses"); toast.error("Failed to load licenses"); })
      .finally(() => setLoading(false));
  }, [refresh]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      const res = await fetch(getApiEndpoint("/api/admin/create-license"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });
      if (!res.ok) throw new Error("Failed to create license");
      toast.success("License created!");
      setForm({ user_email: "", max_usage: 10 });
      setRefresh(r => r + 1);
    } catch (e: any) {
      setError(e.message || "Failed to create license");
      toast.error(e.message || "Failed to create license");
    } finally {
      setCreating(false);
    }
  };

  const handleStatus = async (id: string, active: boolean) => {
    await fetch(getApiEndpoint("/api/admin/set-license-status"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ license_id: id, active })
    });
    toast.success("License status updated!");
    setRefresh(r => r + 1);
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-white">
      <h1 className="text-2xl font-bold mb-6">Admin License Management</h1>
      <form onSubmit={handleCreate} className="flex gap-4 mb-8">
        <input
          type="email"
          placeholder="User email"
          value={form.user_email}
          onChange={e => setForm(f => ({ ...f, user_email: e.target.value }))}
          className="px-4 py-2 rounded bg-slate-800 border border-slate-700 text-white"
          required
        />
        <input
          type="number"
          placeholder="Max Usage"
          value={form.max_usage}
          min={1}
          onChange={e => setForm(f => ({ ...f, max_usage: Number(e.target.value) }))}
          className="px-4 py-2 rounded bg-slate-800 border border-slate-700 text-white w-32"
          required
        />
        <button
          type="submit"
          disabled={creating}
          className="px-6 py-2 bg-emerald-600 rounded text-white font-bold disabled:opacity-60"
        >
          {creating ? "Creating..." : "Create License"}
        </button>
      </form>
      {error && <div className="text-red-400 mb-4">{error}</div>}
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="w-full bg-slate-900 rounded-xl overflow-hidden">
          <thead>
            <tr className="bg-slate-800 text-emerald-300">
              <th className="p-3 text-left">ID</th>
              <th className="p-3 text-left">User Email</th>
              <th className="p-3 text-left">Max Usage</th>
              <th className="p-3 text-left">Used</th>
              <th className="p-3 text-left">Active</th>
              <th className="p-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {licenses.map(l => (
              <tr key={l.id} className="border-b border-slate-800">
                <td className="p-3 font-mono text-xs">{l.id}</td>
                <td className="p-3">{l.user_email}</td>
                <td className="p-3">{l.max_usage}</td>
                <td className="p-3">{l.usage}</td>
                <td className="p-3">{l.active ? "Yes" : "No"}</td>
                <td className="p-3">
                  <button
                    onClick={() => handleStatus(l.id, !l.active)}
                    className={`px-4 py-1 rounded font-bold ${l.active ? "bg-red-600" : "bg-emerald-600"}`}
                  >
                    {l.active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
