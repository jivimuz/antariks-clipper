"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { getApiEndpoint } from "@/lib/api";
import { Key, Loader2, CheckCircle2, AlertCircle, Shield } from "lucide-react";

export default function LicensePage() {
  const [licenseKey, setLicenseKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [error, setError] = useState("");
  const [licenseStatus, setLicenseStatus] = useState<any>(null);
  const router = useRouter();

  // Check license status on mount
  useEffect(() => {
    checkLicenseStatus();
  }, []);

  const checkLicenseStatus = async () => {
    try {
      const res = await fetch(getApiEndpoint("/api/license/status"));
      const data = await res.json();
      setLicenseStatus(data);
      
      // If already activated and valid, redirect to home
      if (data.activated && data.valid) {
        toast.success("License already activated!");
        router.push("/");
      }
    } catch (e) {
      console.error("Failed to check license status:", e);
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!licenseKey.trim()) {
      setError("Please enter a license key");
      toast.error("Please enter a license key");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      const res = await fetch(getApiEndpoint("/api/license/activate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ license_key: licenseKey })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || data.error || "Invalid license key");
      }
      
      if (data.success) {
        toast.success(`License activated for ${data.owner}!`);
        // Redirect to home after successful activation
        setTimeout(() => {
          router.push("/");
        }, 1000);
      } else {
        throw new Error(data.error || "Invalid license key");
      }
    } catch (e: any) {
      const errorMsg = e.message || "License activation failed";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (checkingStatus) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
          <span>Checking license status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 relative overflow-hidden flex items-center justify-center p-4 selection:bg-emerald-500/30">
      {/* Background Effects */}
      <div className="absolute top-0 -left-4 w-96 h-96 bg-emerald-600/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 -right-4 w-96 h-96 bg-teal-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-500/20 rounded-full mb-4 border border-emerald-500/50">
            <Shield size={32} className="text-emerald-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">License Activation</h1>
          <p className="text-slate-400">
            Enter your license key to activate Antariks Clipper
          </p>
        </div>

        {/* License Status Display (if checking and invalid) */}
        {licenseStatus && licenseStatus.activated && !licenseStatus.valid && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-red-400 font-medium">License Invalid</p>
                <p className="text-red-400/80 text-sm mt-1">
                  {licenseStatus.error || "Your license is not valid. Please enter a new license key."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Activation Form */}
        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-8 ring-1 ring-white/5">
          <form onSubmit={handleActivate} className="space-y-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-emerald-100/80 ml-1">
                License Key
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-emerald-400 transition-colors">
                  <Key size={20} />
                </div>
                <input
                  type="text"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  className="w-full pl-12 pr-4 py-4 bg-slate-950/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-600 focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all outline-none"
                  disabled={loading}
                  required
                />
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 animate-in fade-in slide-in-from-top-2">
                <AlertCircle size={20} className="shrink-0 mt-0.5" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold rounded-xl hover:from-emerald-500 hover:to-teal-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-900/20 hover:shadow-emerald-900/40 hover:-translate-y-0.5 active:translate-y-0 overflow-hidden"
            >
              <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 blur-md rounded-xl" />
              <span className="relative z-10 flex items-center gap-2">
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Activating...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={20} />
                    Activate License
                  </>
                )}
              </span>
            </button>
          </form>

          {/* Help Text */}
          <div className="mt-6 pt-6 border-t border-white/5">
            <p className="text-sm text-slate-500 text-center">
              Don't have a license?{" "}
              <a
                href="https://antariks.id"
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-400 hover:text-emerald-300 font-medium"
              >
                Purchase one here
              </a>
            </p>
          </div>
        </div>

        {/* Back to Home Link */}
        <div className="mt-6 text-center">
          <button
            onClick={() => router.push("/")}
            className="text-sm text-slate-500 hover:text-slate-400 transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
