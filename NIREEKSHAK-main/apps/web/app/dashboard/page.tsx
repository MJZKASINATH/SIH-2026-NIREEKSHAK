"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Sidebar from "../../components/Sidebar";
import RoleSwitcher from "../../components/RoleSwitcher";
import GeostatMap from "../../components/map/GeostatMap";
import ProposeProjectModal from "../../components/projects/ProposeProjectModal";
import { getStoredUser, canProposeProject } from "../../lib/auth";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<any[]>([]);
  const [contractors, setContractors] = useState<any[]>([]);
  const [showProposeModal, setShowProposeModal] = useState(false);
  const [currentUser, setCurrentUser] = useState(getStoredUser());

  const [stats, setStats] = useState({
    totalProjects: 0,
    activeProjects: 0,
    totalAllocation: 0,
    totalExpenditure: 0,
    projectsAtRisk: 0,
    redFlags: 0,
    ongoingInvestigations: 0,
    riskDistribution: {
      RED_FLAG: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0
    }
  });

  useEffect(() => {
    const handleAuth = () => setCurrentUser(getStoredUser());
    window.addEventListener("nireekshak_auth_changed", handleAuth);
    return () => window.removeEventListener("nireekshak_auth_changed", handleAuth);
  }, []);

  const loadDashboardData = () => {
    setLoading(true);
    Promise.all([
      fetch("/api/projects?page_size=50").then((r) => (r.ok ? r.json() : { items: [] })),
      fetch("/api/analytics/overview").then((r) => (r.ok ? r.json() : null)),
      fetch("/api/contractors").then((r) => (r.ok ? r.json() : []))
    ])
      .then(([projData, analyticsData, contractorData]) => {
        if (projData.items) setProjects(projData.items);
        if (contractorData && Array.isArray(contractorData)) setContractors(contractorData);
        if (analyticsData) {
          setStats({
            totalProjects: analyticsData.total_projects ?? 0,
            activeProjects: analyticsData.active_projects ?? 0,
            totalAllocation: analyticsData.total_allocation ?? 0,
            totalExpenditure: analyticsData.total_expenditure ?? 0,
            projectsAtRisk: analyticsData.high_risk_projects ?? 0,
            redFlags: analyticsData.red_flagged_projects ?? 0,
            ongoingInvestigations: analyticsData.ongoing_investigations ?? 0,
            riskDistribution: analyticsData.risk_distribution || {
              RED_FLAG: 0,
              HIGH: 0,
              MEDIUM: 0,
              LOW: 0
            }
          });
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Dashboard data load error:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const redFlagProjects = projects.filter((p) => p.risk >= 80 || p.status === "RED_FLAGGED");
  const highRiskProjects = projects.filter((p) => p.risk >= 60 && p.risk < 80);

  // Dynamic alerts derived strictly from live database records
  const dynamicAlerts = [
    ...redFlagProjects.slice(0, 2).map((p) => ({
      type: "RED_FLAG",
      badge: "🔴 Red Flag Alert",
      badgeColor: "text-rose-400 border-rose-500/30 bg-rose-950/20",
      title: p.title || p.description,
      desc: `Multi-signal risk score reached ${p.risk}/100. Auto-investigation case opened.`,
      linkText: "Review Digital File →",
      href: `/projects/${p.id}`
    })),
    ...highRiskProjects.slice(0, 1).map((p) => ({
      type: "HIGH_RISK",
      badge: "⚠️ Cost Anomaly",
      badgeColor: "text-orange-400 border-orange-500/30 bg-orange-950/20",
      title: p.title || p.description,
      desc: "Awarded cost or expenditure deviates significantly from regional peer medians.",
      linkText: "Inspect Anomaly →",
      href: `/projects/${p.id}`
    })),
    ...contractors.filter((c) => c.suspicious_projects > 0).slice(0, 1).map((c) => ({
      type: "CONTRACTOR",
      badge: "🏢 Contractor Risk Profile",
      badgeColor: "text-amber-400 border-amber-500/30 bg-amber-950/20",
      title: c.contractor_name,
      desc: `Entity linked to ${c.suspicious_projects} red-flagged works across jurisdictions.`,
      linkText: "View Vendor Dossier →",
      href: `/contractors/${c.contractor_id}`
    }))
  ];

  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden">
        {/* COMMAND CENTRE HEADER */}
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-6 md:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[11px] font-bold tracking-[0.32em] text-emerald-400 uppercase">
                  Command Centre • SIH26102
                </span>
              </div>
              <h1 className="mt-1 text-3xl font-bold tracking-tight md:text-4xl text-white">
                Intelligence Dashboard
              </h1>
              <p className="mt-1 text-xs text-[#758ea8]">
                Real-time MPLADS lifecycle tracking, explainable AI fraud-risk intelligence & field verification
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <RoleSwitcher />

              {canProposeProject(currentUser.role) && (
                <button
                  onClick={() => setShowProposeModal(true)}
                  className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3.5 py-2 text-xs font-semibold text-white transition shadow-lg flex items-center gap-2"
                >
                  <span>+</span>
                  <span>Propose Project</span>
                </button>
              )}
            </div>
          </div>
        </header>

        <div className="p-6 md:p-8 space-y-6">
          {/* TOP 7 KPI CARDS - STRICTLY FROM DATABASE */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Projects</div>
              <div className="mt-1 text-2xl font-bold text-white">
                {loading ? "..." : stats.totalProjects.toLocaleString("en-IN")}
              </div>
              <div className="mt-1 text-[10px] text-slate-500">Registered in DB</div>
            </div>

            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Works</div>
              <div className="mt-1 text-2xl font-bold text-emerald-400">
                {loading ? "..." : stats.activeProjects.toLocaleString("en-IN")}
              </div>
              <div className="mt-1 text-[10px] text-slate-500">In execution</div>
            </div>

            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Allocation</div>
              <div className="mt-1 text-2xl font-bold text-sky-400">
                ₹{(stats.totalAllocation / 10000000).toFixed(2)} Cr
              </div>
              <div className="mt-1 text-[10px] text-slate-500">Sanctioned fund</div>
            </div>

            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Spent</div>
              <div className="mt-1 text-2xl font-bold text-slate-200">
                ₹{(stats.totalExpenditure / 10000000).toFixed(2)} Cr
              </div>
              <div className="mt-1 text-[10px] text-slate-500">
                {stats.totalAllocation > 0 ? `${((stats.totalExpenditure / stats.totalAllocation) * 100).toFixed(1)}% utilized` : "0% utilized"}
              </div>
            </div>

            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Projects At Risk</div>
              <div className="mt-1 text-2xl font-bold text-orange-400">
                {loading ? "..." : stats.projectsAtRisk.toLocaleString("en-IN")}
              </div>
              <div className="mt-1 text-[10px] text-slate-500">Score 60 to 79</div>
            </div>

            <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-rose-300">Red Flags</div>
              <div className="mt-1 text-2xl font-bold text-rose-400">
                {loading ? "..." : stats.redFlags.toLocaleString("en-IN")}
              </div>
              <div className="mt-1 text-[10px] text-rose-400/70">Score 80+ critical</div>
            </div>

            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-3.5">
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Investigations</div>
              <div className="mt-1 text-2xl font-bold text-purple-400">
                {loading ? "..." : stats.ongoingInvestigations.toLocaleString("en-IN")}
              </div>
              <div className="mt-1 text-[10px] text-slate-500">Open cases</div>
            </div>
          </div>

          {/* PROJECT LIFECYCLE STRIP */}
          <section className="rounded-xl border border-[#1d2a38] bg-[#0e1622] p-4">
            <div className="flex items-center justify-between border-b border-[#1d2a38] pb-2 mb-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                End-to-End MPLADS Digital Chain of Evidence
              </h3>
              <span className="text-[11px] text-emerald-400 font-mono">Full Lifecycle Managed</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4 lg:grid-cols-7">
              {[
                { step: "1. Proposal", desc: "MP submission" },
                { step: "2. Sanction", desc: "Digital ID scan" },
                { step: "3. Tendering", desc: "Entity linked" },
                { step: "4. Execution", desc: "Append ledger" },
                { step: "5. Verification", desc: "5 Geo-checkpoints" },
                { step: "6. Anomaly Engine", desc: "Explainable Risk" },
                { step: "7. Audit & Close", desc: "Case resolved" },
              ].map((s, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className="flex flex-col">
                    <span className="font-bold text-emerald-400">{s.step}</span>
                    <span className="text-[10px] text-slate-400">{s.desc}</span>
                  </div>
                  {idx < 6 && <span className="text-slate-600 font-bold hidden lg:inline">→</span>}
                </div>
              ))}
            </div>
          </section>

          {/* MAIN SURVEILLANCE GRID: RISK DISTRIBUTION + LEAFLET MAP + ALERTS */}
          <div className="grid gap-6 xl:grid-cols-[280px_1fr_300px]">
            {/* LEFT: RISK DISTRIBUTION (STRICT DB SUM) */}
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-5 space-y-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Database Risk Distribution
              </h3>

              <div className="space-y-3 text-xs">
                <div className="rounded-lg bg-rose-950/30 border border-rose-800/40 p-3">
                  <div className="flex justify-between font-bold text-rose-400">
                    <span>Red Flag (80-100)</span>
                    <span>{stats.riskDistribution.RED_FLAG}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Automatic investigation trigger</p>
                </div>

                <div className="rounded-lg bg-orange-950/20 border border-orange-800/30 p-3">
                  <div className="flex justify-between font-bold text-orange-400">
                    <span>High Risk (60-79)</span>
                    <span>{stats.riskDistribution.HIGH}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Vigilance audit review required</p>
                </div>

                <div className="rounded-lg bg-amber-950/20 border border-amber-800/30 p-3">
                  <div className="flex justify-between font-bold text-amber-400">
                    <span>Medium Risk (30-59)</span>
                    <span>{stats.riskDistribution.MEDIUM}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Milestone monitoring flag</p>
                </div>

                <div className="rounded-lg bg-emerald-950/20 border border-emerald-800/30 p-3">
                  <div className="flex justify-between font-bold text-emerald-400">
                    <span>Low Risk (0-29)</span>
                    <span>{stats.riskDistribution.LOW}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Within standard benchmarks</p>
                </div>
              </div>

              <div className="pt-2 border-t border-[#1d2a38]">
                <Link
                  href="/projects"
                  className="text-xs font-semibold text-emerald-400 hover:underline flex items-center justify-between"
                >
                  <span>Explore Project Registry</span>
                  <span>→</span>
                </Link>
              </div>
            </div>

            {/* CENTER: REAL LEAFLET GEO-STATISTICAL MAP */}
            <div className="min-w-0">
              <GeostatMap height="520px" showFilters={true} />
            </div>

            {/* RIGHT: REAL-TIME RECENT ALERTS FEED */}
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1d2a38] pb-2">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Live Alert Signals
                </h3>
                <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping" />
              </div>

              <div className="space-y-3 text-xs">
                {dynamicAlerts.length === 0 ? (
                  <p className="text-xs text-slate-500 text-center py-4">No critical alerts detected in registered works.</p>
                ) : (
                  dynamicAlerts.map((alert, idx) => (
                    <div key={idx} className={`rounded-lg border p-3 space-y-1 ${alert.badgeColor}`}>
                      <span className="text-[10px] font-bold uppercase tracking-wider">{alert.badge}</span>
                      <p className="font-semibold text-white truncate">{alert.title}</p>
                      <p className="text-[11px] text-slate-300">{alert.desc}</p>
                      <Link href={alert.href} className="text-[10px] font-bold text-emerald-400 hover:underline block pt-1">
                        {alert.linkText}
                      </Link>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* LOWER TWO-COLUMN GRID: TOP RED-FLAGGED PROJECTS & CONTRACTOR RISK */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* TOP RED-FLAGGED PROJECTS */}
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1d2a38] pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Top Priority Red-Flagged Projects
                  </h3>
                  <p className="text-xs text-slate-400">Surfaced by multi-signal anomaly fusion for auditor review</p>
                </div>
                <Link href="/investigation" className="text-xs font-semibold text-emerald-400 hover:underline">
                  Investigation Queue →
                </Link>
              </div>

              <div className="space-y-3">
                {redFlagProjects.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3">No red-flagged projects currently in the database.</p>
                ) : (
                  redFlagProjects.slice(0, 4).map((p) => (
                    <div
                      key={p.id}
                      className="rounded-lg border border-rose-500/30 bg-[#0c141d] p-3.5 flex items-center justify-between gap-3 text-xs"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-emerald-400 font-bold">{p.id}</span>
                          <span className="text-slate-500">•</span>
                          <span className="text-slate-400">{p.constituency}, {p.state}</span>
                        </div>
                        <h4 className="font-semibold text-white mt-1 truncate">{p.title || p.description}</h4>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Sanction: ₹{p.amount?.toLocaleString("en-IN")} • Vendor: <strong className="text-slate-300">{p.contractor_name || "Assigned"}</strong>
                        </p>
                      </div>

                      <div className="flex flex-col items-end gap-1.5 shrink-0">
                        <span className="rounded bg-rose-600 px-2 py-0.5 text-xs font-black text-white">
                          {p.risk}/100
                        </span>
                        <Link
                          href={`/projects/${p.id}`}
                          className="rounded border border-[#233549] bg-[#111c28] px-2.5 py-1 text-[11px] text-slate-300 hover:text-white"
                        >
                          Digital File →
                        </Link>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* CONTRACTOR RISK TABLE */}
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#1d2a38] pb-3">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    Contractor Entity Risk Profiles
                  </h3>
                  <p className="text-xs text-slate-400">Entities with flagged works or abnormal delivery patterns</p>
                </div>
                <Link href="/contractors" className="text-xs font-semibold text-emerald-400 hover:underline">
                  Full Vendor DB →
                </Link>
              </div>

              <div className="overflow-x-auto text-xs">
                {contractors.length === 0 ? (
                  <p className="text-xs text-slate-500 py-3">No contractor profiles registered yet.</p>
                ) : (
                  <table className="w-full text-left">
                    <thead className="text-[10px] uppercase text-slate-400 border-b border-[#1d2a38]">
                      <tr>
                        <th className="py-2">Vendor Name</th>
                        <th className="py-2 text-center">Works</th>
                        <th className="py-2 text-center">Suspicious</th>
                        <th className="py-2 text-right">Risk Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#172230]">
                      {contractors.slice(0, 4).map((c) => (
                        <tr key={c.contractor_id} className="hover:bg-[#121c27]">
                          <td className="py-2.5">
                            <Link href={`/contractors/${c.contractor_id}`} className="font-semibold text-white hover:text-emerald-400">
                              {c.contractor_name}
                            </Link>
                            <div className="text-[9px] font-mono text-slate-500">{c.registration_number}</div>
                          </td>
                          <td className="py-2.5 text-center font-bold">{c.total_projects}</td>
                          <td className="py-2.5 text-center">
                            {c.suspicious_projects > 0 ? (
                              <span className="rounded bg-rose-500/20 px-2 py-0.5 font-bold text-rose-300">
                                {c.suspicious_projects}
                              </span>
                            ) : (
                              <span className="text-slate-500">0</span>
                            )}
                          </td>
                          <td className="py-2.5 text-right">
                            <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                              c.risk_score >= 80 ? 'bg-rose-600 text-white' : c.risk_score >= 60 ? 'bg-orange-600 text-white' : 'bg-emerald-600 text-white'
                            }`}>
                              {c.risk_score}/100
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* PROPOSE PROJECT MODAL */}
      <ProposeProjectModal
        isOpen={showProposeModal}
        onClose={() => setShowProposeModal(false)}
        onSuccess={(newP) => {
          loadDashboardData();
          alert(`Project ${newP.id} registered successfully in the database with 5 predefined geo checkpoints!`);
        }}
      />
    </div>
  );
}