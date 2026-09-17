"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setStoredAuth, PRESET_DEMO_ACCOUNTS } from "../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Invalid username or password. Please try again.");
      }

      const data = await res.json();
      setStoredAuth(data.access_token, data.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to sign in.");
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (uname: string, pwd: string = "Demo@123") => {
    setUsername(uname);
    setPassword(pwd);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#070b10] flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glow styling */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-blue-500/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Header / Branding */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center z-10">
        <div className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mb-4">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>SIH26102 • PHASE 2 EVALUATION</span>
        </div>

        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl flex items-center justify-center gap-3">
          <span className="h-3 w-3 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]" />
          NIREEKSHAK
        </h1>
        <p className="mt-1 text-xs uppercase tracking-[0.25em] text-slate-400 font-medium">
          MPLADS Risk Intelligence Platform
        </p>
      </div>

      {/* Login Card */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10">
        <div className="bg-[#0e1622]/90 border border-slate-800/80 backdrop-blur-xl py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          <form className="space-y-5" onSubmit={handleLogin}>
            {error && (
              <div className="rounded-lg bg-rose-500/10 border border-rose-500/30 p-3 text-xs text-rose-300 flex items-center gap-2">
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider">
                Email / User ID
              </label>
              <div className="mt-1.5">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. mp.demo or authority.demo"
                  className="w-full rounded-lg border border-slate-700/80 bg-[#121c2a] px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <span className="text-[11px] text-slate-500 font-mono">Default: Demo@123</span>
              </div>
              <div className="mt-1.5 relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-slate-700/80 bg-[#121c2a] pr-10 pl-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-200"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-700 bg-[#121c2a] text-emerald-500 focus:ring-emerald-500"
                />
                <span>Remember this session</span>
              </label>
              <button
                type="button"
                onClick={() => alert("Password reset is managed by the System Administrator (CAG Vigilance Unit). Please contact admin@nireekshak.gov.in.")}
                className="text-xs text-emerald-400/80 hover:text-emerald-300 transition"
              >
                Forgot password?
              </button>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 rounded-lg shadow-sm text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition disabled:opacity-50"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Signing in...</span>
                  </span>
                ) : (
                  "Authenticate & Access System"
                )}
              </button>
            </div>
          </form>

          {/* QUICK DEMO ACCOUNTS STRIP */}
          <div className="mt-7 pt-6 border-t border-slate-800/80">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 text-center mb-3">
              One-Click Evaluator Demo Accounts
            </p>
            <div className="grid grid-cols-2 gap-2">
              {PRESET_DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.username}
                  type="button"
                  onClick={() => quickFill(acc.username)}
                  className="text-left p-2 rounded-lg border border-slate-800 bg-[#121b27] hover:border-emerald-500/50 hover:bg-[#162333] transition group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-200 group-hover:text-emerald-400">
                      {acc.roleLabel}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                      DEMO
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">{acc.name}</p>
                  <p className="text-[9px] font-mono text-slate-500">{acc.username}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-500 mt-6">
          Authorized government access only. All actions are cryptographically hashed and logged to the digital audit trail.
        </p>
      </div>
    </div>
  );
}
