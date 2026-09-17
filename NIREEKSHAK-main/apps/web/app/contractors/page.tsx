"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Sidebar from "../../components/Sidebar";
import RoleSwitcher from "../../components/RoleSwitcher";

export default function ContractorsPage() {
  const [contractors, setContractors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterRisk, setFilterRisk] = useState("ALL");

  useEffect(() => {
    fetch("/api/contractors")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setContractors(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const filtered = contractors.filter((c) => {
    const matchesSearch =
      !search ||
      c.contractor_name.toLowerCase().includes(search.toLowerCase()) ||
      c.registration_number.toLowerCase().includes(search.toLowerCase());
    const matchesRisk = filterRisk === "ALL" || c.risk_status === filterRisk;
    return matchesSearch && matchesRisk;
  });

  const totalValue = contractors.reduce((acc, c) => acc + (c.total_project_value || 0), 0);
  const suspiciousCount = contractors.reduce((acc, c) => acc + (c.suspicious_projects || 0), 0);
  const highRiskVendors = contractors.filter((c) => c.risk_score >= 60).length;

  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden">
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-6 md:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-[11px] font-medium tracking-[0.32em] text-emerald-400 uppercase">
                Networked Entity Intelligence
              </div>
              <h1 className="mt-1 text-3xl font-bold tracking-tight text-white md:text-4xl">
                Contractor & Vendor Risk Database
              </h1>
              <p className="mt-1 text-xs text-slate-400">
                Cross-project fraud history, entity normalization, and suspicious project involvement
              </p>
            </div>
            <RoleSwitcher />
          </div>

          {/* STATS STRIP */}
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Total Vendors</span>
              <p className="text-xl font-bold text-white mt-0.5">{contractors.length}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Suspicious Works</span>
              <p className="text-xl font-bold text-rose-400 mt-0.5">{suspiciousCount}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">High Risk Vendors</span>
              <p className="text-xl font-bold text-orange-400 mt-0.5">{highRiskVendors}</p>
            </div>
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <span className="text-[10px] uppercase text-slate-500 font-medium">Total Works Value</span>
              <p className="text-xl font-bold text-sky-400 mt-0.5">₹{(totalValue / 10000000).toFixed(1)} Cr</p>
            </div>
          </div>
        </header>

        {/* SEARCH & FILTERS */}
        <div className="p-6 md:p-8 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <input
                type="text"
                placeholder="Search vendor name or registration number..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-72 rounded-lg border border-[#233549] bg-[#0c141d] px-3.5 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
              />

              <select
                value={filterRisk}
                onChange={(e) => setFilterRisk(e.target.value)}
                className="rounded-lg border border-[#233549] bg-[#0c141d] px-3.5 py-2 text-slate-300 focus:border-emerald-500 focus:outline-none"
              >
                <option value="ALL">All Risk Ratings</option>
                <option value="HIGH">High Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="LOW">Low Risk</option>
              </select>
            </div>

            <span className="text-xs text-slate-400">
              Showing <strong className="text-emerald-400">{filtered.length}</strong> contractor records
            </span>
          </div>

          {/* CONTRACTORS TABLE */}
          <div className="overflow-hidden rounded-xl border border-[#1d2a38] bg-[#101924]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#1d2a38] bg-[#0c131c] text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">Vendor Entity</th>
                    <th className="px-5 py-3.5 font-semibold">Registration No.</th>
                    <th className="px-5 py-3.5 font-semibold text-center">Total Works</th>
                    <th className="px-5 py-3.5 font-semibold text-center">Suspicious Works</th>
                    <th className="px-5 py-3.5 font-semibold text-center">Delayed</th>
                    <th className="px-5 py-3.5 font-semibold">Total Portfolio</th>
                    <th className="px-5 py-3.5 font-semibold">Entity Risk</th>
                    <th className="px-5 py-3.5 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#172230]">
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-400 font-mono">
                        Loading contractor database...
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-400">
                        No contractors found matching criteria.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((c) => (
                      <tr key={c.contractor_id} className="hover:bg-[#121c27] transition">
                        <td className="px-5 py-3.5">
                          <Link
                            href={`/contractors/${c.contractor_id}`}
                            className="font-semibold text-white hover:text-emerald-400 transition"
                          >
                            {c.contractor_name}
                          </Link>
                          <div className="text-[10px] text-slate-500">ID: {c.contractor_id}</div>
                        </td>
                        <td className="px-5 py-3.5 font-mono text-emerald-400">{c.registration_number}</td>
                        <td className="px-5 py-3.5 text-center font-bold text-slate-200">{c.total_projects}</td>
                        <td className="px-5 py-3.5 text-center">
                          {c.suspicious_projects > 0 ? (
                            <span className="rounded-full bg-rose-500/20 px-2.5 py-0.5 font-bold text-rose-300 border border-rose-500/40">
                              {c.suspicious_projects} Flagged
                            </span>
                          ) : (
                            <span className="text-slate-500">0</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-center text-slate-400">{c.delayed_projects}</td>
                        <td className="px-5 py-3.5 font-semibold text-sky-400">
                          ₹{(c.total_project_value / 100000).toFixed(1)}L
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-2">
                            <span
                              className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                                c.risk_score >= 80
                                  ? "bg-rose-600 text-white"
                                  : c.risk_score >= 60
                                  ? "bg-orange-600 text-white"
                                  : c.risk_score >= 30
                                  ? "bg-amber-600 text-white"
                                  : "bg-emerald-600 text-white"
                              }`}
                            >
                              {c.risk_score}/100
                            </span>
                            <span className="text-[10px] text-slate-400">{c.risk_status}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <Link
                            href={`/contractors/${c.contractor_id}`}
                            className="rounded-lg border border-[#263c54] bg-[#111d2b] px-3 py-1.5 text-xs text-slate-200 hover:border-emerald-500 hover:text-emerald-400 transition"
                          >
                            Profile →
                          </Link>
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
