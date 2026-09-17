"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { getStoredUser, logout, PRESET_DEMO_ACCOUNTS, setStoredAuth } from "../lib/auth";

export default function RoleSwitcher() {
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [showModal, setShowModal] = useState(false);
  const [loadingUser, setLoadingUser] = useState<string | null>(null);

  useEffect(() => {
    const handleAuth = () => setCurrentUser(getStoredUser());
    window.addEventListener("nireekshak_auth_changed", handleAuth);
    return () => window.removeEventListener("nireekshak_auth_changed", handleAuth);
  }, []);

  const switchAccount = async (username: string) => {
    setLoadingUser(username);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: "Demo@123" })
      });
      if (res.ok) {
        const data = await res.json();
        setStoredAuth(data.access_token, data.user);
        setShowModal(false);
        // Refresh page data to reflect new role
        window.location.reload();
      }
    } catch (err) {
      console.error("Failed to switch demo account:", err);
    } finally {
      setLoadingUser(null);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "MP":
        return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
      case "APPROVING_AUTHORITY":
        return "bg-blue-500/15 text-blue-300 border-blue-500/30";
      case "CONTRACTOR":
        return "bg-amber-500/15 text-amber-300 border-amber-500/30";
      case "FIELD_OFFICER":
        return "bg-purple-500/15 text-purple-300 border-purple-500/30";
      case "AUDITOR":
        return "bg-rose-500/15 text-rose-300 border-rose-500/30";
      default:
        return "bg-indigo-500/15 text-indigo-300 border-indigo-500/30";
    }
  };

  return (
    <>
      <div className="flex items-center gap-2.5">
        {/* User Profile Pill */}
        <div className="flex items-center gap-2.5 rounded-lg border border-slate-800 bg-[#0e1622] px-3.5 py-1.5 shadow-sm">
          <div className="flex flex-col text-right">
            <span className="text-xs font-semibold text-white tracking-wide">
              {currentUser.full_name}
            </span>
            <div className="flex items-center justify-end gap-1.5 mt-0.5">
              <span
                className={`inline-block px-1.5 py-0.2 rounded border text-[10px] font-medium uppercase tracking-wider ${getRoleBadgeColor(
                  currentUser.role
                )}`}
              >
                {currentUser.role.replace("_", " ")}
              </span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                DEMO
              </span>
            </div>
          </div>

          <button
            onClick={() => setShowModal(true)}
            title="Switch demo account for SIH presentation"
            className="rounded-md border border-slate-700/80 bg-slate-800/80 hover:bg-slate-700 hover:text-white px-2 py-1 text-[11px] font-medium text-slate-300 transition"
          >
            Switch Role
          </button>

          <button
            onClick={logout}
            title="Log out of session"
            className="rounded-md border border-slate-700/80 bg-slate-800/80 hover:bg-rose-950/40 hover:border-rose-800/50 hover:text-rose-300 px-2 py-1 text-[11px] font-medium text-slate-400 transition"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Switch Demo Account Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-[#0e1724] p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white">Switch Evaluator Persona</h3>
                <p className="text-xs text-slate-400">Select an official role to evaluate permissions & workflow</p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ×
              </button>
            </div>

            <div className="mt-4 space-y-2.5">
              {PRESET_DEMO_ACCOUNTS.map((acc) => {
                const isSelected = currentUser.username === acc.username;
                return (
                  <button
                    key={acc.username}
                    type="button"
                    disabled={loadingUser !== null}
                    onClick={() => switchAccount(acc.username)}
                    className={`w-full text-left p-3 rounded-xl border transition flex items-center justify-between ${
                      isSelected
                        ? "border-emerald-500/60 bg-emerald-950/20 text-white"
                        : "border-slate-800 bg-[#121c2a] hover:border-slate-700 hover:bg-[#152335] text-slate-300"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">{acc.name}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                          {acc.roleLabel}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">{acc.designation}</p>
                      <p className="text-[10px] font-mono text-slate-500">{acc.officialId}</p>
                    </div>

                    {loadingUser === acc.username ? (
                      <span className="h-4 w-4 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
                    ) : isSelected ? (
                      <span className="text-xs font-semibold text-emerald-400">Active</span>
                    ) : (
                      <span className="text-xs text-slate-500">Select →</span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-5 pt-4 border-t border-slate-800 flex justify-end">
              <Link
                href="/login"
                onClick={() => setShowModal(false)}
                className="text-xs text-emerald-400 hover:underline mr-auto"
              >
                Go to Dedicated Login Page →
              </Link>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-xs text-slate-300 hover:text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
