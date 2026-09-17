"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";

export interface MapMarker {
  projectId: string;
  title: string;
  latitude: number;
  longitude: number;
  riskScore: number;
  riskLevel: string;
  cost: number;
  expenditure: number;
  physicalProgress?: number;
  financialUtilization?: number;
  status: string;
  state: string;
  district?: string;
  constituency: string;
  contractor: string;
  contractorSuspicious: number;
  isRedFlag: boolean;
  category?: string;
  checkpointsVerified?: number;
  totalCheckpoints?: number;
}

interface GeostatMapProps {
  initialMarkers?: MapMarker[];
  height?: string;
  showFilters?: boolean;
}

export type ActiveLayer = "projects" | "risk_heatmap" | "expenditure" | "red_flags" | "contractor";

export default function GeostatMap({
  initialMarkers,
  height = "560px",
  showFilters = true
}: GeostatMapProps) {
  const [markers, setMarkers] = useState<MapMarker[]>(initialMarkers || []);
  const [loading, setLoading] = useState(!initialMarkers);
  const [error, setError] = useState<string | null>(null);
  const [activeLayer, setActiveLayer] = useState<ActiveLayer>("projects");
  const [search, setSearch] = useState("");
  const [selectedState, setSelectedState] = useState("ALL");
  const [selectedRisk, setSelectedRisk] = useState("ALL");
  const [availableStates, setAvailableStates] = useState<string[]>([]);
  const [mapReady, setMapReady] = useState(false);

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);
  const layerGroupRef = useRef<any>(null);

  // Fetch real coordinates from backend API endpoint (/api/geostat/projects)
  useEffect(() => {
    if (!initialMarkers) {
      setLoading(true);
      setError(null);
      fetch("/api/geostat/projects")
        .then((res) => {
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
          }
          return res.json();
        })
        .then((data) => {
          const projectItems: MapMarker[] = data.projects || data.markers || [];
          setMarkers(projectItems);
          if (data.filters?.states && Array.isArray(data.filters.states)) {
            setAvailableStates(data.filters.states);
          }
          setLoading(false);
        })
        .catch((err) => {
          console.error("Failed to load map points:", err);
          setError(err.message || "Failed to load geolocated project points");
          setMarkers([]);
          setLoading(false);
        });
    }
  }, [initialMarkers]);

  // Distinct states for filtering
  const statesList = useMemo(() => {
    if (availableStates.length > 0) return availableStates;
    const s = new Set<string>();
    markers.forEach((m) => {
      if (m.state && m.state !== "Unknown") s.add(m.state);
    });
    return Array.from(s).sort();
  }, [markers, availableStates]);

  // Filtered markers based on query, state, risk, and active layer
  const filteredMarkers = useMemo(() => {
    return markers.filter((m) => {
      const matchQuery =
        !search ||
        (m.title && m.title.toLowerCase().includes(search.toLowerCase())) ||
        (m.projectId && m.projectId.toLowerCase().includes(search.toLowerCase())) ||
        (m.contractor && m.contractor.toLowerCase().includes(search.toLowerCase()));

      const matchState = selectedState === "ALL" || m.state === selectedState;
      const matchRisk =
        selectedRisk === "ALL" ||
        (selectedRisk === "RED_FLAG" && (m.riskScore >= 80 || m.isRedFlag)) ||
        (selectedRisk === "HIGH" && m.riskScore >= 60 && m.riskScore < 80) ||
        (selectedRisk === "MEDIUM" && m.riskScore >= 30 && m.riskScore < 60) ||
        (selectedRisk === "LOW" && m.riskScore < 30);

      if (activeLayer === "red_flags" && !m.isRedFlag && m.riskScore < 80) return false;
      if (activeLayer === "contractor" && (!m.contractorSuspicious || m.contractorSuspicious === 0)) return false;

      return matchQuery && matchState && matchRisk;
    });
  }, [markers, search, selectedState, selectedRisk, activeLayer]);

  // Initialize Leaflet Map with CARTO Basemap
  useEffect(() => {
    if (typeof window === "undefined" || !mapContainerRef.current) return;

    let isMounted = true;

    // Dynamically import Leaflet client-side
    import("leaflet").then((L) => {
      if (!isMounted || !mapContainerRef.current) return;

      // Fix icon issues in Leaflet with webpack
      delete (L.Icon.Default.prototype as any)._getIconUrl;

      if (!leafletMapRef.current) {
        const map = L.map(mapContainerRef.current, {
          center: [21.5, 79.0], // Center of India
          zoom: 5,
          minZoom: 4,
          maxZoom: 18,
          attributionControl: false
        });

        // CartoDB Dark Matter tile layer with process.env key if provided
        const cartoKey = process.env.NEXT_PUBLIC_CARTO_API_KEY || "";
        const tileUrl = cartoKey
          ? `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${cartoKey}`
          : `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png`;

        L.tileLayer(tileUrl, {
          subdomains: "abcd",
          maxZoom: 19
        }).addTo(map);

        L.control.attribution({ position: "bottomright" })
          .addAttribution('&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>')
          .addTo(map);

        const group = L.layerGroup().addTo(map);
        layerGroupRef.current = group;
        leafletMapRef.current = map;
        setMapReady(true);
      }
    });

    return () => {
      isMounted = false;
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  // Update Markers, Layer Visualization & Fit Bounds
  useEffect(() => {
    if (!mapReady || !leafletMapRef.current || !layerGroupRef.current) return;

    import("leaflet").then((L) => {
      const group = layerGroupRef.current;
      group.clearLayers();

      const validCoords: [number, number][] = [];

      filteredMarkers.forEach((m) => {
        if (!m.latitude || !m.longitude) return;
        validCoords.push([m.latitude, m.longitude]);

        let markerColor = "#10b981"; // Low risk emerald
        if (m.riskScore >= 80 || m.isRedFlag) markerColor = "#f43f5e"; // Red flag rose
        else if (m.riskScore >= 60) markerColor = "#f97316"; // High orange
        else if (m.riskScore >= 30) markerColor = "#eab308"; // Medium amber

        const costFormatted = (m.cost / 100000).toFixed(1);
        const expFormatted = (m.expenditure / 100000).toFixed(1);
        const phys = m.physicalProgress !== undefined && m.physicalProgress !== null ? `${m.physicalProgress}%` : "N/A";
        const fin = m.financialUtilization !== undefined && m.financialUtilization !== null ? `${m.financialUtilization}%` : "N/A";
        const ckVerified = m.checkpointsVerified !== undefined ? m.checkpointsVerified : 0;
        const ckTotal = m.totalCheckpoints !== undefined ? m.totalCheckpoints : 0;
        const ckDisplay = ckTotal > 0 ? `${ckVerified}/${ckTotal} Verified` : "Pending Verification";

        const popupContent = `
          <div style="font-family: inherit; min-width: 250px; color: #fff; background: #0e1724; padding: 12px; border-radius: 10px; border: 1px solid #1e293b;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
              <span style="font-size: 9px; font-weight: 700; letter-spacing: 0.15em; color: #10b981; text-transform: uppercase;">${m.projectId}</span>
              <span style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: ${markerColor}25; color: ${markerColor}; border: 1px solid ${markerColor}50;">
                ${m.riskScore}/100 • ${m.riskLevel}
              </span>
            </div>
            <h4 style="font-size: 13px; font-weight: 700; line-height: 1.3; margin: 0 0 6px 0; color: #fff;">${m.title}</h4>
            <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">
              📍 ${m.constituency}${m.state ? `, ${m.state}` : ''}<br/>
              🏢 Vendor: <strong style="color: #cbd5e1;">${m.contractor || "Unassigned"}</strong>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; background: #131d2e; padding: 6px; border-radius: 6px; font-size: 10px; margin-bottom: 8px;">
              <div>Allocated: <strong>₹${costFormatted} L</strong></div>
              <div>Spent: <strong>₹${expFormatted} L</strong></div>
              <div>Physical: <strong style="color: #38bdf8;">${phys}</strong></div>
              <div>Financial: <strong style="color: ${m.riskScore >= 60 ? '#f43f5e' : '#38bdf8'};">${fin}</strong></div>
            </div>
            <div style="font-size: 10px; color: #94a3b8; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; background: #0b121c; padding: 4px 8px; border-radius: 4px;">
              <span>Checkpoints:</span>
              <strong style="color: ${ckVerified > 0 ? '#10b981' : '#f59e0b'};">${ckDisplay}</strong>
            </div>
            <a href="/projects/${m.projectId}" style="display: block; text-align: center; background: #059669; color: #fff; text-decoration: none; padding: 6px 10px; font-size: 11px; font-weight: 600; border-radius: 6px; transition: 0.2s;">
              View Project →
            </a>
          </div>
        `;

        // Render based on active analytical layer
        if (activeLayer === "risk_heatmap") {
          const radiusMeters = Math.max(25000, m.riskScore * 800);
          const circle = L.circle([m.latitude, m.longitude], {
            color: markerColor,
            fillColor: markerColor,
            fillOpacity: 0.45,
            radius: radiusMeters,
            weight: 2
          });
          circle.bindPopup(popupContent, { className: "custom-leaflet-popup" });
          group.addLayer(circle);
        } else if (activeLayer === "expenditure") {
          const radiusMeters = Math.max(20000, (m.expenditure / 100000) * 1200);
          const circle = L.circle([m.latitude, m.longitude], {
            color: "#38bdf8",
            fillColor: "#0284c7",
            fillOpacity: 0.4,
            radius: radiusMeters,
            weight: 2
          });
          circle.bindPopup(popupContent, { className: "custom-leaflet-popup" });
          group.addLayer(circle);
        } else {
          const customIcon = L.divIcon({
            className: "custom-map-pin",
            html: `
              <div style="position: relative; width: 24px; height: 24px;">
                <div style="position: absolute; inset: 0; border-radius: 9999px; background: ${markerColor}; opacity: 0.4; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
                <div style="position: relative; width: 14px; height: 14px; margin: 5px auto; border-radius: 9999px; background: ${markerColor}; border: 2px solid #0e1622; box-shadow: 0 0 10px ${markerColor};"></div>
              </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          const marker = L.marker([m.latitude, m.longitude], { icon: customIcon });
          marker.bindPopup(popupContent, { className: "custom-leaflet-popup" });
          group.addLayer(marker);
        }
      });

      // Fit bounds if markers are present
      if (validCoords.length > 0 && leafletMapRef.current) {
        try {
          const bounds = L.latLngBounds(validCoords);
          leafletMapRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
        } catch (_err) {
          // ignore fit bounds error if bounds are invalid
        }
      }
    });
  }, [mapReady, filteredMarkers, activeLayer]);

  const layerOptions: { id: ActiveLayer; label: string; icon: string }[] = [
    { id: "projects", label: "Projects", icon: "📍" },
    { id: "risk_heatmap", label: "Risk Severity Heatmap", icon: "🔥" },
    { id: "expenditure", label: "Expenditure Scale", icon: "💰" },
    { id: "red_flags", label: "Red Flags Only", icon: "🚨" },
    { id: "contractor", label: "Contractor Risk Concentration", icon: "🏢" }
  ];

  return (
    <div className="rounded-2xl border border-[#1e2a38] bg-[#0c131d] overflow-hidden shadow-2xl relative">
      {/* MAP HEADER & LAYER SELECTOR */}
      {showFilters && (
        <div className="p-4 border-b border-[#1e2a38] bg-[#0e1622] flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] font-bold tracking-[0.25em] text-emerald-400 uppercase">
                Geospatial Surveillance Engine
              </span>
            </div>
            <h2 className="text-base font-bold text-white mt-0.5">
              Live MPLADS Asset Map ({filteredMarkers.length} Mapped Assets)
            </h2>
          </div>

          {/* Layer Selector Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-xl bg-[#090e15] border border-slate-800">
            {layerOptions.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setActiveLayer(opt.id)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
                  activeLayer === opt.id
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                <span>{opt.icon}</span>
                <span>{opt.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* FILTER BAR */}
      {showFilters && (
        <div className="px-4 py-2.5 border-b border-[#1e2a38] bg-[#090f17] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <input
              type="text"
              placeholder="Search title, ID or contractor..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="rounded-lg border border-slate-700/80 bg-[#121c2a] px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none w-56"
            />

            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="rounded-lg border border-slate-700/80 bg-[#121c2a] px-3 py-1.5 text-xs text-slate-300 focus:border-emerald-500 focus:outline-none"
            >
              <option value="ALL">All States ({statesList.length})</option>
              {statesList.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>

            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="rounded-lg border border-slate-700/80 bg-[#121c2a] px-3 py-1.5 text-xs text-slate-300 focus:border-emerald-500 focus:outline-none"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="RED_FLAG">Red Flag Only (80-100)</option>
              <option value="HIGH">High Risk (60-79)</option>
              <option value="MEDIUM">Medium Risk (30-59)</option>
              <option value="LOW">Low Risk (0-29)</option>
            </select>
          </div>

          <div className="flex items-center gap-4 text-[11px] text-slate-400 font-mono">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              <span>Red Flag</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-orange-500" />
              <span>High</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              <span>Medium</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>Low</span>
            </span>
          </div>
        </div>
      )}

      {/* LEAFLET MAP CONTAINER */}
      <div className="relative w-full" style={{ height }}>
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#0b1016]/80 backdrop-blur-sm">
            <div className="flex flex-col items-center gap-2 text-slate-400">
              <span className="h-6 w-6 border-2 border-emerald-500/30 border-t-emerald-400 rounded-full animate-spin" />
              <span className="text-xs font-mono">Loading database geostatistical coordinates...</span>
            </div>
          </div>
        )}

        {!loading && filteredMarkers.length === 0 && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#0b1016]/90 p-6 text-center">
            <div className="max-w-md">
              <span className="text-3xl">🗺️</span>
              <h3 className="mt-2 text-base font-bold text-white">
                {error ? "Backend Connection Notice" : "No geolocated projects available"}
              </h3>
              <p className="mt-1 text-xs text-slate-400">
                {error
                  ? error
                  : "There are currently no registered projects matching the selected filter criteria with GPS coordinates."}
              </p>
            </div>
          </div>
        )}

        <div ref={mapContainerRef} className="w-full h-full z-0" />
      </div>

      {/* FOOTER STATS STRIP */}
      <div className="px-4 py-2 border-t border-[#1e2a38] bg-[#0a1017] flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <div>
          Layer: <strong className="text-white uppercase">{activeLayer.replace("_", " ")}</strong>
        </div>
        <div>
          Map Projection: <strong className="text-slate-300">WGS84 • OpenStreetMap / CartoDB Dark</strong>
        </div>
      </div>
    </div>
  );
}
