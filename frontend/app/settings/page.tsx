"use client";
import { useState } from "react";
import toast from "react-hot-toast";

export default function SettingsPage() {
  const [licenseKey, setLicenseKey] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem("license_key") || "" : ""
  );
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("license_key", licenseKey);
    setSaved(true);
    toast.success("License key saved!");
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="bg-slate-900/80 border border-white/10 rounded-2xl shadow-xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-center">Settings</h1>
        <form onSubmit={handleSave} className="space-y-6">
          <div>
            <label className="block text-slate-300 mb-2 font-medium">License Key</label>
            <input
              type="text"
              value={licenseKey}
              onChange={e => setLicenseKey(e.target.value)}
              className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none"
              placeholder="Paste your license key here"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-white font-bold disabled:opacity-60"
          >
            Save
          </button>
          {saved && <div className="text-emerald-400 text-center">License key saved!</div>}
        </form>
      </div>
    </div>
  );
}
