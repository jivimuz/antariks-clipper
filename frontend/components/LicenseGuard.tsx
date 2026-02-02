"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getApiEndpoint } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { LicenseStatus } from "@/types/license";

export default function LicenseGuard({ children }: { children: React.ReactNode }) {
  const [checking, setChecking] = useState(true);
  const [licenseValid, setLicenseValid] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const checkLicense = useCallback(async () => {
    try {
      // Use the unified validate endpoint with no body to check existing license
      const res = await fetch(getApiEndpoint("/api/license/validate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();

      if (!data.valid) {
        // Redirect to license page if not valid
        router.push("/license");
        return;
      }

      setLicenseValid(true);
    } catch (error) {
      console.error("License check failed:", error);
      // On error, redirect to license page
      router.push("/license");
    } finally {
      setChecking(false);
    }
  }, [router]);

  useEffect(() => {
    // Skip check for license page itself
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

  if (!licenseValid && pathname !== "/license") {
    return null; // Will redirect
  }

  return <>{children}</>;
}
