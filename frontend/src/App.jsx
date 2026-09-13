import React, { useState, useEffect, useMemo } from 'react';
import {
  Shield,
  Radio,
  Search,
  SlidersHorizontal,
  ChevronRight,
  ChevronLeft,
  Activity,
  LineChart as ChartIcon,
  Cpu,
  Sparkles,
  Compass,
  ShieldCheck,
  ShieldAlert,
  Satellite,
  Sliders,
  Layers,
  X,
} from 'lucide-react';

import GisMap from './components/GisMap';
import TelemetryHUD from './components/TelemetryHUD';
import DiagnosticTrace from './components/DiagnosticTrace';
import ShapPanel from './components/ShapPanel';
import SpatialNeighbors from './components/SpatialNeighbors';
import SatelliteView from './components/SatelliteView';
import AnomalySandbox from './components/AnomalySandbox';
import CustomAnomalyModal from './components/CustomAnomalyModal';
import StationDirectoryModal from './components/StationDirectoryModal';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function App() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [nearestNeighbors, setNearestNeighbors] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [latestResult, setLatestResult] = useState(null);
  const [satelliteData, setSatelliteData] = useState(null);
  const [showCorrected, setShowCorrected] = useState(true);
  const [loading, setLoading] = useState(true);
  const [timeStr, setTimeStr] = useState('');

  // UI State: Active Inspector Tab & Drawer Collapse
  const [activeTab, setActiveTab] = useState('telemetry'); // 'telemetry' | 'diagnostics' | 'explainability' | 'spatial' | 'satellite'
  const [isInspectorOpen, setIsInspectorOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'CRITICAL' | 'WARNING' | 'WEATHER'
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [isStationDirectoryOpen, setIsStationDirectoryOpen] = useState(false);

  // Live IST Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) + ' IST');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch stations on load
  useEffect(() => {
    fetch(`${API_BASE}/api/stations`)
      .then((res) => res.json())
      .then((data) => {
        setStations(data);
        if (data.length > 0) {
          const delhi = data.find((s) => s.station_name.includes('SAFDARJUNG')) || data[0];
          handleSelectStation(delhi);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load stations:', err);
        setLoading(false);
      });
  }, []);

  const handleSelectStation = async (station) => {
    setSelectedStation(station);

    try {
      // Parallelize station details, telemetry history, and spaceborne satellite cross-check
      const [detailRes, telRes, satRes] = await Promise.all([
        fetch(`${API_BASE}/api/stations/${station.station_id}`),
        fetch(`${API_BASE}/api/stations/${station.station_id}/telemetry?limit=48`),
        fetch(`${API_BASE}/api/stations/${station.station_id}/satellite`).catch((err) => {
          console.error('Error fetching satellite cross-check:', err);
          return null;
        }),
      ]);

      const detailData = await detailRes.json();
      const telData = await telRes.json();
      const satJson = satRes && satRes.ok ? await satRes.json() : null;

      setNearestNeighbors(detailData.nearest_neighbors || []);
      setTelemetry(telData || []);
      if (satJson) {
        setSatelliteData(satJson);
      }

      // Evaluate latest reading in pipeline
      if (telData && telData.length > 0) {
        const lastReading = telData[telData.length - 1];
        const evalRes = await fetch(`${API_BASE}/api/pipeline/evaluate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            station_id: station.station_id,
            station_name: station.station_name,
            latitude: station.latitude,
            longitude: station.longitude,
            timestamp: lastReading.timestamp,
            temperature: lastReading.temperature,
            pressure: lastReading.pressure,
            humidity: lastReading.humidity,
          }),
        });
        const evalData = await evalRes.json();
        setLatestResult(evalData);
        if (evalData?.satellite_cross_check) {
          setSatelliteData(evalData.satellite_cross_check);
        }

        // Dynamically sync status on map pin
        const newStatus = evalData.final_anomaly
          ? 'CRITICAL'
          : evalData.final_status === 'SUSPECT'
          ? 'WARNING'
          : evalData.anomaly_category === 'GENUINE_WEATHER_EVENT'
          ? 'WEATHER'
          : 'NORMAL';

        setStations((prev) =>
          prev.map((s) =>
            s.station_id === station.station_id ? { ...s, status: newStatus } : s
          )
        );
      }
    } catch (err) {
      console.error('Error fetching station data:', err);
    }
  };

  // On-the-fly anomaly injection
  const handleInjectAnomaly = async (anomalyType, magnitude) => {
    if (!selectedStation || telemetry.length === 0) return;
    const lastReading = telemetry[telemetry.length - 1];

    try {
      const res = await fetch(`${API_BASE}/api/simulate/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_id: selectedStation.station_id,
          station_name: selectedStation.station_name,
          latitude: selectedStation.latitude,
          longitude: selectedStation.longitude,
          timestamp: lastReading.timestamp,
          base_temperature: lastReading.temperature ?? 30.0,
          base_pressure: lastReading.pressure ?? 1010.0,
          base_humidity: lastReading.humidity ?? 60.0,
          anomaly_type: anomalyType,
          magnitude: magnitude,
        }),
      });
      const diagResult = await res.json();
      setLatestResult(diagResult);
      if (diagResult?.satellite_cross_check) {
        setSatelliteData(diagResult.satellite_cross_check);
      }
      if (diagResult?.nearest_neighbors) {
        setNearestNeighbors(diagResult.nearest_neighbors);
      }

      // Update telemetry array so all HUDs and charts immediately reflect the injected reading
      if (diagResult?.raw_reading) {
        setTelemetry((prev) => {
          if (!prev || prev.length === 0) return prev;
          const copy = [...prev];
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            temperature: diagResult.raw_reading.temperature,
            pressure: diagResult.raw_reading.pressure,
            humidity: diagResult.raw_reading.humidity,
            battery_voltage: diagResult.raw_reading.battery_voltage ?? copy[copy.length - 1].battery_voltage,
          };
          return copy;
        });
      }

      // Dynamically reflect anomaly on map pin
      const newStatus = diagResult.final_anomaly ? 'CRITICAL' : 'WARNING';
      setStations((prev) =>
        prev.map((s) =>
          s.station_id === selectedStation.station_id
            ? { ...s, status: newStatus }
            : s
        )
      );
    } catch (err) {
      console.error('Error injecting anomaly:', err);
    }
  };

  // Custom user anomaly injection with direct numerical values & offsets
  const handleInjectCustomAnomaly = async (customConfig) => {
    if (!selectedStation || telemetry.length === 0) return;
    const lastReading = telemetry[telemetry.length - 1];

    try {
      const res = await fetch(`${API_BASE}/api/simulate/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_id: selectedStation.station_id,
          station_name: selectedStation.station_name,
          latitude: selectedStation.latitude,
          longitude: selectedStation.longitude,
          timestamp: lastReading.timestamp,
          base_temperature: lastReading.temperature ?? 30.0,
          base_pressure: lastReading.pressure ?? 1010.0,
          base_humidity: lastReading.humidity ?? 60.0,
          base_battery: lastReading.battery_voltage ?? 12.6,
          ...customConfig,
        }),
      });
      const diagResult = await res.json();
      setLatestResult(diagResult);
      if (diagResult?.satellite_cross_check) {
        setSatelliteData(diagResult.satellite_cross_check);
      }
      if (diagResult?.nearest_neighbors) {
        setNearestNeighbors(diagResult.nearest_neighbors);
      }

      if (diagResult?.raw_reading) {
        setTelemetry((prev) => {
          if (!prev || prev.length === 0) return prev;
          const copy = [...prev];
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            temperature: diagResult.raw_reading.temperature,
            pressure: diagResult.raw_reading.pressure,
            humidity: diagResult.raw_reading.humidity,
            battery_voltage: diagResult.raw_reading.battery_voltage ?? copy[copy.length - 1].battery_voltage,
          };
          return copy;
        });
      }

      const newStatus = diagResult.final_anomaly ? 'CRITICAL' : 'WARNING';
      setStations((prev) =>
        prev.map((s) =>
          s.station_id === selectedStation.station_id
            ? { ...s, status: newStatus }
            : s
        )
      );
    } catch (err) {
      console.error('Error injecting custom anomaly:', err);
    }
  };

  // Restore nominal telemetry and reset pipeline state
  const handleRestoreNominal = async () => {
    if (selectedStation) {
      try {
        await fetch(`${API_BASE}/api/stations/${selectedStation.station_id}/reset`, { method: 'POST' });
      } catch (err) {
        console.error('Error resetting station pipeline:', err);
      }
      handleSelectStation(selectedStation);
      setStations((prev) =>
        prev.map((s) =>
          s.station_id === selectedStation.station_id ? { ...s, status: 'NORMAL' } : s
        )
      );
    }
  };

  // Compute status counts for filter buttons
  const counts = useMemo(() => {
    let anomalies = 0;
    let suspect = 0;
    let weather = 0;
    stations.forEach((s) => {
      if (s.status === 'CRITICAL') anomalies++;
      else if (s.status === 'WARNING') suspect++;
      else if (s.status === 'WEATHER') weather++;
    });
    return {
      all: stations.length,
      anomalies,
      suspect,
      weather,
    };
  }, [stations]);

  // Filter stations based on search query & status pill
  const filteredStations = useMemo(() => {
    return stations.filter((s) => {
      const matchesSearch =
        s.station_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.station_id.includes(searchQuery) ||
        (s.state && s.state.toLowerCase().includes(searchQuery.toLowerCase()));

      if (!matchesSearch) return false;
      if (statusFilter === 'ALL') return true;
      return s.status === statusFilter;
    });
  }, [stations, searchQuery, statusFilter]);

  // Matching search results for autocomplete dropdown
  const matchingSearchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase();
    return stations.filter(
      (s) =>
        s.station_name.toLowerCase().includes(q) ||
        String(s.station_id).includes(q) ||
        (s.state && s.state.toLowerCase().includes(q))
    );
  }, [stations, searchQuery]);

  // Dynamic health score computed from actual pipeline state (not a static pre-assigned value)
  const rawHealthFromBackend = latestResult?.sensor_health?.health_score_pct;
  const computedHealthScore = (() => {
    if (rawHealthFromBackend != null) return rawHealthFromBackend;
    // Build from first principles using what the pipeline actually reported
    let score = 100.0;
    const isAnom = latestResult?.final_anomaly ?? false;
    const satInconsistent = latestResult?.satellite_cross_check?.is_satellite_inconsistent ?? false;
    const tier1Pass = !isAnom;
    const tier2Score = latestResult?.tier2?.anomaly_score ?? (isAnom ? 0.7 : 0.0);
    const battV = latestResult?.raw_reading?.battery_voltage ?? selectedStation?.last_battery ?? 12.6;
    const wmoFlag = latestResult?.wmo_qc_flag ?? (isAnom ? 2 : 0);

    if (isAnom) score -= 40.0 * Math.min(1.0, tier2Score);  // anomaly penalty
    if (satInconsistent) score -= 15.0;                      // satellite divergence
    if (battV < 11.2) score -= 20.0;                         // low battery
    else if (battV < 12.0) score -= 5.0;                     // marginal battery
    if (wmoFlag === 3) score -= 10.0;                        // missing data

    return Math.max(0, Math.min(100, score));
  })();
  const healthScore = computedHealthScore;
  const isAnomaly = latestResult?.final_anomaly ?? false;

  return (
    <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', background: '#0d1117' }}>
      {/* Top Compact Command Header */}
      <header
        className="glass-panel"
        style={{
          margin: '8px 12px 0 12px',
          padding: '6px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderRadius: '6px',
          zIndex: 10,
          background: '#161b22',
          border: '1px solid #30363d',
          height: '46px',
        }}
      >
        {/* Compact Logo & Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '4px',
              background: '#1f6feb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Shield size={15} color="#ffffff" />
          </div>
          <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f0f6fc', letterSpacing: '-0.01em' }}>
            SkyGuard AI
          </span>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3fb950' }} title="National Mesonet Active" />
          <span className="badge badge-purple" style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
            INSAT-3DR
          </span>
        </div>

        {/* Center: Search, Directory & Status Filter Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Station Directory Trigger Button */}
          <button
            className="btn-ghost"
            onClick={() => setIsStationDirectoryOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              height: '28px',
              padding: '4px 10px',
              background: '#21262d',
              border: '1px solid #30363d',
              borderRadius: '6px',
              fontSize: '0.72rem',
              color: '#f0f6fc',
              fontWeight: 600,
              cursor: 'pointer',
            }}
            title="Open Directory of All 900 Indian AWS Stations"
          >
            <Layers size={13} color="#58a6ff" />
            <span>Stations ({stations.length || 900})</span>
          </button>

          {/* Search Container with Instant Autocomplete Dropdown */}
          <div style={{ position: 'relative' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '6px',
                padding: '4px 8px',
                width: '190px',
              }}
            >
              <Search size={13} color="#8b949e" />
              <input
                type="text"
                placeholder="Search 900 stations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: '#f0f6fc',
                  fontSize: '0.72rem',
                  width: '100%',
                }}
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  style={{ background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer', padding: 0 }}
                >
                  <X size={12} />
                </button>
              )}
            </div>

            {/* Instant Search Autocomplete Dropdown */}
            {searchQuery.trim() && (
              <div
                style={{
                  position: 'absolute',
                  top: '34px',
                  left: 0,
                  width: '320px',
                  maxHeight: '340px',
                  overflowY: 'auto',
                  background: '#161b22',
                  border: '1px solid #30363d',
                  borderRadius: '6px',
                  boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
                  zIndex: 2500,
                  padding: '4px',
                }}
              >
                <div
                  style={{
                    padding: '6px 8px',
                    fontSize: '0.68rem',
                    color: '#8b949e',
                    borderBottom: '1px solid #21262d',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span>MATCHING STATIONS ({matchingSearchResults.length})</span>
                  <span
                    style={{ color: '#58a6ff', cursor: 'pointer', fontWeight: 600 }}
                    onClick={() => {
                      setIsStationDirectoryOpen(true);
                    }}
                  >
                    All Directory →
                  </span>
                </div>
                {matchingSearchResults.length === 0 ? (
                  <div style={{ padding: '12px 8px', fontSize: '0.72rem', color: '#8b949e', textAlign: 'center' }}>
                    No station matches "{searchQuery}"
                  </div>
                ) : (
                  matchingSearchResults.slice(0, 10).map((st) => (
                    <div
                      key={st.station_id}
                      onClick={() => {
                        handleSelectStation(st);
                        setSearchQuery('');
                      }}
                      style={{
                        padding: '6px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '0.75rem',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = '#21262d')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      <div style={{ minWidth: 0, paddingRight: '8px' }}>
                        <div
                          style={{
                            fontWeight: 600,
                            color: '#f0f6fc',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {st.station_name}
                        </div>
                        <div style={{ fontSize: '0.68rem', color: '#8b949e' }}>
                          {st.state || 'India'} • WMO: {st.station_id}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <span
                          style={{
                            fontSize: '0.62rem',
                            fontWeight: 700,
                            color:
                              st.status === 'CRITICAL'
                                ? '#f85149'
                                : st.status === 'WARNING'
                                ? '#d29922'
                                : st.status === 'WEATHER'
                                ? '#58a6ff'
                                : '#3fb950',
                          }}
                        >
                          {st.status}
                        </span>
                        <div style={{ fontSize: '0.65rem', color: '#8b949e' }}>
                          {Math.round(st.health_score ?? 98)}%
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '3px', alignItems: 'center', background: '#0d1117', padding: '2px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <button
              className={`btn-ghost ${statusFilter === 'ALL' ? 'btn-ghost-active' : ''}`}
              onClick={() => setStatusFilter('ALL')}
              style={{ padding: '3px 8px', fontSize: '0.7rem' }}
            >
              All {counts.all}
            </button>
            <button
              className={`btn-ghost ${statusFilter === 'CRITICAL' ? 'btn-ghost-active' : ''}`}
              onClick={() => setStatusFilter('CRITICAL')}
              style={{ padding: '3px 8px', fontSize: '0.7rem', color: statusFilter === 'CRITICAL' ? '#ffffff' : '#f85149' }}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f85149' }} />
              {counts.anomalies} Anom
            </button>
            <button
              className={`btn-ghost ${statusFilter === 'WARNING' ? 'btn-ghost-active' : ''}`}
              onClick={() => setStatusFilter('WARNING')}
              style={{ padding: '3px 8px', fontSize: '0.7rem', color: statusFilter === 'WARNING' ? '#ffffff' : '#d29922' }}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#d29922' }} />
              {counts.suspect} Susp
            </button>
            <button
              className={`btn-ghost ${statusFilter === 'WEATHER' ? 'btn-ghost-active' : ''}`}
              onClick={() => setStatusFilter('WEATHER')}
              style={{ padding: '3px 8px', fontSize: '0.7rem', color: statusFilter === 'WEATHER' ? '#ffffff' : '#58a6ff' }}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#58a6ff' }} />
              {counts.weather} Storm
            </button>
          </div>

          <button
            className="btn-primary"
            onClick={() => setIsCustomModalOpen(true)}
            style={{
              fontSize: '0.7rem',
              padding: '4px 10px',
              height: '28px',
            }}
            title="Create & Inject Custom Anomaly"
          >
            <Sliders size={12} />
            + Anomaly
          </button>
        </div>

        {/* Right: Live IST Clock & Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 600, color: '#8b949e' }}>
            {timeStr}
          </span>

          <button
            className="btn-ghost"
            onClick={() => setIsInspectorOpen(!isInspectorOpen)}
            style={{ padding: '4px 8px', fontSize: '0.7rem', height: '28px' }}
            title="Toggle Inspector Drawer"
          >
            {isInspectorOpen ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main
        style={{
          flex: 1,
          padding: '10px 12px 12px 12px',
          display: 'grid',
          gridTemplateColumns: isInspectorOpen ? '1fr 520px' : '1fr',
          gap: '10px',
          overflow: 'hidden',
        }}
      >
        {/* Left Hero: Large GIS Mesonet Map */}
        <div
          className="glass-panel"
          style={{
            position: 'relative',
            height: '100%',
            overflow: 'hidden',
            borderRadius: '6px',
            display: 'flex',
            flexDirection: 'column',
            background: '#0d1117',
            border: '1px solid #30363d',
          }}
        >
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#8b949e' }}>
              Loading India National Mesonet GIS Stations...
            </div>
          ) : (
            <GisMap
              stations={filteredStations}
              selectedStation={selectedStation}
              nearestNeighbors={nearestNeighbors}
              onSelectStation={handleSelectStation}
            />
          )}

          {/* Clean Floating Anomaly Sandbox Dock (Bottom Left) */}
          <div
            style={{
              position: 'absolute',
              bottom: '14px',
              left: '14px',
              zIndex: 1000,
            }}
          >
            <AnomalySandbox
              onInject={handleInjectAnomaly}
              onRestore={handleRestoreNominal}
              onOpenCustom={() => setIsCustomModalOpen(true)}
              isSimulating={false}
            />
          </div>
        </div>

        {/* Right Panel: Clean Tabbed Diagnostic Inspector */}
        {isInspectorOpen && (
          <aside
            className="glass-panel"
            style={{
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              borderRadius: '6px',
              overflow: 'hidden',
              background: '#161b22',
              border: '1px solid #30363d',
            }}
          >
            {/* Inspector Header: Selected Station Card */}
            {selectedStation && (
              <div
                style={{
                  padding: '10px 14px',
                  borderBottom: '1px solid #30363d',
                  background: '#161b22',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#f0f6fc' }}>
                      {selectedStation.station_name}
                    </h2>
                    <span className={`badge ${isAnomaly ? 'badge-fail' : (selectedStation.status === 'WEATHER' ? 'badge-weather' : 'badge-pass')}`}>
                      {latestResult?.final_status ?? selectedStation.status ?? 'NOMINAL'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#8b949e', marginTop: '1px' }}>
                    ID: <span style={{ fontFamily: 'var(--font-mono)', color: '#58a6ff' }}>{selectedStation.station_id}</span> • Elev: {selectedStation.elevation_m}m • {(!selectedStation.state || selectedStation.state === 'nan') ? 'National Mesonet' : selectedStation.state}
                  </div>
                </div>

                {/* Sensor Health Mini-Dial — dynamically computed from pipeline */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', textAlign: 'right' }}>
                  <div title={[
                    `Live Health Score — computed from actual sensor diagnostics:`,
                    `• Base score: 100%`,
                    latestResult?.final_anomaly ? `• Anomaly detected: −${Math.round(40 * Math.min(1, latestResult?.tier2?.anomaly_score ?? 0.7))}%` : `• No anomaly detected: 0%`,
                    latestResult?.satellite_cross_check?.is_satellite_inconsistent ? `• Satellite divergence: −15%` : `• Satellite verified: 0%`,
                    (latestResult?.raw_reading?.battery_voltage ?? 12.6) < 11.2 ? `• Low battery: −20%` : `• Battery OK: 0%`,
                    `• Final: ${healthScore.toFixed(0)}%`,
                  ].join('\n')} style={{ cursor: 'help' }}>
                    <div style={{ fontSize: '0.62rem', color: '#8b949e', fontWeight: 600 }}>HEALTH</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: healthScore > 95 ? '#3fb950' : (healthScore > 75 ? '#d29922' : '#f85149'), fontFamily: 'var(--font-mono)' }}>
                      {healthScore.toFixed(0)}%
                    </div>
                    <div style={{ fontSize: '0.55rem', color: healthScore > 95 ? '#3fb950' : '#d29922', fontWeight: 600 }}>
                      {healthScore >= 100 ? '✓ ALL CLEAR' : healthScore > 90 ? 'GOOD' : healthScore > 75 ? 'DEGRADED' : 'FAULT'}
                    </div>
                  </div>
                  {healthScore > 90 ? (
                    <ShieldCheck size={20} color="#3fb950" />
                  ) : (
                    <ShieldAlert size={20} color={healthScore > 60 ? '#d29922' : '#f85149'} />
                  )}
                </div>

              </div>
            )}

            {/* Clean Tab Selector Bar */}
            <div
              style={{
                display: 'flex',
                borderBottom: '1px solid #30363d',
                background: '#0d1117',
                overflowX: 'auto',
              }}
            >
              <button
                className={`tab-btn ${activeTab === 'telemetry' ? 'active' : ''}`}
                onClick={() => setActiveTab('telemetry')}
              >
                <ChartIcon size={14} />
                Telemetry
              </button>

              <button
                className={`tab-btn ${activeTab === 'diagnostics' ? 'active' : ''}`}
                onClick={() => setActiveTab('diagnostics')}
              >
                <Cpu size={14} />
                Diagnostics
              </button>

              <button
                className={`tab-btn ${activeTab === 'satellite' ? 'active' : ''}`}
                onClick={() => setActiveTab('satellite')}
              >
                <Satellite size={14} />
                Satellite Cross-Check
              </button>

              <button
                className={`tab-btn ${activeTab === 'explainability' ? 'active' : ''}`}
                onClick={() => setActiveTab('explainability')}
              >
                <Sparkles size={14} />
                TreeSHAP &amp; RCA
              </button>

              <button
                className={`tab-btn ${activeTab === 'spatial' ? 'active' : ''}`}
                onClick={() => setActiveTab('spatial')}
              >
                <Compass size={14} />
                Mesonet Peers
              </button>
            </div>

            {/* Active Tab Body */}
            <div style={{ flex: 1, padding: '12px', overflowY: 'auto' }}>
              {activeTab === 'telemetry' && (
                <TelemetryHUD
                  station={selectedStation}
                  telemetry={telemetry}
                  latestResult={latestResult}
                  showCorrected={showCorrected}
                  setShowCorrected={setShowCorrected}
                />
              )}

              {activeTab === 'diagnostics' && (
                <DiagnosticTrace latestResult={latestResult} />
              )}

              {activeTab === 'satellite' && (
                <SatelliteView
                  station={selectedStation}
                  satelliteData={satelliteData}
                  telemetry={telemetry}
                  latestResult={latestResult}
                />
              )}

              {activeTab === 'explainability' && (
                <ShapPanel latestResult={latestResult} />
              )}

              {activeTab === 'spatial' && (
                <SpatialNeighbors
                  station={selectedStation}
                  nearestNeighbors={nearestNeighbors}
                  spatialConsensus={latestResult?.spatial_consensus}
                  latestResult={latestResult}
                  onSelectStation={(peer) => {
                    const fullStation = stations.find((s) => s.station_id === peer.station_id);
                    if (fullStation) handleSelectStation(fullStation);
                  }}
                />
              )}
            </div>
          </aside>
        )}
      </main>

      {/* Custom User Anomaly Injector Modal */}
      <CustomAnomalyModal
        isOpen={isCustomModalOpen}
        onClose={() => setIsCustomModalOpen(false)}
        onInjectCustom={handleInjectCustomAnomaly}
        selectedStation={selectedStation}
        latestResult={latestResult}
      />

      {/* Complete 543 Indian AWS Observatories Directory Modal */}
      <StationDirectoryModal
        isOpen={isStationDirectoryOpen}
        onClose={() => setIsStationDirectoryOpen(false)}
        stations={stations}
        selectedStation={selectedStation}
        onSelectStation={handleSelectStation}
      />
    </div>
  );
}
