"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AccountPage() {
  const [email, setEmail] = useState("");
  const [licenses, setLicenses] = useState<any[]>([]);
  const [licenseKey, setLicenseKey] = useState("");
  const [licenseStatus, setLicenseStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    const storedEmail = localStorage.getItem("user_email");
    if (storedEmail) setEmail(storedEmail);
  }, []);

  const fetchLicenses = async () => {
    if (!email) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`http://localhost:8000/api/user/licenses?email=${encodeURIComponent(email)}`);
      if (!res.ok) throw new Error("Failed to fetch licenses");
      const data = await res.json();
      setLicenses(data);
    } catch (e: any) {
      setError(e.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (email) fetchLicenses();
  }, [email]);

  const handleValidateLicense = async (e: React.FormEvent) => {
    e.preventDefault();
    setLicenseStatus(null);
    setError("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/license/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: licenseKey })
      });
      if (!res.ok) throw new Error("Invalid or inactive license");
      const data = await res.json();
      setLicenseStatus(data);
      localStorage.setItem("license_key", licenseKey);
    } catch (e: any) {
      setError(e.message || "License validation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-4">
      <div className="bg-slate-900/80 border border-white/10 rounded-2xl shadow-xl p-8 w-full max-w-lg">
        <h1 className="text-2xl font-bold mb-6 text-center">Account & License</h1>
        <div className="mb-6">
          <div className="mb-2 text-slate-400">Logged in as:</div>
          <div className="font-mono text-emerald-400 mb-2">{email || "-"}</div>
          <button
            onClick={() => { localStorage.clear(); router.push("/login"); }}
            className="text-sm text-red-400 underline hover:text-red-300 mb-4"
          >Logout</button>
        </div>
        <form onSubmit={handleValidateLicense} className="mb-6">
          <div className="mb-2 text-slate-400">Enter License Key</div>
          <input
            type="text"
            placeholder="Paste your license key"
            value={licenseKey}
            onChange={e => setLicenseKey(e.target.value)}
            className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none mb-2"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-white font-bold disabled:opacity-60"
          >
            {loading ? "Validating..." : "Validate License"}
          </button>
        </form>
        {licenseStatus && (
          <div className="mb-4 p-3 rounded bg-emerald-900/30 border border-emerald-500/20 text-emerald-300">
            License valid! Plan: <b>{licenseStatus.plan}</b>
          </div>
        )}
        {error && <div className="text-red-400 mb-4">{error}</div>}
        <div className="mt-4">
          <h2 className="text-lg font-semibold mb-2">Your Licenses</h2>
          <div className="space-y-3">
            {licenses.map(lic => (
              <div key={lic.key} className="bg-slate-800 rounded-xl p-4 border border-white/10">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <div className="text-xs text-slate-400">Key</div>
                    <div className="font-mono text-emerald-400 break-all">{lic.key}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Plan</div>
                    <div className="font-bold">{lic.plan}</div>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-300">
                  <div>Active: <span className={lic.is_active ? "text-emerald-400" : "text-red-400"}>{lic.is_active ? "Yes" : "No"}</span></div>
                  <div>Usage: {lic.usage_count} / {lic.usage_limit ?? "∞"}</div>
                  {lic.expires_at && <div>Expires: {lic.expires_at.split("T")[0]}</div>}
                </div>
              </div>
            ))}
            {licenses.length === 0 && <div className="text-slate-500">No licenses found.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
