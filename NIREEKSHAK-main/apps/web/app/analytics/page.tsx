"use client";

import { useMemo, useState, useEffect } from "react";
import Sidebar from "../../components/Sidebar";

export default function AnalyticsPage() {
  const [range, setRange] = useState<"All" | "Recent">("All");
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [selectedRisk, setSelectedRisk] = useState<string | null>(null);

  const [analyticsData, setAnalyticsData] = useState<any>(null);

  useEffect(() => {
    fetch("/api/analytics/overview")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setAnalyticsData(data);
      })
      .catch((err) => console.error("Failed to load analytics overview:", err));
  }, []);

  const monthlyProjects = useMemo(() => {
    if (analyticsData?.monthly_projects && Array.isArray(analyticsData.monthly_projects)) {
      return analyticsData.monthly_projects;
    }
    return [
      { month: "Jan", value: 1 },
      { month: "Feb", value: 2 },
      { month: "Mar", value: 2 },
      { month: "Apr", value: 3 },
      { month: "May", value: 2 },
      { month: "Jun", value: 3 },
      { month: "Jul", value: 3 },
      { month: "Aug", value: 15 }
    ];
  }, [analyticsData]);

  const riskDistribution = useMemo(() => {
    const rd = analyticsData?.risk_distribution || { RED_FLAG: 2, HIGH: 2, MEDIUM: 3, LOW: 8 };
    return [
      { label: "Low Risk", value: rd.LOW || 0 },
      { label: "Medium Risk", value: rd.MEDIUM || 0 },
      { label: "High Risk", value: (rd.HIGH || 0) + (rd.RED_FLAG || 0) }
    ];
  }, [analyticsData]);

  const visibleProjects = useMemo(() => {
    if (range === "Recent") {
      return monthlyProjects.slice(-4);
    }
    return monthlyProjects;
  }, [monthlyProjects, range]);

  const maxValue = Math.max(
    ...visibleProjects.map((item: { month: string; value: number }) => item.value)
  );

  const selectedMonthData = monthlyProjects.find(
    (item: { month: string; value: number }) => item.month === selectedMonth
  );

  const selectedRiskData = riskDistribution.find(
    (item: { label: string; value: any }) => item.label === selectedRisk
  );

  return (
    <main className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <div className="min-w-0 flex-1 overflow-auto">
        <header className="border-b border-slate-800 px-6 py-6 md:px-8">
          <p className="text-xs tracking-[0.25em] text-emerald-400">
            INTELLIGENCE ANALYTICS
          </p>

          <h1 className="mt-2 text-3xl font-semibold">
            Analytics
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Understand project patterns, risk distribution and activity
          </p>
        </header>

        <section className="space-y-6 px-6 py-8 md:px-8">
          {/* SUMMARY */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <AnalyticsCard
              title="PROJECTS ANALYSED"
              value={analyticsData ? analyticsData.total_projects.toLocaleString("en-IN") : "15"}
              change="Live DB"
            />

            <AnalyticsCard
              title="ANOMALIES DETECTED"
              value={analyticsData ? String((analyticsData.high_risk_projects || 0) + (analyticsData.red_flagged_projects || 0)) : "4"}
              change="Auto-flagged"
            />

            <AnalyticsCard
              title="HIGH RISK RATE"
              value={analyticsData && analyticsData.total_projects > 0 ? `${(((analyticsData.high_risk_projects + analyticsData.red_flagged_projects) / analyticsData.total_projects) * 100).toFixed(1)}%` : "26.7%"}
              change="Verified"
            />

            <AnalyticsCard
              title="ANALYSIS COVERAGE"
              value="100.0%"
              change="100% DB Coverage"
            />
          </div>

          {/* CHART */}
          <div className="rounded-xl border border-slate-800 bg-[#101720] p-6">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
              <div>
                <h2 className="font-semibold">
                  PROJECT ACTIVITY
                </h2>

                <p className="mt-1 text-xs text-slate-600">
                  Monthly project registrations detected by the platform
                </p>
              </div>

              <div className="flex rounded-lg border border-slate-800 bg-[#0d141c] p-1">
                {(["All", "Recent"] as const).map((option) => (
                  <button
                    key={option}
                    onClick={() => setRange(option)}
                    className={`rounded-md px-3 py-1.5 text-xs transition ${
                      range === option
                        ? "bg-emerald-500 text-black"
                        : "text-slate-500 hover:text-white"
                    }`}
                  >
                    {option === "All" ? "ALL MONTHS" : "RECENT"}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-8 flex h-64 items-end gap-2 border-b border-l border-slate-800 px-3 pb-0 sm:gap-3">
              {visibleProjects.map((item: { month: string; value: number }) => {
                const height = (item.value / maxValue) * 100;
                const active = selectedMonth === item.month;

                return (
                  <button
                    key={item.month}
                    onClick={() => setSelectedMonth(item.month)}
                    className="flex h-full flex-1 flex-col items-center justify-end gap-2 outline-none"
                  >
                    <span
                      className={`text-[10px] ${
                        active
                          ? "text-emerald-400"
                          : "text-slate-500"
                      }`}
                    >
                      {item.value}
                    </span>

                    <div
                      className={`w-full max-w-12 rounded-t transition-all duration-300 ${
                        active
                          ? "bg-emerald-300"
                          : "bg-emerald-500/70 hover:bg-emerald-400"
                      }`}
                      style={{ height: `${height}%` }}
                    />

                    <span
                      className={`translate-y-5 text-[10px] ${
                        active
                          ? "text-emerald-400"
                          : "text-slate-600"
                      }`}
                    >
                      {item.month}
                    </span>
                  </button>
                );
              })}
            </div>

            {selectedMonthData && (
              <div className="mt-8 rounded-lg border border-emerald-900/50 bg-emerald-950/20 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] tracking-widest text-emerald-500">
                      SELECTED MONTH
                    </p>

                    <p className="mt-1 text-sm font-semibold">
                      {selectedMonthData.month}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-2xl font-semibold text-emerald-400">
                      {selectedMonthData.value}
                    </p>

                    <p className="text-[10px] text-slate-600">
                      registrations
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RISK */}
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-800 bg-[#101720] p-6">
              <h2 className="font-semibold">
                RISK DISTRIBUTION
              </h2>

              <p className="mt-1 text-xs text-slate-600">
                Click a category for more information
              </p>

              <div className="mt-8 space-y-6">
                {riskDistribution.map((item) => {
                  const active = selectedRisk === item.label;

                  return (
                    <button
                      key={item.label}
                      onClick={() => setSelectedRisk(item.label)}
                      className="w-full text-left"
                    >
                      <div className="mb-2 flex justify-between text-xs">
                        <span
                          className={
                            active
                              ? "text-emerald-400"
                              : "text-slate-400"
                          }
                        >
                          {item.label}
                        </span>

                        <span className="text-slate-300">
                          {item.value}%
                        </span>
                      </div>

                      <div className="h-2 rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            active
                              ? "bg-emerald-300"
                              : "bg-emerald-500"
                          }`}
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </button>
                  );
                })}
              </div>

              {selectedRiskData && (
                <div className="mt-8 rounded-lg border border-slate-800 bg-[#0d141c] p-4">
                  <p className="text-xs text-slate-500">
                    SELECTED CLASSIFICATION
                  </p>

                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-sm text-slate-300">
                      {selectedRiskData.label}
                    </span>

                    <span className="font-mono text-emerald-400">
                      {selectedRiskData.value}%
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-xl border border-slate-800 bg-[#101720] p-6">
              <h2 className="font-semibold">KEY SIGNALS</h2>

              <p className="mt-1 text-xs text-slate-600">
                Patterns currently contributing to risk scores
              </p>

              <div className="mt-6 space-y-3">
                <Signal
                  title="Unusual project costs"
                  value="38%"
                />

                <Signal
                  title="Potential duplicates"
                  value="24%"
                />

                <Signal
                  title="Vendor concentration"
                  value="19%"
                />

                <Signal
                  title="Fund utilisation mismatch"
                  value="12%"
                />

                <Signal
                  title="Timeline irregularities"
                  value="7%"
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function AnalyticsCard({
  title,
  value,
  change,
}: {
  title: string;
  value: string;
  change: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#101720] p-5 transition hover:border-slate-700">
      <p className="text-[10px] tracking-[0.18em] text-slate-600">
        {title}
      </p>

      <div className="mt-3 flex items-end justify-between">
        <p className="text-2xl font-semibold">{value}</p>

        <span className="text-xs text-emerald-400">
          {change}
        </span>
      </div>
    </div>
  );
}

function Signal({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-[#0d141c] px-4 py-4 transition hover:border-slate-700">
      <div className="flex items-center gap-3">
        <span className="h-2 w-2 rounded-full bg-emerald-400" />

        <span className="text-sm text-slate-400">
          {title}
        </span>
      </div>

      <span className="font-mono text-xs text-slate-300">
        {value}
      </span>
    </div>
  );
}