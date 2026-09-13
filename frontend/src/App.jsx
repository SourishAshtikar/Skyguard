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
} from 'lucide-react';

import GisMap from './components/GisMap';
import TelemetryHUD from './components/TelemetryHUD';
import DiagnosticTrace from './components/DiagnosticTrace';
import ShapPanel from './components/ShapPanel';
import SpatialNeighbors from './components/SpatialNeighbors';
import AnomalySandbox from './components/AnomalySandbox';
import CustomAnomalyModal from './components/CustomAnomalyModal';
import { Sliders } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [nearestNeighbors, setNearestNeighbors] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [latestResult, setLatestResult] = useState(null);
  const [showCorrected, setShowCorrected] = useState(true);
  const [loading, setLoading] = useState(true);
  const [timeStr, setTimeStr] = useState('');

  // UI State: Active Inspector Tab & Drawer Collapse
  const [activeTab, setActiveTab] = useState('telemetry'); // 'telemetry' | 'diagnostics' | 'explainability' | 'spatial'
  const [isInspectorOpen, setIsInspectorOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'CRITICAL' | 'WARNING' | 'NORMAL'
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);

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
      // 1. Fetch nearest neighbors
      const detailRes = await fetch(`${API_BASE}/api/stations/${station.station_id}`);
      const detailData = await detailRes.json();
      setNearestNeighbors(detailData.nearest_neighbors || []);

      // 2. Fetch recent telemetry
      const telRes = await fetch(`${API_BASE}/api/stations/${station.station_id}/telemetry?limit=48`);
      const telData = await telRes.json();
      setTelemetry(telData);

      // 3. Evaluate latest reading in pipeline
      if (telData.length > 0) {
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

      // Dynamically reflect anomaly on map pin
      setStations((prev) =>
        prev.map((s) =>
          s.station_id === selectedStation.station_id
            ? { ...s, status: diagResult.final_status === 'FAIL' ? 'CRITICAL' : 'WARNING' }
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

      setStations((prev) =>
        prev.map((s) =>
          s.station_id === selectedStation.station_id
            ? { ...s, status: diagResult.final_status === 'FAIL' ? 'CRITICAL' : 'WARNING' }
            : s
        )
      );
    } catch (err) {
      console.error('Error injecting custom anomaly:', err);
    }
  };

  // Restore nominal telemetry
  const handleRestoreNominal = () => {
    if (selectedStation) {
      handleSelectStation(selectedStation);
      setStations((prev) =>
        prev.map((s) =>
          s.station_id === selectedStation.station_id ? { ...s, status: 'NORMAL' } : s
        )
      );
    }
  };

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

  const healthScore = latestResult?.sensor_health?.score_pct ?? 98.2;
  const isAnomaly = latestResult?.final_anomaly ?? false;

  return (
    <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', background: 'var(--bg-main)' }}>
      {/* Top National Command Bar */}
      <header
        className="glass-panel"
        style={{
          margin: '10px 14px 0 14px',
          padding: '10px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderRadius: '10px',
          zIndex: 10,
        }}
      >
        {/* Brand & National Mesonet Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 14px rgba(56, 189, 248, 0.4)',
            }}
          >
            <Shield size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
                SkyGuard AI
              </span>
              <span className="badge badge-pass" style={{ fontSize: '0.65rem' }}>
                National Mesonet Active
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
              Intelligent 3-Tier Anomaly Detection &amp; Self-Healing AWS Network
            </div>
          </div>
        </div>

        {/* Station Search & Filter Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: '#0a101f',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '5px 10px',
              width: '260px',
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder="Search 545 AWS stations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#f8fafc',
                fontSize: '0.75rem',
                width: '100%',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <button
              className={`filter-pill ${statusFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setStatusFilter('ALL')}
            >
              All ({stations.length})
            </button>
            <button
              className={`filter-pill ${statusFilter === 'CRITICAL' ? 'active' : ''}`}
              onClick={() => setStatusFilter('CRITICAL')}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ff3366' }} />
              Anomalies
            </button>
            <button
              className={`filter-pill ${statusFilter === 'WARNING' ? 'active' : ''}`}
              onClick={() => setStatusFilter('WARNING')}
            >
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ffb800' }} />
              Suspect
            </button>

            <button
              className="btn-secondary"
              onClick={() => setIsCustomModalOpen(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '0.75rem',
                padding: '5px 12px',
                color: '#00f0ff',
                borderColor: 'rgba(0, 240, 255, 0.4)',
                background: 'rgba(0, 240, 255, 0.08)',
                fontWeight: 600,
                marginLeft: '4px',
              }}
              title="Create & Inject Custom Anomaly with Exact Numbers"
            >
              <Sliders size={13} color="#00f0ff" />
              + Custom Anomaly
            </button>
          </div>
        </div>

        {/* Live IST Clock & Inspector Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8' }}>
              {timeStr}
            </div>
            <div style={{ fontSize: '0.65rem', color: '#64748b' }}>UTC +05:30 (India)</div>
          </div>

          <button
            className="btn-secondary"
            onClick={() => setIsInspectorOpen(!isInspectorOpen)}
            style={{ padding: '6px 10px', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
            title="Toggle Inspector Drawer"
          >
            {isInspectorOpen ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            <span>{isInspectorOpen ? 'Expand Map' : 'Show Inspector'}</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main
        style={{
          flex: 1,
          padding: '10px 14px 14px 14px',
          display: 'grid',
          gridTemplateColumns: isInspectorOpen ? '1fr 480px' : '1fr',
          gap: '12px',
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
            borderRadius: '10px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
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

          {/* Sleek Floating Anomaly Sandbox Dock (Bottom Left) */}
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              left: '16px',
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
              borderRadius: '10px',
              overflow: 'hidden',
            }}
          >
            {/* Inspector Header: Selected Station Card */}
            {selectedStation && (
              <div
                style={{
                  padding: '12px 16px',
                  borderBottom: '1px solid var(--border-subtle)',
                  background: 'rgba(10, 16, 30, 0.6)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                      {selectedStation.station_name}
                    </h2>
                    <span className={`badge ${isAnomaly ? 'badge-fail' : 'badge-pass'}`}>
                      {latestResult?.final_status ?? 'NOMINAL'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.725rem', color: '#94a3b8', marginTop: '1px' }}>
                    ID: <span style={{ fontFamily: 'var(--font-mono)', color: '#00f0ff' }}>{selectedStation.station_id}</span> • Elev: {selectedStation.elevation_m}m • {(!selectedStation.state || selectedStation.state === 'nan') ? 'National Mesonet' : selectedStation.state}
                  </div>
                </div>

                {/* Sensor Health Mini-Dial */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', textAlign: 'right' }}>
                  <div>
                    <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>HEALTH</div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 800, color: healthScore > 80 ? '#22c55e' : (healthScore > 50 ? '#f59e0b' : '#f43f5e') }}>
                      {healthScore}%
                    </div>
                  </div>
                  {healthScore > 80 ? (
                    <ShieldCheck size={22} color="#22c55e" />
                  ) : (
                    <ShieldAlert size={22} color={healthScore > 50 ? '#f59e0b' : '#f43f5e'} />
                  )}
                </div>
              </div>
            )}

            {/* Clean Tab Selector Bar */}
            <div
              style={{
                display: 'flex',
                borderBottom: '1px solid var(--border-subtle)',
                background: 'rgba(10, 16, 30, 0.4)',
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

            {/* Active Tab Body (Scrollable, Clean & Uncluttered) */}
            <div style={{ flex: 1, padding: '14px', overflowY: 'auto' }}>
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

              {activeTab === 'explainability' && (
                <ShapPanel latestResult={latestResult} />
              )}

              {activeTab === 'spatial' && (
                <SpatialNeighbors
                  station={selectedStation}
                  nearestNeighbors={nearestNeighbors}
                  spatialConsensus={latestResult?.spatial_consensus}
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
    </div>
  );
}
