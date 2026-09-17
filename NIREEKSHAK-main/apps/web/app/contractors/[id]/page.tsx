"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import Sidebar from "../../../components/Sidebar";
import RoleSwitcher from "../../../components/RoleSwitcher";

interface ContractorDetailProps {
  params: Promise<{ id: string }>;
}

export default function ContractorDetailPage({ params }: ContractorDetailProps) {
  const resolvedParams = use(params);
  const contractorId = resolvedParams.id;

  const [contractor, setContractor] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/contractors/${contractorId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Contractor not found");
        return res.json();
      })
      .then((data) => {
        setContractor(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [contractorId]);

  if (loading || !contractor) {
    return (
      <div className="flex min-h-screen bg-[#0b1016] text-white">
        <Sidebar />
        <div className="flex-1 p-8 flex items-center justify-center">
          <span className="h-8 w-8 inline-block animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />
        </div>
      </div>
    );
  }

  const isHighRisk = contractor.risk_score >= 60;

  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden">
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-6 md:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Link
                  href="/contractors"
                  className="rounded-lg border border-[#233549] bg-[#111c28] px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                >
                  ← All Contractors
                </Link>
                <span className="font-mono text-xs text-emerald-400">{contractor.registration_number}</span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                    isHighRisk
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  }`}
                >
                  {contractor.risk_status} Risk Entity
                </span>
              </div>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-white md:text-3xl">
                {contractor.contractor_name}
              </h1>
              <p className="mt-1 text-xs text-slate-400">
                Entity ID: <strong className="text-slate-300">{contractor.contractor_id}</strong> • Last Updated: {contractor.last_updated || "Live"}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <RoleSwitcher />

              {/* RISK BADGE */}
              <div className={`rounded-xl border p-4 text-center ${isHighRisk ? 'border-rose-500/50 bg-rose-950/30' : 'border-emerald-500/50 bg-emerald-950/20'}`}>
                <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Entity Risk Score</span>
                <p className={`text-2xl font-black ${isHighRisk ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {contractor.risk_score}/100
                </p>
              </div>
            </div>
          </div>

          {/* METRIC STRIP */}
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Total Works</span>
              <p className="text-xl font-bold text-white mt-0.5">{contractor.total_projects}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Completed</span>
              <p className="text-xl font-bold text-emerald-400 mt-0.5">{contractor.completed_projects}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Delayed</span>
              <p className="text-xl font-bold text-orange-400 mt-0.5">{contractor.delayed_projects}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Suspicious Works</span>
              <p className="text-xl font-bold text-rose-400 mt-0.5">{contractor.suspicious_projects}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Total Sanction Value</span>
              <p className="text-xl font-bold text-sky-400 mt-0.5">₹{(contractor.total_project_value / 100000).toFixed(1)}L</p>
            </div>
          </div>
        </header>

        {/* ASSOCIATED PROJECTS */}
        <div className="p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white uppercase tracking-wider">
              Associated MPLADS Works ({contractor.associated_projects?.length || 0})
            </h3>
            <span className="text-xs text-slate-400">
              Cross-constituency project registry
            </span>
          </div>

          <div className="overflow-hidden rounded-xl border border-[#1d2a38] bg-[#101924]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#1d2a38] bg-[#0c131c] text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="px-5 py-3.5">Project ID</th>
                    <th className="px-5 py-3.5">Work Title</th>
                    <th className="px-5 py-3.5">Constituency / State</th>
                    <th className="px-5 py-3.5">Sanction Amount</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5">Risk Score</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172230]">
                  {contractor.associated_projects && contractor.associated_projects.length > 0 ? (
                    contractor.associated_projects.map((p: any) => (
                      <tr key={p.id} className="hover:bg-[#121c27] transition">
                        <td className="px-5 py-3.5 font-mono text-emerald-400 font-bold">{p.id}</td>
                        <td className="px-5 py-3.5 font-medium text-white max-w-xs truncate">{p.title || p.description}</td>
                        <td className="px-5 py-3.5 text-slate-300">{p.constituency}, {p.state}</td>
                        <td className="px-5 py-3.5 font-semibold text-white">₹{p.amount?.toLocaleString("en-IN")}</td>
                        <td className="px-5 py-3.5">
                          <span className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                            p.status === 'RED_FLAGGED' ? 'bg-rose-500/20 text-rose-300' : 'bg-blue-500/20 text-blue-300'
                          }`}>
                            {p.status}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                            p.risk >= 80 ? 'bg-rose-600 text-white' : p.risk >= 60 ? 'bg-orange-600 text-white' : 'bg-emerald-600 text-white'
                          }`}>
                            {p.risk}/100
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right space-x-2">
                          <Link
                            href={`/projects/${p.id}`}
                            className="rounded border border-[#263c54] bg-[#111d2b] px-2.5 py-1 text-[11px] text-slate-200 hover:border-emerald-500 hover:text-emerald-400"
                          >
                            Digital File →
                          </Link>
                          {p.risk >= 80 && (
                            <Link
                              href={`/investigation?project=${p.id}`}
                              className="rounded bg-rose-600 hover:bg-rose-500 px-2 py-1 text-[11px] font-bold text-white"
                            >
                              Investigate
                            </Link>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-slate-400">
                        No projects mapped directly to this vendor profile.
                      </td>
                    </tr>
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
