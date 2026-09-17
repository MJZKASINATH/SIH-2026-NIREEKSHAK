"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import Sidebar from "../../../components/Sidebar";
import RoleSwitcher from "../../../components/RoleSwitcher";
import { getStoredUser, getAuthHeaders, canApproveProject, canAwardTender, canAddExpenditure, canSubmitProgress, canVerifyCheckpoints, canManageInvestigation } from "../../../lib/auth";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ProjectMasterFilePage({ params }: PageProps) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [activeTab, setActiveTab] = useState<
    "overview" | "proposal" | "approval" | "tender" | "financial" | "progress" | "checkpoints" | "risk" | "investigation" | "audit"
  >("overview");

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  // Modals state
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showTenderModal, setShowTenderModal] = useState(false);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [showNoteModal, setShowNoteModal] = useState(false);

  // Verification checkpoint selected
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<string | null>(null);

  // Forms state
  const [approvalForm, setApprovalForm] = useState({
    approved_by: "Dr. Rajesh Sharma, IAS",
    designation: "District Magistrate & Collector",
    official_id: "IAS-KL-2015-4091",
    digital_signature: "DIGITAL_SIG_CERT_VERIFIED_SHA256",
    remarks: "Administrative and technical sanctions verified. Approved for execution."
  });

  const [tenderForm, setTenderForm] = useState({
    contractor_name: "Apex Infrastructure Projects Ltd",
    registration_number: "REG-KL-2018-9941",
    tender_amount: 3500000,
    awarded_amount: 3420000,
    work_order_number: "WO-2026-MPLADS-091"
  });

  const [expenseForm, setExpenseForm] = useState({
    expense_category: "Civil Materials",
    description: "Supply of high-grade structural reinforcement steel & cement",
    amount: 850000,
    invoice_number: "INV-MAT-2026-88"
  });

  const [progressForm, setProgressForm] = useState({
    physical_progress_percent: 50,
    work_description: "Sub-structure casting complete; masonry work underway.",
    remarks: "Field quality inspection passed."
  });

  const [noteForm, setNoteForm] = useState({
    note_text: "",
    action_type: "NOTE"
  });

  // Listen for role switch events
  useEffect(() => {
    const handleAuth = () => setCurrentUser(getStoredUser());
    window.addEventListener("nireekshak_auth_changed", handleAuth);
    return () => window.removeEventListener("nireekshak_auth_changed", handleAuth);
  }, []);

  // Fetch complete 10-tab project file from FastAPI
  useEffect(() => {
    setLoading(true);
    fetch(`/api/projects/${projectId}/master-file`)
      .then((res) => {
        if (!res.ok) throw new Error("Could not load project master file");
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [projectId, refreshKey]);

  if (loading || !data) {
    return (
      <div className="flex min-h-screen bg-[#0b1016] text-white">
        <Sidebar />
        <div className="flex-1 p-8 flex items-center justify-center">
          <div className="text-center">
            <span className="h-8 w-8 inline-block animate-spin rounded-full border-2 border-emerald-400 border-t-transparent mb-3" />
            <p className="text-sm text-slate-400 font-mono">Accessing Project Digital Master File...</p>
          </div>
        </div>
      </div>
    );
  }

  const { header, proposal, approval, tender, expenditures, progressUpdates, checkpoints, evidence, riskAnalysis, investigation, auditTrail } = data;

  const isRedFlag = header.riskScore >= 80;

  // Handlers
  const handleApprove = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/projects/${projectId}/approve`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(approvalForm)
      });
      if (!res.ok) throw new Error("Approval failed");
      setShowApprovalModal(false);
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleTender = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/projects/${projectId}/tender`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          ...tenderForm,
          tender_amount: Number(tenderForm.tender_amount),
          awarded_amount: Number(tenderForm.awarded_amount)
        })
      });
      if (!res.ok) throw new Error("Tender assignment failed");
      setShowTenderModal(false);
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/projects/${projectId}/expenditure`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          ...expenseForm,
          amount: Number(expenseForm.amount),
          entered_by: currentUser.full_name
        })
      });
      if (!res.ok) throw new Error("Adding expenditure failed");
      setShowExpenseModal(false);
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleProgress = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`/api/projects/${projectId}/progress`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          ...progressForm,
          physical_progress_percent: Number(progressForm.physical_progress_percent),
          field_officer: currentUser.full_name
        })
      });
      if (!res.ok) throw new Error("Progress update failed");
      setShowProgressModal(false);
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleVerifyCheckpoint = async (code: string, isMismatch: boolean = false) => {
    try {
      const cp = checkpoints.find((c: any) => c.code === code);
      const lat = isMismatch ? (cp.expectedLat + 0.15) : cp.expectedLat;
      const lng = isMismatch ? (cp.expectedLng + 0.15) : cp.expectedLng;

      const res = await fetch(`/api/projects/${projectId}/checkpoints/${code}/verify`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          checkpoint_code: code,
          submitted_latitude: lat,
          submitted_longitude: lng,
          photo_url: "https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?w=400",
          uploader: currentUser.full_name
        })
      });
      if (!res.ok) throw new Error("Verification failed");
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteForm.note_text) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/investigation/notes`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          author_name: currentUser.full_name,
          role: currentUser.role,
          note_text: noteForm.note_text,
          action_type: noteForm.action_type
        })
      });
      if (!res.ok) throw new Error("Failed to add note");
      setShowNoteModal(false);
      setNoteForm({ note_text: "", action_type: "NOTE" });
      setRefreshKey((k) => k + 1);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const tabs = [
    { id: "overview", label: "1. Overview" },
    { id: "proposal", label: "2. Proposal" },
    { id: "approval", label: "3. Approval" },
    { id: "tender", label: "4. Tender" },
    { id: "financial", label: "5. Financial Ledger" },
    { id: "progress", label: "6. Progress Timeline" },
    { id: "checkpoints", label: `7. 5-Geo Checkpoints (${header.verifiedCheckpointsCount}/5)` },
    { id: "risk", label: `8. AI Risk (${header.riskScore})` },
    { id: "investigation", label: "9. Investigation Case" },
    { id: "audit", label: "10. Audit Trail" }
  ];

  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 overflow-x-hidden">
        {/* HEADER BAR */}
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-5 md:px-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Link
                  href="/projects"
                  className="rounded-lg border border-[#233549] bg-[#111c28] px-2.5 py-1 text-xs text-slate-400 hover:text-white"
                >
                  ← All Projects
                </Link>
                <span className="font-mono text-xs text-emerald-400">{header.projectId}</span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                    header.status === "RED_FLAGGED"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
                      : header.status === "COMPLETED"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                      : "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                  }`}
                >
                  {header.status.replace("_", " ")}
                </span>
              </div>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-white md:text-3xl">
                {header.title}
              </h1>
              <p className="mt-1 text-xs text-slate-400">
                {header.constituency}, {header.state} • Proposer: <strong className="text-slate-200">{header.mpName}</strong> • Category: <strong className="text-slate-200">{header.category}</strong>
              </p>
            </div>

            {/* TOP RIGHT: RISK GAUGE & ROLE ACTIONS */}
            <div className="flex items-center gap-4">
              <RoleSwitcher />

              {/* RISK GAUGE */}
              <div
                className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${
                  isRedFlag
                    ? "border-rose-600/50 bg-rose-950/30"
                    : header.riskScore >= 60
                    ? "border-orange-500/50 bg-orange-950/30"
                    : "border-emerald-500/50 bg-emerald-950/20"
                }`}
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-full text-lg font-black shadow-lg ${
                    isRedFlag
                      ? "bg-rose-600 text-white animate-pulse"
                      : header.riskScore >= 60
                      ? "bg-orange-600 text-white"
                      : "bg-emerald-600 text-white"
                  }`}
                >
                  {header.riskScore}
                </div>
                <div>
                  <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                    AI Risk Level
                  </div>
                  <div
                    className={`text-sm font-extrabold ${
                      isRedFlag
                        ? "text-rose-400"
                        : header.riskScore >= 60
                        ? "text-orange-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {header.riskLevel.replace("_", " ")}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ACTION BUTTONS STRIP */}
          <div className="mt-4 flex flex-wrap items-center gap-2 pt-3 border-t border-[#1d2a38]">
            {canApproveProject(currentUser.role) && header.status === "SUBMITTED" && (
              <button
                onClick={() => setShowApprovalModal(true)}
                className="rounded-lg bg-blue-600 hover:bg-blue-500 px-3.5 py-1.5 text-xs font-semibold text-white transition shadow"
              >
                ✓ Digitally Approve Project
              </button>
            )}

            {canAwardTender(currentUser.role) && (header.status === "APPROVED" || !tender.contractorName) && (
              <button
                onClick={() => setShowTenderModal(true)}
                className="rounded-lg bg-purple-600 hover:bg-purple-500 px-3.5 py-1.5 text-xs font-semibold text-white transition shadow"
              >
                ⚖ Award Tender / Work Order
              </button>
            )}

            {canAddExpenditure(currentUser.role) && (
              <button
                onClick={() => setShowExpenseModal(true)}
                className="rounded-lg bg-sky-600 hover:bg-sky-500 px-3.5 py-1.5 text-xs font-semibold text-white transition shadow"
              >
                + Append Expenditure
              </button>
            )}

            {canSubmitProgress(currentUser.role) && (
              <button
                onClick={() => setShowProgressModal(true)}
                className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3.5 py-1.5 text-xs font-semibold text-white transition shadow"
              >
                📸 Submit Milestone Progress
              </button>
            )}

            {canManageInvestigation(currentUser.role) && (
              <button
                onClick={() => setShowNoteModal(true)}
                className="rounded-lg bg-rose-600 hover:bg-rose-500 px-3.5 py-1.5 text-xs font-semibold text-white transition shadow ml-auto"
              >
                🔍 Record Investigation Action
              </button>
            )}
          </div>
        </header>

        {/* 10-TAB NAVIGATION */}
        <div className="border-b border-[#1d2a38] bg-[#0a1017] px-6 md:px-8 overflow-x-auto">
          <div className="flex space-x-1 py-2 min-w-max">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`rounded-lg px-3.5 py-2 text-xs font-medium transition ${
                  activeTab === t.id
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#121c27]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* TAB CONTENTS */}
        <div className="p-6 md:p-8 space-y-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* FINANCIAL KPI CARDS */}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-4">
                  <span className="text-[10px] uppercase text-slate-500">Proposed / Sanction</span>
                  <p className="mt-1 text-xl font-bold text-white">₹{header.allocatedAmount.toLocaleString("en-IN")}</p>
                  <p className="text-[10px] text-slate-400 mt-1">Official MP recommendation</p>
                </div>
                <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-4">
                  <span className="text-[10px] uppercase text-slate-500">Awarded Contract</span>
                  <p className="mt-1 text-xl font-bold text-purple-400">₹{header.awardedAmount.toLocaleString("en-IN")}</p>
                  <p className="text-[10px] text-slate-400 mt-1">Contractor: {tender.contractorName}</p>
                </div>
                <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-4">
                  <span className="text-[10px] uppercase text-slate-500">Actual Expenditure</span>
                  <p className="mt-1 text-xl font-bold text-sky-400">₹{header.expenditureAmount.toLocaleString("en-IN")}</p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {((header.expenditureAmount / (header.awardedAmount || 1)) * 100).toFixed(1)}% of ceiling utilized
                  </p>
                </div>
                <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-4">
                  <span className="text-[10px] uppercase text-slate-500">Field Checkpoints</span>
                  <p className="mt-1 text-xl font-bold text-emerald-400">
                    {header.verifiedCheckpointsCount}/5 Verified
                  </p>
                  <p className="text-[10px] text-slate-400 mt-1">5-location geofence status</p>
                </div>
              </div>

              {/* PROGRESS BAR STRIP */}
              <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-5">
                <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-wider">
                  Physical vs Financial Execution Divergence
                </h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-emerald-400 font-medium">Physical Progress</span>
                      <span className="font-bold">
                        {progressUpdates.length > 0 ? progressUpdates[progressUpdates.length - 1].physical : 0}%
                      </span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 transition-all duration-500"
                        style={{
                          width: `${progressUpdates.length > 0 ? progressUpdates[progressUpdates.length - 1].physical : 0}%`
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-sky-400 font-medium">Financial Fund Disbursed</span>
                      <span className="font-bold">
                        {header.awardedAmount > 0 ? ((header.expenditureAmount / header.awardedAmount) * 100).toFixed(1) : 0}%
                      </span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-sky-500 transition-all duration-500"
                        style={{
                          width: `${Math.min(100, header.awardedAmount > 0 ? (header.expenditureAmount / header.awardedAmount) * 100 : 0)}%`
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PROPOSAL */}
          {activeTab === "proposal" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-4 text-xs">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                MP Project Proposal Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-500 uppercase text-[10px]">Proposing MP</span>
                  <p className="text-white font-semibold text-sm">{proposal.mpName}</p>
                </div>
                <div>
                  <span className="text-slate-500 uppercase text-[10px]">Proposed Location</span>
                  <p className="text-white font-semibold text-sm">{proposal.proposedLocation}</p>
                </div>
                <div>
                  <span className="text-slate-500 uppercase text-[10px]">Coordinates</span>
                  <p className="text-emerald-400 font-mono">{proposal.latitude?.toFixed(4)}, {proposal.longitude?.toFixed(4)}</p>
                </div>
                <div>
                  <span className="text-slate-500 uppercase text-[10px]">Target Beneficiaries</span>
                  <p className="text-white">{proposal.beneficiaryInfo}</p>
                </div>
              </div>
              <div className="pt-3 border-t border-[#1d2a38]">
                <span className="text-slate-500 uppercase text-[10px]">Work Description & Objectives</span>
                <p className="text-slate-300 mt-1 leading-relaxed">{proposal.description}</p>
              </div>
            </div>
          )}

          {/* TAB 3: APPROVAL */}
          {activeTab === "approval" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-4 text-xs">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Digital Identity Verification & Statutory Approval
              </h3>
              {approval.isApproved ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <span className="text-slate-500 uppercase text-[10px]">Approved By</span>
                      <p className="text-white font-bold">{approval.approvedBy}</p>
                      <p className="text-slate-400 text-[11px]">{approval.designation}</p>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px]">Official ID Reference</span>
                      <p className="font-mono text-emerald-400 font-bold">{approval.officialId}</p>
                      <p className="text-slate-400 text-[11px]">{approval.maskedIdPreview}</p>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px]">Sanction Date</span>
                      <p className="text-white">{approval.approvalDate}</p>
                    </div>
                  </div>

                  <div className="rounded-lg border border-[#1d2a38] bg-[#0c131c] p-4 space-y-2">
                    <span className="text-slate-500 uppercase text-[10px]">Cryptographic SHA-256 Hashes</span>
                    <p className="font-mono text-[10px] text-slate-300 truncate">
                      Document Hash: <strong className="text-emerald-400">{approval.documentHash}</strong>
                    </p>
                    <p className="font-mono text-[10px] text-slate-300 truncate">
                      Digital Signature: <strong className="text-emerald-400">{approval.digitalSignature}</strong>
                    </p>
                  </div>

                  <div>
                    <span className="text-slate-500 uppercase text-[10px]">Sanction Remarks</span>
                    <p className="text-slate-300 mt-1">{approval.remarks}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <p>This project proposal has not yet been approved by authorized personnel.</p>
                  {canApproveProject(currentUser.role) && (
                    <button
                      onClick={() => setShowApprovalModal(true)}
                      className="mt-3 rounded-lg bg-blue-600 hover:bg-blue-500 px-4 py-2 text-xs font-semibold text-white"
                    >
                      Digitally Approve Now
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: TENDER */}
          {activeTab === "tender" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-4 text-xs">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Tender Award & Contractor Risk Record
              </h3>
              {tender.contractorName !== "Not Assigned" ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <span className="text-slate-500 uppercase text-[10px]">Contractor Entity</span>
                      <p className="text-white font-bold text-sm">{tender.contractorName}</p>
                      <p className="font-mono text-emerald-400 text-[11px]">{tender.registrationNumber}</p>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px]">Awarded Amount</span>
                      <p className="text-white font-bold text-sm">₹{tender.awardedAmount.toLocaleString("en-IN")}</p>
                      <p className={`text-[11px] ${tender.tenderDeviationPercent > 15 ? 'text-rose-400' : 'text-slate-400'}`}>
                        {tender.tenderDeviationPercent > 0 ? `+${tender.tenderDeviationPercent}%` : `${tender.tenderDeviationPercent}%`} deviation vs estimate
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px]">Work Order Number</span>
                      <p className="font-mono text-white">{tender.workOrderNumber}</p>
                    </div>
                  </div>

                  {tender.contractorRisk && (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-4">
                      <span className="text-amber-400 uppercase text-[10px] font-bold">
                        Entity Network Intelligence
                      </span>
                      <p className="mt-1 text-slate-200">
                        This contractor has <strong>{tender.contractorRisk.suspiciousProjects}</strong> suspicious/red-flagged works in the national database. Entity Risk Score: <strong>{tender.contractorRisk.riskScore}/100</strong>.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-slate-400">No tender awarded yet.</p>
              )}
            </div>
          )}

          {/* TAB 5: FINANCIAL LEDGER */}
          {activeTab === "financial" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Append-Only Expenditure Ledger
                </h3>
                {canAddExpenditure(currentUser.role) && (
                  <button
                    onClick={() => setShowExpenseModal(true)}
                    className="rounded-lg bg-sky-600 hover:bg-sky-500 px-3 py-1.5 text-xs font-semibold text-white"
                  >
                    + Record Transaction
                  </button>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-[#1d2a38] text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="py-2.5">Date</th>
                      <th className="py-2.5">Invoice #</th>
                      <th className="py-2.5">Category</th>
                      <th className="py-2.5">Description</th>
                      <th className="py-2.5">Amount (₹)</th>
                      <th className="py-2.5">Cumulative (₹)</th>
                      <th className="py-2.5">Entered By</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#172230]">
                    {expenditures.map((tx: any) => (
                      <tr key={tx.id} className="hover:bg-[#121c27]">
                        <td className="py-2.5 font-mono text-slate-300">{tx.date}</td>
                        <td className="py-2.5 font-mono text-emerald-400">{tx.invoice || "N/A"}</td>
                        <td className="py-2.5">{tx.category}</td>
                        <td className="py-2.5 text-slate-300">{tx.description}</td>
                        <td className="py-2.5 font-semibold text-white">₹{tx.amount.toLocaleString("en-IN")}</td>
                        <td className="py-2.5 font-semibold text-sky-400">₹{tx.cumulative.toLocaleString("en-IN")}</td>
                        <td className="py-2.5 text-slate-400">{tx.enteredBy}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: PROGRESS TIMELINE */}
          {activeTab === "progress" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Physical Execution Milestones
                </h3>
                {canSubmitProgress(currentUser.role) && (
                  <button
                    onClick={() => setShowProgressModal(true)}
                    className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white"
                  >
                    + Submit Progress
                  </button>
                )}
              </div>

              <div className="space-y-3">
                {progressUpdates.map((pr: any) => (
                  <div key={pr.id} className="rounded-lg border border-[#1d2a38] bg-[#0c131c] p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div>
                      <span className="font-mono text-slate-500 text-[10px]">{pr.date} • Officer: {pr.officer}</span>
                      <p className="text-white font-semibold text-sm mt-0.5">{pr.description}</p>
                      <p className="text-slate-400 text-xs mt-1">
                        Physical Progress: <strong className="text-emerald-400">{pr.physical}%</strong> • Financial Progress: <strong className="text-sky-400">{pr.financial}%</strong>
                      </p>
                    </div>
                    {pr.photo && (
                      <div className="flex items-center gap-3">
                        <img src={pr.photo} alt="Field proof" className="h-16 w-24 object-cover rounded-lg border border-slate-700" />
                        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-800/40">
                          SHA-256 Verified
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: 5-GEO CHECKPOINTS */}
          {activeTab === "checkpoints" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[#1d2a38] pb-4">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                    5-Location Field Verification Checkpoints
                  </h3>
                  <p className="text-xs text-slate-400">
                    Geofenced checkpoints requiring site photographs within registered threshold radiuses.
                  </p>
                </div>
                <span className="rounded-full bg-emerald-500/20 border border-emerald-500/40 px-3 py-1 text-xs font-bold text-emerald-400">
                  {header.verifiedCheckpointsCount}/5 Checkpoints Verified
                </span>
              </div>

              {/* CHECKPOINT CARDS */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {checkpoints.map((cp: any) => {
                  const isVerified = cp.status === "VERIFIED";
                  const isMismatch = cp.status === "MISMATCH";

                  return (
                    <div
                      key={cp.code}
                      className={`rounded-xl border p-4 space-y-3 ${
                        isVerified
                          ? "border-emerald-500/30 bg-emerald-950/10"
                          : isMismatch
                          ? "border-rose-500/40 bg-rose-950/20"
                          : "border-[#1d2a38] bg-[#0c131c]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 font-bold font-mono text-xs text-white">
                          {cp.code}
                        </span>
                        <span
                          className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                            isVerified
                              ? "bg-emerald-500/20 text-emerald-300"
                              : isMismatch
                              ? "bg-rose-500/20 text-rose-300"
                              : "bg-slate-700 text-slate-300"
                          }`}
                        >
                          {cp.status}
                        </span>
                      </div>

                      <div>
                        <h4 className="font-semibold text-white text-xs">{cp.name}</h4>
                        <p className="text-[10px] font-mono text-slate-400 mt-1">
                          Expected: {cp.expectedLat.toFixed(4)}, {cp.expectedLng.toFixed(4)}
                        </p>
                        <p className="text-[10px] text-slate-500">
                          Geofence radius: {cp.radius}m
                        </p>
                      </div>

                      {cp.distance !== null && (
                        <div className="text-[11px] font-medium">
                          Discrepancy:{" "}
                          <strong className={isVerified ? "text-emerald-400" : "text-rose-400"}>
                            {cp.distance}m
                          </strong>
                        </div>
                      )}

                      {/* FIELD OFFICER ACTIONS */}
                      {canVerifyCheckpoints(currentUser.role) && (
                        <div className="flex gap-2 pt-2 border-t border-[#1d2a38]">
                          <button
                            onClick={() => handleVerifyCheckpoint(cp.code, false)}
                            className="flex-1 rounded bg-emerald-600 hover:bg-emerald-500 py-1 text-[11px] font-semibold text-white transition"
                          >
                            Verify (Within Radius)
                          </button>
                          <button
                            onClick={() => handleVerifyCheckpoint(cp.code, true)}
                            className="rounded bg-rose-700 hover:bg-rose-600 px-2 py-1 text-[11px] font-semibold text-white transition"
                            title="Simulate out-of-bounds photo"
                          >
                            Simulate Mismatch
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 8: AI RISK ANALYSIS */}
          {activeTab === "risk" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-[#1d2a38] pb-4">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400">
                    TrustUs Explainable Risk Intelligence
                  </span>
                  <h3 className="text-xl font-bold text-white mt-1">
                    Multi-Signal Anomaly Breakdown
                  </h3>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-black text-rose-400">{riskAnalysis.score}/100</span>
                  <p className="text-[10px] text-slate-400 uppercase">{riskAnalysis.level}</p>
                </div>
              </div>

              <div className="rounded-lg bg-[#0c141e] border border-[#233549] p-4 text-xs leading-relaxed text-slate-300">
                <span className="text-emerald-400 font-bold">AI RATIONALE: </span>
                {riskAnalysis.summaryText || "Evaluation based on independent multi-signal anomaly detectors."}
              </div>

              {/* INDIVIDUAL SIGNALS */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Flagged Anomalous Signals ({riskAnalysis.signals?.length || 0})
                </h4>
                {riskAnalysis.signals && riskAnalysis.signals.length > 0 ? (
                  riskAnalysis.signals.map((s: any, idx: number) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-rose-500/30 bg-rose-950/20 p-4 flex items-start gap-3 text-xs"
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-rose-500 text-white font-bold text-xs">
                        !
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <h5 className="font-bold text-white">{s.title}</h5>
                          <span className="rounded bg-rose-900/60 px-2 py-0.5 text-[9px] font-bold text-rose-300">
                            +{s.scoreImpact} pts
                          </span>
                        </div>
                        <p className="mt-1 text-slate-300 leading-relaxed">{s.description}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400">No anomalous signals detected. Project conforms to expected statistical norms.</p>
                )}
              </div>
            </div>
          )}

          {/* TAB 9: INVESTIGATION CASE */}
          {activeTab === "investigation" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-6 text-xs">
              <div className="flex items-center justify-between border-b border-[#1d2a38] pb-4">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400">
                    Official Vigilance & Audit Case
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1">
                    Case ID: {investigation.caseId || "NONE"}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-rose-500/20 border border-rose-500/40 px-3 py-1 text-xs font-bold text-rose-400">
                    Status: {investigation.status}
                  </span>
                  {canManageInvestigation(currentUser.role) && (
                    <button
                      onClick={() => setShowNoteModal(true)}
                      className="rounded-lg bg-rose-600 hover:bg-rose-500 px-3 py-1.5 font-semibold text-white"
                    >
                      + Add Action / Note
                    </button>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                  Investigator Activity Log
                </h4>
                {investigation.notes && investigation.notes.length > 0 ? (
                  investigation.notes.map((n: any) => (
                    <div key={n.id} className="rounded-lg border border-[#1d2a38] bg-[#0c141e] p-4 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-emerald-400">{n.author} ({n.role})</span>
                        <span className="font-mono text-[10px] text-slate-500">{n.timestamp}</span>
                      </div>
                      <span className="inline-block rounded bg-slate-800 px-2 py-0.5 text-[9px] font-bold text-slate-300">
                        {n.actionType}
                      </span>
                      <p className="text-slate-200 mt-2">{n.text}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400">No investigator notes recorded.</p>
                )}
              </div>
            </div>
          )}

          {/* TAB 10: AUDIT TRAIL */}
          {activeTab === "audit" && (
            <div className="rounded-xl border border-[#1d2a38] bg-[#101924] p-6 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Immutable Cryptographic Audit Trail
              </h3>
              <div className="overflow-x-auto text-xs">
                <table className="w-full text-left">
                  <thead className="border-b border-[#1d2a38] text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="py-2.5">Timestamp</th>
                      <th className="py-2.5">User</th>
                      <th className="py-2.5">Role</th>
                      <th className="py-2.5">Action</th>
                      <th className="py-2.5">Details</th>
                      <th className="py-2.5">Event Hash</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#172230]">
                    {auditTrail.map((ev: any) => (
                      <tr key={ev.eventId} className="hover:bg-[#121c27]">
                        <td className="py-2.5 font-mono text-slate-400 text-[11px]">{ev.timestamp}</td>
                        <td className="py-2.5 font-medium text-white">{ev.user}</td>
                        <td className="py-2.5 text-slate-400">{ev.role}</td>
                        <td className="py-2.5 font-bold text-emerald-400">{ev.action}</td>
                        <td className="py-2.5 text-slate-300">{ev.newValue || ev.previousValue || "Action logged"}</td>
                        <td className="py-2.5 font-mono text-[9px] text-slate-500 truncate max-w-xs">{ev.eventHash}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* APPROVAL MODAL */}
      {showApprovalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-[#233549] bg-[#0c141e] p-6 text-xs">
            <h3 className="text-base font-bold text-white mb-3">Digitally Approve Project</h3>
            <form onSubmit={handleApprove} className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">Approving Officer Name</label>
                <input
                  type="text"
                  value={approvalForm.approved_by}
                  onChange={(e) => setApprovalForm({ ...approvalForm, approved_by: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Official ID Badge Reference</label>
                <input
                  type="text"
                  value={approvalForm.official_id}
                  onChange={(e) => setApprovalForm({ ...approvalForm, official_id: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Approval Remarks</label>
                <textarea
                  rows={2}
                  value={approvalForm.remarks}
                  onChange={(e) => setApprovalForm({ ...approvalForm, remarks: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div className="rounded bg-emerald-950/30 border border-emerald-800/40 p-2 text-[11px] text-emerald-300">
                ✓ Synthetic ID Scan Attached • Digital SHA-256 Signature Generated
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowApprovalModal(false)} className="px-3 py-1.5 text-slate-400">Cancel</button>
                <button type="submit" className="rounded bg-blue-600 hover:bg-blue-500 px-4 py-1.5 font-bold text-white">Confirm Approval</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TENDER MODAL */}
      {showTenderModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-[#233549] bg-[#0c141e] p-6 text-xs">
            <h3 className="text-base font-bold text-white mb-3">Award Tender & Work Order</h3>
            <form onSubmit={handleTender} className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">Contractor Name</label>
                <input
                  type="text"
                  value={tenderForm.contractor_name}
                  onChange={(e) => setTenderForm({ ...tenderForm, contractor_name: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Contractor Registration Number</label>
                <input
                  type="text"
                  value={tenderForm.registration_number}
                  onChange={(e) => setTenderForm({ ...tenderForm, registration_number: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Awarded Amount (₹)</label>
                <input
                  type="number"
                  value={tenderForm.awarded_amount}
                  onChange={(e) => setTenderForm({ ...tenderForm, awarded_amount: Number(e.target.value) })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowTenderModal(false)} className="px-3 py-1.5 text-slate-400">Cancel</button>
                <button type="submit" className="rounded bg-purple-600 hover:bg-purple-500 px-4 py-1.5 font-bold text-white">Award Contract</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EXPENSE MODAL */}
      {showExpenseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-[#233549] bg-[#0c141e] p-6 text-xs">
            <h3 className="text-base font-bold text-white mb-3">Append Expenditure Transaction</h3>
            <form onSubmit={handleExpense} className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">Expense Category</label>
                <select
                  value={expenseForm.expense_category}
                  onChange={(e) => setExpenseForm({ ...expenseForm, expense_category: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                >
                  <option value="Civil Materials">Civil Materials</option>
                  <option value="Labor & Wages">Labor & Wages</option>
                  <option value="Heavy Equipment">Heavy Equipment</option>
                  <option value="Electrical & Plumbing">Electrical & Plumbing</option>
                  <option value="Consultancy / Milestone">Consultancy / Milestone</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Description</label>
                <input
                  type="text"
                  value={expenseForm.description}
                  onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Amount (₹)</label>
                <input
                  type="number"
                  value={expenseForm.amount}
                  onChange={(e) => setExpenseForm({ ...expenseForm, amount: Number(e.target.value) })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowExpenseModal(false)} className="px-3 py-1.5 text-slate-400">Cancel</button>
                <button type="submit" className="rounded bg-sky-600 hover:bg-sky-500 px-4 py-1.5 font-bold text-white">Record Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PROGRESS MODAL */}
      {showProgressModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-[#233549] bg-[#0c141e] p-6 text-xs">
            <h3 className="text-base font-bold text-white mb-3">Submit Milestone Progress</h3>
            <form onSubmit={handleProgress} className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">Physical Completion (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={progressForm.physical_progress_percent}
                  onChange={(e) => setProgressForm({ ...progressForm, physical_progress_percent: Number(e.target.value) })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Work Description</label>
                <textarea
                  rows={2}
                  value={progressForm.work_description}
                  onChange={(e) => setProgressForm({ ...progressForm, work_description: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div className="rounded bg-slate-900 border border-slate-800 p-2 text-[11px] text-slate-400">
                📸 Field Photo Automatically Geo-Tagged with Browser Device Coordinates
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowProgressModal(false)} className="px-3 py-1.5 text-slate-400">Cancel</button>
                <button type="submit" className="rounded bg-emerald-600 hover:bg-emerald-500 px-4 py-1.5 font-bold text-white">Submit Progress</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* INVESTIGATION NOTE MODAL */}
      {showNoteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-[#233549] bg-[#0c141e] p-6 text-xs">
            <h3 className="text-base font-bold text-white mb-3">Record Investigation Action</h3>
            <form onSubmit={handleAddNote} className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">Action Type</label>
                <select
                  value={noteForm.action_type}
                  onChange={(e) => setNoteForm({ ...noteForm, action_type: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                >
                  <option value="NOTE">General Audit Note</option>
                  <option value="CLARIFICATION_REQUEST">Request Clarification from MP / Vendor</option>
                  <option value="FIELD_INSPECTION">Schedule Vigilance Field Inspection</option>
                  <option value="ESCALATE">Escalate to Central Vigilance / CAG</option>
                  <option value="RESOLVE">Resolve & Close Investigation</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 mb-1">Notes / Findings Summary</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Enter detailed audit findings or reason for action..."
                  value={noteForm.note_text}
                  onChange={(e) => setNoteForm({ ...noteForm, note_text: e.target.value })}
                  className="w-full rounded bg-[#070d14] border border-[#233549] p-2 text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowNoteModal(false)} className="px-3 py-1.5 text-slate-400">Cancel</button>
                <button type="submit" className="rounded bg-rose-600 hover:bg-rose-500 px-4 py-1.5 font-bold text-white">Record Action</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
