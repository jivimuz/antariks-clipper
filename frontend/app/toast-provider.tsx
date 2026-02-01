"use client";
import { Toaster } from "react-hot-toast";

export function ToastProvider({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Toaster position="top-right" toastOptions={{
        style: { background: "#0f172a", color: "#fff" },
        success: { style: { background: "#059669", color: "#fff" } },
        error: { style: { background: "#dc2626", color: "#fff" } },
      }} />
      {children}
    </>
  );
}
