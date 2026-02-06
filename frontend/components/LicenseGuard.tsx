"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getApiEndpoint } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { LicenseStatus } from "@/types/license";
import toast from "react-hot-toast";

export default function LicenseGuard({ children }: { children: React.ReactNode }) {
  const [checking, setChecking] = useState(true);
  const [licenseValid, setLicenseValid] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const checkLicense = useCallback(async () => {
    try {
      setErrorMessage(null);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      // Use the unified validate endpoint with no body to check existing license
      const res = await fetch(getApiEndpoint("/api/license/validate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      const data: LicenseStatus = await res.json();

      if (!data.valid) {
        // Check if license is expired
        if (data.error?.toLowerCase().includes("expired")) {
          // Show expiry notification
          toast.error("Lisensi Anda telah berakhir.", {
            duration: 5000,
            position: "top-center"
          });
          
          // Redirect to license page
          router.push("/license");
          return;
        }
        
        // Redirect to license page if not valid
        router.push("/license");
        return;
      }

      // License is valid - check if expiring soon
      if (data.expiringSoon && data.daysRemaining !== null && data.daysRemaining !== undefined) {
        const daysText = data.daysRemaining === 0 
          ? "hari ini" 
          : data.daysRemaining === 1 
            ? "besok" 
            : `${data.daysRemaining} hari lagi`;
        
        toast(`Lisensi Anda akan berakhir ${daysText}. Segera perpanjang lisensi Anda.`, {
          duration: 8000,
          icon: "⚠️",
          style: {
            background: "#713f12",
            color: "#fef3c7",
            border: "1px solid #f59e0b",
          }
        });
      }

      setLicenseValid(true);
    } catch (error) {
      console.error("License check failed:", error);
      setErrorMessage("Backend tidak dapat diakses.");
    } finally {
      setChecking(false);
    }
  }, [router]);

  useEffect(() => {
    // Skip check for license page
    if (pathname === "/license") {
      setChecking(false);
      setLicenseValid(true);
      return;
    }

    checkLicense();
  }, [pathname, checkLicense]);

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
          <span>Verifying license...</span>
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-slate-900/70 border border-white/10 rounded-2xl p-6 text-center">
          <div className="text-red-400 text-sm font-semibold mb-2">Backend Error</div>
          <p className="text-slate-300 text-sm mb-4">{errorMessage}</p>
          <button
            onClick={() => {
              setChecking(true);
              checkLicense();
            }}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium"
          >
            Coba lagi
          </button>
        </div>
      </div>
    );
  }

  if (!licenseValid && pathname !== "/license") {
    return null; // Will redirect
  }

  return <>{children}</>;
}
