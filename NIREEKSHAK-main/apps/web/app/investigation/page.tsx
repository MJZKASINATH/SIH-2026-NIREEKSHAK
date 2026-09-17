"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Sidebar from "../../components/Sidebar";
import RoleSwitcher from "../../components/RoleSwitcher";
import { getStoredUser, canManageInvestigation, getAuthHeaders } from "../../lib/auth";

export default function InvestigationPage() {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [selectedCase, setSelectedCase] = useState<any | null>(null);
  const [actionModalCase, setActionModalCase] = useState<any | null>(null);
  const [actionType, setActionType] = useState("NOTE");
  const [noteText, setNoteText] = useState("");
  const [submittingAction, setSubmittingAction] = useState(false);

  useEffect(() => {
    const handleAuth = () => setCurrentUser(getStoredUser());
    window.addEventListener("nireekshak_auth_changed", handleAuth);
    return () => window.removeEventListener("nireekshak_auth_changed", handleAuth);
  }, []);

  const loadCases = () => {
    setLoading(true);
    fetch("/api/investigations")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setCases(data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load investigation cases:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleActionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionModalCase || !noteText.trim()) return;
    setSubmittingAction(true);

    try {
      const res = await fetch(`/api/investigations/${actionModalCase.case_id}/action`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          author_name: currentUser.full_name,
          role: currentUser.role,
          note_text: noteText.trim(),
          action_type: actionType
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Action failed");
      }

      alert(`Investigation action '${actionType}' recorded and logged to immutable audit trail.`);
      setActionModalCase(null);
      setNoteText("");
      loadCases();
    } catch (err: any) {
      alert(err.message || "Failed to record action.");
    } finally {
      setSubmittingAction(false);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case "OPEN":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "UNDER_REVIEW":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "CLARIFICATION_REQUESTED":
        return "bg-sky-500/20 text-sky-300 border-sky-500/40";
      case "FIELD_INSPECTION":
        return "bg-purple-500/20 text-purple-300 border-purple-500/40";
      case "RESOLVED":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      case "ESCALATED":
        return "bg-red-600 text-white font-black";
      default:
        return "bg-slate-800 text-slate-400 border-slate-700";
    }
  };

  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden">
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-6 md:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-[11px] font-medium tracking-[0.32em] text-rose-400 uppercase">
                Vigilance & Audit Command
              </div>
              <h1 className="mt-1 text-3xl font-bold tracking-tight text-white md:text-4xl">
                Investigation Queue
              </h1>
              <p className="mt-1 text-xs text-slate-400">
                Prioritized queue of red-flagged MPLADS works requiring formal administrative inquiry and evidence review
              </p>
            </div>
            <RoleSwitcher />
          </div>

          {/* METRIC STRIP */}
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Total Cases</span>
              <p className="text-xl font-bold text-white mt-0.5">{cases.length}</p>
            </div>
            <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-3.5">
              <span className="text-[10px] uppercase text-rose-400 font-medium">Active Inquiries</span>
              <p className="text-xl font-bold text-rose-400 mt-0.5">
                {cases.filter((c) => c.status !== "RESOLVED" && c.status !== "DISMISSED").length}
              </p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Flagged Works Value</span>
              <p className="text-xl font-bold text-sky-400 mt-0.5">
                ₹{(cases.reduce((acc, c) => acc + (c.allocated_amount || 0), 0) / 10000000).toFixed(2)} Cr
              </p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">AI Red Flag Threshold</span>
              <p className="text-xl font-bold text-emerald-400 mt-0.5">≥ 80 / 100</p>
            </div>
          </div>
        </header>

        <section className="p-6 md:p-8 space-y-6">
          {loading ? (
            <div className="p-12 text-center text-slate-400">
              <span className="h-6 w-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin inline-block mb-2" />
              <p className="text-xs font-mono">Loading investigation cases from database...</p>
            </div>
          ) : cases.length === 0 ? (
            <div className="rounded-xl border border-slate-800 bg-[#0e1622] p-12 text-center">
              <span className="text-4xl">🛡️</span>
              <h3 className="mt-3 text-lg font-bold text-white">No Open Investigation Cases</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                No projects have triggered critical red-flag thresholds (≥80/100). All ongoing MPLADS works are executing within nominal anomaly bounds.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {cases.map((c) => (
                <div
                  key={c.case_id}
                  className="rounded-xl border border-slate-800 bg-[#0e1622] hover:border-slate-700 transition p-5 shadow-lg space-y-4"
                >
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2.5">
                        <span className="px-2 py-0.5 rounded bg-rose-600 text-white text-xs font-black font-mono">
                          {c.case_id}
                        </span>
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${getStatusBadge(c.status)}`}>
                          {c.status.replace("_", " ")}
                        </span>
                        <span className="text-xs text-slate-500 font-mono">• Project: {c.project_id}</span>
                      </div>
                      <h3 className="text-base font-bold text-white">{c.project_title}</h3>
                      <p className="text-xs text-slate-400">
                        📍 {c.constituency}, {c.state} • Vendor: <strong className="text-slate-300">{c.contractor_name}</strong>
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="text-[10px] text-slate-500 uppercase font-mono">Risk Fusion</span>
                        <div className="text-xl font-black text-rose-400">{c.risk_score}/100</div>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <Link
                          href={`/projects/${c.project_id}?tab=investigation`}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition text-center shadow"
                        >
                          Open Digital File →
                        </Link>

                        {canManageInvestigation(currentUser.role) && (
                          <button
                            onClick={() => setActionModalCase(c)}
                            className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
                          >
                            Add Finding / Action
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Financial & Anomaly Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-3 border-t border-slate-800/80 text-xs">
                    <div className="rounded-lg bg-[#121c2a] p-2.5">
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Financial Allocation</span>
                      <p className="font-bold text-white mt-0.5">
                        ₹{(c.allocated_amount || 0).toLocaleString("en-IN")}
                      </p>
                      <span className="text-[10px] text-slate-400">
                        Spent: ₹{(c.expenditure_amount || 0).toLocaleString("en-IN")}
                      </span>
                    </div>

                    <div className="rounded-lg bg-[#121c2a] p-2.5">
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Assigned Auditor</span>
                      <p className="font-bold text-slate-200 mt-0.5 truncate">{c.assigned_to}</p>
                      <span className="text-[10px] text-slate-400 font-mono">
                        Opened: {new Date(c.opened_at).toLocaleDateString("en-IN")}
                      </span>
                    </div>

                    <div className="rounded-lg bg-[#121c2a] p-2.5">
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Case Findings Summary</span>
                      <p className="text-[11px] text-slate-300 mt-0.5 line-clamp-2">
                        {c.findings || c.summary}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* AUDITOR ACTION MODAL */}
      {actionModalCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0e1724] p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white">Record Investigation Action</h3>
                <p className="text-xs text-slate-400 font-mono">{actionModalCase.case_id} • {actionModalCase.project_id}</p>
              </div>
              <button
                onClick={() => setActionModalCase(null)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleActionSubmit} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Select Action Type</label>
                <select
                  value={actionType}
                  onChange={(e) => setActionType(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-[#121c2a] px-3 py-2 text-white focus:border-emerald-500 focus:outline-none"
                >
                  <option value="NOTE">General Investigator Note</option>
                  <option value="CLARIFICATION_REQUEST">Request Clarification from Agency</option>
                  <option value="INSPECTION_SCHEDULED">Schedule Physical Site Re-Inspection</option>
                  <option value="ESCALATION">Escalate to Vigilance Directorate</option>
                  <option value="RESOLUTION">Resolve & Close Investigation</option>
                  <option value="DISMISS">Dismiss Case (False Positive)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Official Findings / Remarks</label>
                <textarea
                  rows={4}
                  required
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Detail your inquiry findings, contractor response, or resolution justification..."
                  className="w-full rounded-lg border border-slate-700 bg-[#121c2a] p-3 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-[11px] text-emerald-300">
                🔒 Every inquiry action creates an immutable, SHA-256 stamped entry in the National MPLADS Audit Trail.
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setActionModalCase(null)}
                  className="px-3.5 py-2 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingAction}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold disabled:opacity-50 transition"
                >
                  {submittingAction ? "Recording Action..." : "Commit Action to Audit Trail"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}