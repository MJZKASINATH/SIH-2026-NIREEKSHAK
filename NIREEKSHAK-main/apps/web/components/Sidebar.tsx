"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const navigation = [
  { name: "Command Centre", href: "/dashboard", icon: "▦" },
  { name: "Projects Directory", href: "/projects", icon: "◫" },
  { name: "Contractor Risk DB", href: "/contractors", icon: "🏢" },
  { name: "Geostatistical Map", href: "/geostat", icon: "🗺" },
  { name: "Investigation Queue", href: "/investigation", icon: "🔍" },
  { name: "Risk Analytics", href: "/analytics", icon: "◒" },
  { name: "Digital Audit Trail", href: "/audit-logs", icon: "📜" },
  { name: "Statutory Reports", href: "/reports", icon: "▤" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <>
      {/* MOBILE HEADER */}
      <div className="sticky top-0 z-40 flex items-center justify-between border-b border-slate-800 bg-[#0b1118]/95 px-5 py-4 backdrop-blur md:hidden">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.7)]" />
          <span className="text-lg font-bold tracking-[0.18em]">
            NIREEKSHAK
          </span>
        </Link>

        <button
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation"
          className="rounded-lg border border-slate-800 px-3 py-2 text-xl text-slate-300 transition hover:border-emerald-900 hover:text-emerald-400"
        >
          ☰
        </button>
      </div>

      {/* DESKTOP SIDEBAR */}
      <div className="hidden w-[250px] min-w-[250px] shrink-0 md:block">
        <aside className="fixed left-0 top-0 z-40 h-screen w-[250px] border-r border-slate-800 bg-[#0b1118] overflow-y-auto">
          <SidebarContent pathname={pathname} />
        </aside>
      </div>

      {/* MOBILE SIDEBAR */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
            className="absolute inset-0 bg-black/60"
          />

          <aside className="relative z-10 flex h-full w-[280px] flex-col border-r border-slate-800 bg-[#0b1118] shadow-2xl overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 px-6 py-6">
              <div className="flex items-center gap-3">
                <div className="h-3.5 w-3.5 rounded-full bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.7)]" />
                <h1 className="text-xl font-bold tracking-[0.2em]">
                  NIREEKSHAK
                </h1>
              </div>

              <button
                onClick={() => setMobileOpen(false)}
                aria-label="Close navigation"
                className="text-xl text-slate-500 transition hover:text-white"
              >
                ×
              </button>
            </div>

            <SidebarNavigation pathname={pathname} />

            <div className="mt-auto p-4">
              <SystemStatus />
            </div>
          </aside>
        </div>
      )}
    </>
  );
}

function SidebarContent({ pathname }: { pathname: string }) {
  return (
    <div className="flex h-screen flex-col">
      {/* BRANDING */}
      <div className="border-b border-slate-800 px-6 py-6">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="h-3.5 w-3.5 rounded-full bg-emerald-400 shadow-[0_0_15px_rgba(52,211,153,0.7)]" />
          <h1 className="text-xl font-bold tracking-[0.2em]">
            NIREEKSHAK
          </h1>
        </Link>

        <p className="mt-2 pl-6 text-[10px] tracking-[0.2em] text-slate-500">
          MPLADS RISK INTELLIGENCE
        </p>
      </div>

      {/* NAVIGATION */}
      <div className="flex-1 overflow-y-auto">
        <SidebarNavigation pathname={pathname} />
      </div>

      {/* SYSTEM STATUS */}
      <div className="mt-auto px-4 pb-5 pt-2">
        <SystemStatus />
      </div>
    </div>
  );
}

function SidebarNavigation({ pathname }: { pathname: string }) {
  return (
    <div className="px-3 py-4">
      <p className="px-3 text-[10px] font-medium tracking-[0.25em] text-slate-600 uppercase">
        Navigation
      </p>

      <nav className="mt-3 space-y-1">
        {navigation.map((item) => {
          const active =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(`${item.href}`));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-xs transition ${
                active
                  ? "border border-emerald-900/70 bg-emerald-950/30 text-emerald-400 font-semibold"
                  : "border border-transparent text-slate-400 hover:border-slate-800 hover:bg-slate-900/50 hover:text-slate-200"
              }`}
            >
              <span className="w-4 text-center text-sm">{item.icon}</span>
              <span>{item.name}</span>
              {active && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

function SystemStatus() {
  return (
    <div className="rounded-lg border border-slate-800 bg-[#101820] p-4">
      <div className="flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]" />
        <span className="text-[11px] font-bold tracking-wider text-emerald-300">
          CORE OPERATIONAL
        </span>
      </div>

      <p className="mt-2 text-[10px] text-slate-400">
        AI Risk Engine & 5-Geo Checkpoints Active
      </p>

      <div className="mt-3 border-t border-slate-800/80 pt-2 flex items-center justify-between text-[9px] font-mono text-slate-500">
        <span>SIH26102</span>
        <span>PHASE 2</span>
      </div>
    </div>
  );
}