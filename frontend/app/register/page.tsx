"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch("http://localhost:8000/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || "Registration failed");
        throw new Error(err.detail || "Registration failed");
      }
      toast.success("Registration successful! Please login.");
      setSuccess("Registration successful! Please login.");
      setTimeout(() => router.push("/login"), 1500);
    } catch (e: any) {
      setError(e.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <form onSubmit={handleRegister} className="bg-slate-900/80 border border-white/10 rounded-2xl shadow-xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-center">Register</h1>
        <div className="mb-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none mb-3"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="w-full px-4 py-2 rounded bg-slate-800 text-white border border-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none"
            required
          />
        </div>
        {/* {error && <div className="text-red-400 mb-4">{error}</div> } */}
        {/* {success && <div className="text-emerald-400 mb-4">{success}</div> } */}
        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-white font-bold disabled:opacity-60"
        >
          {loading ? "Registering..." : "Register"}
        </button>
      </form>
    </div>
  );
}
