"use client";

import React from "react";
import Sidebar from "../../components/Sidebar";
import RoleSwitcher from "../../components/RoleSwitcher";
import GeostatMap from "../../components/map/GeostatMap";

export default function GeostatPage() {
  return (
    <div className="flex min-h-screen bg-[#0b1016] text-white">
      <Sidebar />

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-hidden">
        <header className="border-b border-[#1d2a38] bg-[#0e1620] px-6 py-4 flex items-center justify-between shrink-0">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-emerald-400">
              Spatial Decision Support System
            </span>
            <h1 className="text-xl font-bold text-white">
              Geostatistical Intelligence Map
            </h1>
          </div>
          <RoleSwitcher />
        </header>

        <div className="flex-1 p-4 overflow-y-auto flex flex-col min-h-[650px]">
          <GeostatMap height="600px" showFilters={true} />
        </div>
      </main>
    </div>
  );
}
