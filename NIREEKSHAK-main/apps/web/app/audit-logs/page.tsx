"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Sidebar from "../../components/Sidebar";
import RoleSwitcher from "../../components/RoleSwitcher";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState("ALL");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/audit-logs?limit=100")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setLogs(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filtered = logs.filter((log) => {
    const matchesSearch =
      !search ||
      log.user_name.toLowerCase().includes(search.toLowerCase()) ||
      (log.project_id && log.project_id.toLowerCase().includes(search.toLowerCase())) ||
      log.action.toLowerCase().includes(search.toLowerCase());
    const matchesAction = filterAction === "ALL" || log.action.includes(filterAction);
    return matchesSearch && matchesAction;
  });

  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden">
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-6 md:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-[11px] font-medium tracking-[0.32em] text-emerald-400 uppercase">
                Regulatory Compliance & Chain of Custody
              </div>
              <h1 className="mt-1 text-3xl font-bold tracking-tight text-white md:text-4xl">
                National Digital Audit Trail
              </h1>
              <p className="mt-1 text-xs text-slate-400">
                Tamper-evident, immutable system ledger recording every statutory lifecycle mutation with cryptographic event hashes
              </p>
            </div>
            <RoleSwitcher />
          </div>
        </header>

        <div className="p-6 md:p-8 space-y-6">
          {/* SEARCH & FILTER CONTROLS */}
          <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex flex-wrap items-center gap-3">
              <input
                type="text"
                placeholder="Search user, action, project ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-72 rounded-lg border border-[#233549] bg-[#0c141d] px-3.5 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
              />

              <select
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="rounded-lg border border-[#233549] bg-[#0c141d] px-3.5 py-2 text-slate-300 focus:border-emerald-500 focus:outline-none"
              >
                <option value="ALL">All Actions</option>
                <option value="PROPOSAL">Proposals</option>
                <option value="APPROVED">Approvals</option>
                <option value="TENDER">Tender Awards</option>
                <option value="EXPENDITURE">Expenditures</option>
                <option value="PROGRESS">Progress Milestones</option>
                <option value="CHECKPOINT">Checkpoints Verification</option>
                <option value="INVESTIGATION">Investigations</option>
              </select>
            </div>

            <span className="text-slate-400">
              Showing <strong className="text-emerald-400">{filtered.length}</strong> immutable events
            </span>
          </div>

          {/* AUDIT LOG TABLE */}
          <div className="overflow-hidden rounded-xl border border-[#1d2a38] bg-[#101924]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#1d2a38] bg-[#0c131c] text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="px-5 py-3.5">Event ID & Time</th>
                    <th className="px-5 py-3.5">User & Role</th>
                    <th className="px-5 py-3.5">Statutory Action</th>
                    <th className="px-5 py-3.5">Project ID</th>
                    <th className="px-5 py-3.5">Mutation Details</th>
                    <th className="px-5 py-3.5">Cryptographic SHA-256 Event Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172230]">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400 font-mono">
                        Retrieving cryptographic audit trail...
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        No audit events match criteria.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((item) => (
                      <tr key={item.event_id} className="hover:bg-[#121c27] transition">
                        <td className="px-5 py-3.5">
                          <div className="font-mono text-emerald-400 font-bold">{item.event_id}</div>
                          <div className="text-[10px] text-slate-500">{item.timestamp}</div>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-semibold text-white">{item.user_name}</div>
                          <span className="inline-block rounded bg-slate-800 px-1.5 py-0.5 text-[9px] font-mono text-slate-400">
                            {item.role}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="rounded bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-300">
                            {item.action}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          {item.project_id ? (
                            <Link
                              href={`/projects/${item.project_id}`}
                              className="font-mono text-xs text-sky-400 hover:underline"
                            >
                              {item.project_id}
                            </Link>
                          ) : (
                            <span className="text-slate-600 font-mono">SYSTEM</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 max-w-sm text-slate-300 truncate">
                          {item.new_value || item.previous_value || "Audit record sealed"}
                        </td>
                        <td className="px-5 py-3.5 font-mono text-[9px] text-slate-500 max-w-xs truncate">
                          {item.event_hash}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
