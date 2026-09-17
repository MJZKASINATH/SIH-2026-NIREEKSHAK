"use client";

import React, { useState } from "react";
import { getStoredRole, getAuthHeaders } from "../../lib/auth";

interface ProposeProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newProject: any) => void;
}

const INDIAN_STATES = [
  "Kerala", "Tamil Nadu", "Karnataka", "Maharashtra", "Uttar Pradesh",
  "Delhi", "West Bengal", "Rajasthan", "Andhra Pradesh", "Gujarat",
  "Madhya Pradesh", "Bihar", "Odisha", "Punjab", "Haryana"
];

const CATEGORIES = [
  "Roads & Bridges",
  "Healthcare",
  "Education",
  "Drinking Water",
  "Community Infrastructure",
  "Sanitation & Sewerage",
  "Irrigation & Flood Control",
  "Renewable Energy / Solar"
];

export default function ProposeProjectModal({
  isOpen,
  onClose,
  onSuccess
}: ProposeProjectModalProps) {
  const currentUser = getStoredRole();

  const [formData, setFormData] = useState({
    mp_name: currentUser.full_name || "Rahul Verma, MP",
    mp_constituency: "Wayanad",
    state: "Kerala",
    district: "Wayanad",
    local_body: "Sulthan Bathery Block",
    title: "",
    description: "",
    category: "Community Infrastructure",
    proposed_amount: 3500000,
    estimated_cost: 3500000,
    beneficiary_info: "Estimated 1,200 local residents and tribal families",
    proposed_location: "Sulthan Bathery Sector 4",
    latitude: 11.6664,
    longitude: 76.2627
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.description) {
      setError("Please fill in project title and description.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const res = await fetch("/api/projects/propose", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          ...formData,
          proposed_amount: Number(formData.proposed_amount),
          estimated_cost: Number(formData.estimated_cost),
          latitude: Number(formData.latitude),
          longitude: Number(formData.longitude)
        })
      });

      if (!res.ok) {
        throw new Error("Failed to submit proposal to server.");
      }

      const created = await res.json();
      onSuccess(created);
      onClose();
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Error creating project proposal.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl rounded-2xl border border-[#23384e] bg-[#0c141e] p-6 shadow-2xl my-8">
        <div className="flex items-center justify-between border-b border-[#1f2f42] pb-4">
          <div>
            <span className="text-[10px] font-bold tracking-[0.25em] text-emerald-400 uppercase">
              Official MPLADS Project Registration
            </span>
            <h2 className="mt-1 text-xl font-bold text-white">
              Submit New Project Proposal
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-[#162331] hover:text-white"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/30 border border-red-700/50 p-3 text-xs text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4 text-xs">
          {/* Proposer Info Strip */}
          <div className="rounded-lg border border-[#1d2a38] bg-[#111c29] p-3 flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-medium">Proposing MP</span>
              <p className="font-semibold text-white">{formData.mp_name}</p>
            </div>
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-medium">Constituency</span>
              <p className="font-semibold text-emerald-400">{formData.mp_constituency}, {formData.state}</p>
            </div>
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-medium">ID Format</span>
              <p className="font-mono text-slate-400">MPLADS-2026-XX-XXXXXX</p>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Project Title <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Construction of Community Health & Skill Centre"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3.5 py-2.5 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">
              Detailed Scope / Work Description <span className="text-rose-400">*</span>
            </label>
            <textarea
              required
              rows={3}
              placeholder="Describe physical specifications, beneficiary targets, and planned utility..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3.5 py-2.5 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3.5 py-2.5 text-white focus:border-emerald-500 focus:outline-none"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">State</label>
              <select
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3.5 py-2.5 text-white focus:border-emerald-500 focus:outline-none"
              >
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Proposed Recommendation Amount (₹)
              </label>
              <input
                type="number"
                min="50000"
                step="50000"
                value={formData.proposed_amount}
                onChange={(e) => setFormData({ ...formData, proposed_amount: Number(e.target.value), estimated_cost: Number(e.target.value) })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3.5 py-2.5 text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">
                Estimated Engineering Cost (₹)
              </label>
              <input
                type="number"
                min="50000"
                step="50000"
                value={formData.estimated_cost}
                onChange={(e) => setFormData({ ...formData, estimated_cost: Number(e.target.value) })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3.5 py-2.5 text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-1">
              <label className="block text-slate-300 font-medium mb-1">Site Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: Number(e.target.value) })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3 py-2 text-white font-mono"
              />
            </div>
            <div className="sm:col-span-1">
              <label className="block text-slate-300 font-medium mb-1">Site Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: Number(e.target.value) })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3 py-2 text-white font-mono"
              />
            </div>
            <div className="sm:col-span-1">
              <label className="block text-slate-300 font-medium mb-1">District / Block</label>
              <input
                type="text"
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                className="w-full rounded-lg border border-[#233549] bg-[#070d14] px-3 py-2 text-white"
              />
            </div>
          </div>

          <div className="rounded-lg border border-dashed border-[#23384e] bg-[#091017] p-3 text-center">
            <span className="text-[11px] text-slate-400">
              📎 Supporting Documents: Detailed Project Report (DPR), Cadastral Survey & Beneficiary Endorsement
            </span>
            <div className="mt-1 text-[10px] text-emerald-400 font-medium">
              [Auto-Attached: DPR-2026-SYNTHETIC-VERIFIED.pdf • 1.4 MB]
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#1f2f42]">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-slate-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-6 py-2.5 font-semibold text-white transition shadow-lg disabled:opacity-50"
            >
              {submitting ? "Registering Proposal..." : "Submit Proposal →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
