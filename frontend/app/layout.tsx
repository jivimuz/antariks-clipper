
import type { Metadata } from "next";
import "./globals.css";
import { ToastProvider } from "./toast-provider";
import LicenseGuard from "@/components/LicenseGuard";

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
          <LicenseGuard>
            {children}
          </LicenseGuard>
        </ToastProvider>
      </body>
    </html>
  );
}
