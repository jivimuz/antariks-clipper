
import type { Metadata } from "next";
import "./globals.css";
import { ToastProvider } from "./toast-provider";
import LicenseGuard from "@/components/LicenseGuard";
import { DownloadProvider } from "@/contexts/DownloadContext";
import { JobProcessProvider } from "@/contexts/JobProcessContext";
import FloatingDownloadManager from "@/components/FloatingDownloadManager";
import FloatingJobProcess from "@/components/FloatingJobProcess";

export const metadata: Metadata = {
  title: "Antariks Clipper",
  description: "Auto-generate viral highlight clips for Reels & TikTok",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ToastProvider>
          <DownloadProvider>
            <JobProcessProvider>
              <LicenseGuard>
                {children}
              </LicenseGuard>
              <FloatingJobProcess />
              <FloatingDownloadManager />
            </JobProcessProvider>
          </DownloadProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
