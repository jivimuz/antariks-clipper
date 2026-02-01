"use client";
import { useState } from "react";
import toast from "react-hot-toast";
import { getApiEndpoint } from "../lib/api";

export default function ResetPasswordPage() {
  const [step, setStep] = useState<"request" | "confirm">("request");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(getApiEndpoint("/api/password-reset/request"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Request failed");
      toast.success("Token generated! Silakan cek email Anda.");
      setMessage("Token generated: " + data.token + " (for demo, check your email in production)");
      setStep("confirm");
    } catch (e: any) {
      toast.error(e.message || "Request failed");
      setError(e.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(getApiEndpoint("/api/password-reset/confirm"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Reset failed");
      toast.success("Password reset successful! Silakan login.");
      setMessage("Password reset successful! You can now login.");
    } catch (e: any) {
      toast.error(e.message || "Reset failed");
      setError(e.message || "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="bg-slate-900/80 border border-white/10 rounded-2xl shadow-xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-center">Reset Password</h1>
        {step === "request" && (
          <form onSubmit={handleRequest} className="space-y-4">
            <input
              type="email"
              placeholder="Your email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-white font-bold disabled:opacity-60"
            >
              {loading ? "Requesting..." : "Request Reset"}
            </button>
          </form>
        )}
        {step === "confirm" && (
          <form onSubmit={handleConfirm} className="space-y-4">
            <input
              type="text"
              placeholder="Reset token"
              value={token}
              onChange={e => setToken(e.target.value)}
              className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none"
              required
            />
            <input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-white font-bold disabled:opacity-60"
            >
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          </form>
        )}
        {/* {error && <div className="text-red-400 mb-4">{error}</div>} */}
        {/* {message && <div className="text-emerald-400 mb-4">{message}</div>} */}
      </div>
    </div>
  );
}
