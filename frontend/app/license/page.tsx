"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { getApiEndpoint } from "@/lib/api";
import { Key, Loader2, CheckCircle2, AlertCircle, Shield } from "lucide-react";
import { LicenseStatus, LicenseActivationResponse } from "@/types/license";

export default function LicensePage() {
  const [licenseKey, setLicenseKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [error, setError] = useState("");
  const [licenseStatus, setLicenseStatus] = useState<LicenseStatus | null>(null);
  const [isEditingLicense, setIsEditingLicense] = useState(false);
  const router = useRouter();

  // Check license status on mount
  useEffect(() => {
    checkLicenseStatus();
  }, []);

  const checkLicenseStatus = async () => {
    try {
      // Use the unified validate endpoint with no body to check existing license
      const res = await fetch(getApiEndpoint("/api/license/validate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      
      // Save status for display (both valid and invalid)
      if (data.valid) {
        setLicenseStatus({
          licenseKey: data.licenseKey || "",
          activated: true,
          valid: data.valid,
          owner: data.owner,
          expires: data.expires
        });
      } else if (data.error) {
        setLicenseStatus({
          licenseKey: "",
          activated: true,
          valid: false,
          error: data.error
        });
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
      // Use the unified validate endpoint with license_key to activate
      const res = await fetch(getApiEndpoint("/api/license/validate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ license_key: licenseKey })
      });
      
      const data = await res.json();
      
      if (data.valid) {
        toast.success(`License updated for ${data.owner}!`);
        // Update license status immediately
        setLicenseStatus({
          licenseKey: licenseKey,
          activated: true,
          valid: true,
          owner: data.owner,
          expires: data.expires
        });
        // Reset edit mode and input
        setIsEditingLicense(false);
        setLicenseKey("");
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
          <h1 className="text-3xl font-bold text-white mb-2">License Management</h1>
          <p className="text-slate-400">
            {licenseStatus?.valid ? "Manage your Antariks Clipper license" : "Enter your license key to activate Antariks Clipper"}
          </p>
        </div>

        {/* Active License Display */}
        {licenseStatus && licenseStatus.activated && licenseStatus.valid && !isEditingLicense && (
          <div className="mb-6 p-6 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl">
            <div className="flex items-start gap-3 mb-4">
              <CheckCircle2 size={24} className="text-emerald-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-emerald-400 font-bold text-lg">License Active</p>
                <p className="text-emerald-400/80 text-sm mt-1">
                  Your license is valid and active
                </p>
              </div>
            </div>
            <div className="space-y-3 pl-9 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 text-sm">License Key</span>
                <span className="text-white font-medium font-mono text-sm">
                  {licenseStatus.licenseKey ? 
                    licenseStatus.licenseKey.substring(0, 4) + "****" + licenseStatus.licenseKey.slice(-4)
                    : "N/A"
                  }
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 text-sm">Owner</span>
                <span className="text-white font-medium">{licenseStatus.owner}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 text-sm">Expires</span>
                <span className="text-white font-medium">
                  {new Date(licenseStatus.expires || "").toLocaleDateString("id-ID", {
                    day: "numeric",
                    month: "long",
                    year: "numeric"
                  })}
                </span>
              </div>
            </div>
            <div className="flex gap-2 pt-4 border-t border-emerald-500/20">
              <button
                onClick={() => setIsEditingLicense(true)}
                className="flex-1 py-2 px-4 bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-400 text-sm font-medium rounded-lg transition-colors"
              >
                Change License
              </button>
              <button
                onClick={() => router.push("/")}
                className="flex-1 py-2 px-4 bg-slate-700/30 hover:bg-slate-700/50 text-slate-400 text-sm font-medium rounded-lg transition-colors"
              >
                Back Home
              </button>
            </div>
          </div>
        )}

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
          {/* Only show form if no valid license or editing license */}
          {(!licenseStatus || !licenseStatus.valid || isEditingLicense) && (
            <form onSubmit={handleActivate} className="space-y-6">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-emerald-100/80 ml-1">
                  {isEditingLicense ? "New License Key" : "License Key"}
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
                    autoFocus={isEditingLicense}
                  />
                </div>
              </div>

              {error && (
                <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 animate-in fade-in slide-in-from-top-2">
                  <AlertCircle size={20} className="shrink-0 mt-0.5" />
                  <span className="text-sm font-medium">{error}</span>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 group relative flex items-center justify-center gap-3 py-4 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold rounded-xl hover:from-emerald-500 hover:to-teal-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-900/20 hover:shadow-emerald-900/40 hover:-translate-y-0.5 active:translate-y-0 overflow-hidden"
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
                        {isEditingLicense ? "Update License" : "Activate License"}
                      </>
                    )}
                  </span>
                </button>
                {isEditingLicense && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingLicense(false);
                      setLicenseKey("");
                      setError("");
                    }}
                    disabled={loading}
                    className="px-6 py-4 bg-slate-700/30 hover:bg-slate-700/50 text-slate-400 font-bold rounded-xl transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          )}

          {/* Show message if license is valid and not editing */}
          {licenseStatus && licenseStatus.valid && !isEditingLicense && (
            <div className="text-center space-y-4">
              <p className="text-slate-400">
                Your license is active and valid.
              </p>
            </div>
          )}

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
