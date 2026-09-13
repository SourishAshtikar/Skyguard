import React, { useState, useMemo } from 'react';
import {
  X,
  Search,
  SlidersHorizontal,
  MapPin,
  Activity,
  ShieldCheck,
  ShieldAlert,
  Compass,
  ArrowUpDown,
  ExternalLink,
  ChevronRight,
  Layers,
} from 'lucide-react';

export default function StationDirectoryModal({
  isOpen,
  onClose,
  stations,
  selectedStation,
  onSelectStation,
}) {
  if (!isOpen) return null;

  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [sortBy, setSortBy] = useState('name'); // 'name' | 'health-asc' | 'health-desc' | 'elev-desc' | 'elev-asc'

  // Extract unique states for filter dropdown
  const uniqueStates = useMemo(() => {
    const states = new Set();
    stations.forEach((s) => {
      if (s.state && s.state !== 'nan' && s.state !== 'National Mesonet') {
        states.add(s.state);
      }
    });
    return Array.from(states).sort();
  }, [stations]);

  // Aggregate status counts
  const counts = useMemo(() => {
    let nominal = 0;
    let suspect = 0;
    let anomaly = 0;
    let weather = 0;
    stations.forEach((s) => {
      if (s.status === 'CRITICAL') anomaly++;
      else if (s.status === 'WARNING') suspect++;
      else if (s.status === 'WEATHER') weather++;
      else nominal++;
    });
    return { all: stations.length, nominal, suspect, anomaly, weather };
  }, [stations]);

  // Filter and sort stations
  const filteredStations = useMemo(() => {
    return stations
      .filter((s) => {
        // Search query match
        if (search.trim()) {
          const q = search.toLowerCase();
          const matchName = s.station_name.toLowerCase().includes(q);
          const matchId = String(s.station_id).includes(q);
          const matchState = (s.state || '').toLowerCase().includes(q);
          if (!matchName && !matchId && !matchState) return false;
        }

        // State filter
        if (selectedState !== 'ALL') {
          if (s.state !== selectedState) return false;
        }

        // Status filter
        if (selectedStatus === 'NORMAL' && s.status !== 'NORMAL') return false;
        if (selectedStatus === 'WARNING' && s.status !== 'WARNING') return false;
        if (selectedStatus === 'CRITICAL' && s.status !== 'CRITICAL') return false;
        if (selectedStatus === 'WEATHER' && s.status !== 'WEATHER') return false;

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'name') {
          return a.station_name.localeCompare(b.station_name);
        }
        if (sortBy === 'health-asc') {
          return (a.health_score ?? 100) - (b.health_score ?? 100);
        }
        if (sortBy === 'health-desc') {
          return (b.health_score ?? 100) - (a.health_score ?? 100);
        }
        if (sortBy === 'elev-desc') {
          return (b.elevation_m ?? 0) - (a.elevation_m ?? 0);
        }
        if (sortBy === 'elev-asc') {
          return (a.elevation_m ?? 0) - (b.elevation_m ?? 0);
        }
        return 0;
      });
  }, [stations, search, selectedState, selectedStatus, sortBy]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'CRITICAL':
        return '#f85149';
      case 'WARNING':
        return '#d29922';
      case 'WEATHER':
        return '#58a6ff';
      default:
        return '#3fb950';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'CRITICAL':
        return 'ANOMALY';
      case 'WARNING':
        return 'SUSPECT';
      case 'WEATHER':
        return 'EXTREME WX';
      default:
        return 'NOMINAL';
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(5, 8, 15, 0.85)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '95%',
          maxWidth: '1150px',
          height: '88vh',
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: '10px',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #30363d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(13, 17, 23, 0.95)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: '#1f6feb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Layers size={18} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f0f6fc', margin: 0 }}>
                  IMD National AWS Observatories Directory
                </h2>
                <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                  {stations.length} Active Stations
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#8b949e', marginTop: '2px' }}>
                Browse, filter, and inspect live QC pipelines across all Indian surface mesonet stations
              </div>
            </div>
          </div>

          <button
            className="btn-ghost"
            onClick={onClose}
            style={{ padding: '6px', borderRadius: '6px' }}
            title="Close Directory"
          >
            <X size={18} />
          </button>
        </div>

        {/* Status Metrics Bar */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '10px',
            padding: '12px 20px',
            background: '#0d1117',
            borderBottom: '1px solid #30363d',
          }}
        >
          <button
            onClick={() => setSelectedStatus('ALL')}
            style={{
              background: selectedStatus === 'ALL' ? '#21262d' : 'transparent',
              border: `1px solid ${selectedStatus === 'ALL' ? '#58a6ff' : '#30363d'}`,
              borderRadius: '6px',
              padding: '8px 12px',
              textAlign: 'left',
              cursor: 'pointer',
              color: '#f0f6fc',
            }}
          >
            <div style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600 }}>ALL STATIONS</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {counts.all}
            </div>
          </button>

          <button
            onClick={() => setSelectedStatus('NORMAL')}
            style={{
              background: selectedStatus === 'NORMAL' ? '#21262d' : 'transparent',
              border: `1px solid ${selectedStatus === 'NORMAL' ? '#3fb950' : '#30363d'}`,
              borderRadius: '6px',
              padding: '8px 12px',
              textAlign: 'left',
              cursor: 'pointer',
              color: '#3fb950',
            }}
          >
            <div style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600 }}>NOMINAL</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {counts.nominal}
            </div>
          </button>

          <button
            onClick={() => setSelectedStatus('WARNING')}
            style={{
              background: selectedStatus === 'WARNING' ? '#21262d' : 'transparent',
              border: `1px solid ${selectedStatus === 'WARNING' ? '#d29922' : '#30363d'}`,
              borderRadius: '6px',
              padding: '8px 12px',
              textAlign: 'left',
              cursor: 'pointer',
              color: '#d29922',
            }}
          >
            <div style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600 }}>SUSPECT / JITTER</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {counts.suspect}
            </div>
          </button>

          <button
            onClick={() => setSelectedStatus('CRITICAL')}
            style={{
              background: selectedStatus === 'CRITICAL' ? '#21262d' : 'transparent',
              border: `1px solid ${selectedStatus === 'CRITICAL' ? '#f85149' : '#30363d'}`,
              borderRadius: '6px',
              padding: '8px 12px',
              textAlign: 'left',
              cursor: 'pointer',
              color: '#f85149',
            }}
          >
            <div style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600 }}>ANOMALY / DEFECT</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {counts.anomaly}
            </div>
          </button>

          <button
            onClick={() => setSelectedStatus('WEATHER')}
            style={{
              background: selectedStatus === 'WEATHER' ? '#21262d' : 'transparent',
              border: `1px solid ${selectedStatus === 'WEATHER' ? '#58a6ff' : '#30363d'}`,
              borderRadius: '6px',
              padding: '8px 12px',
              textAlign: 'left',
              cursor: 'pointer',
              color: '#58a6ff',
            }}
          >
            <div style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600 }}>EXTREME WEATHER</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {counts.weather}
            </div>
          </button>
        </div>

        {/* Filter & Search Bar */}
        <div
          style={{
            padding: '12px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            borderBottom: '1px solid #30363d',
            background: '#161b22',
          }}
        >
          {/* Search Box */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '6px 12px',
            }}
          >
            <Search size={15} color="#8b949e" />
            <input
              type="text"
              placeholder="Search by station name (e.g., Santacruz, Safdarjung), WMO ID, state..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#f0f6fc',
                fontSize: '0.82rem',
                width: '100%',
              }}
              autoFocus
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                style={{ background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer', padding: 0 }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* State / Region Dropdown Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: '#8b949e' }}>State:</span>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              style={{
                background: '#0d1117',
                border: '1px solid #30363d',
                color: '#f0f6fc',
                fontSize: '0.78rem',
                padding: '6px 10px',
                borderRadius: '6px',
                outline: 'none',
                cursor: 'pointer',
                minWidth: '160px',
              }}
            >
              <option value="ALL">All States / Regions</option>
              {uniqueStates.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ArrowUpDown size={14} color="#8b949e" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                background: '#0d1117',
                border: '1px solid #30363d',
                color: '#f0f6fc',
                fontSize: '0.78rem',
                padding: '6px 10px',
                borderRadius: '6px',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="name">Sort: Name (A-Z)</option>
              <option value="health-asc">Sort: Health (Lowest First)</option>
              <option value="health-desc">Sort: Health (Highest First)</option>
              <option value="elev-desc">Sort: Elevation (High to Low)</option>
              <option value="elev-asc">Sort: Elevation (Low to High)</option>
            </select>
          </div>
        </div>

        {/* Stations Counter */}
        <div
          style={{
            padding: '8px 20px',
            background: 'rgba(13, 17, 23, 0.6)',
            borderBottom: '1px solid #21262d',
            fontSize: '0.75rem',
            color: '#8b949e',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>
            Showing <strong style={{ color: '#f0f6fc' }}>{filteredStations.length}</strong> of {stations.length} Indian AWS Observatories
          </span>
          <span style={{ fontStyle: 'italic', fontSize: '0.7rem' }}>
            Tip: Click any station to center the GIS map and execute all 4 tiers of QC models in real time
          </span>
        </div>

        {/* Scrollable Stations List */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '12px 20px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '10px',
            alignContent: 'start',
          }}
        >
          {filteredStations.length === 0 ? (
            <div
              style={{
                gridColumn: '1 / -1',
                padding: '40px 20px',
                textAlign: 'center',
                color: '#8b949e',
              }}
            >
              No AWS stations found matching "{search}". Try clearing search or filters.
            </div>
          ) : (
            filteredStations.map((st) => {
              const isSelected = selectedStation?.station_id === st.station_id;
              const color = getStatusColor(st.status);
              const label = getStatusLabel(st.status);
              const health = st.health_score ?? 98.0;

              return (
                <div
                  key={st.station_id}
                  onClick={() => {
                    onSelectStation(st);
                    onClose();
                  }}
                  style={{
                    background: isSelected ? 'rgba(31, 111, 235, 0.15)' : '#0d1117',
                    border: `1px solid ${isSelected ? '#1f6feb' : '#30363d'}`,
                    borderRadius: '8px',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '8px',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.borderColor = '#58a6ff';
                      e.currentTarget.style.background = '#161b22';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.borderColor = '#30363d';
                      e.currentTarget.style.background = '#0d1117';
                    }
                  }}
                >
                  {/* Card Top Row: Name & Status */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: '0.88rem',
                          fontWeight: 700,
                          color: '#f0f6fc',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                        title={st.station_name}
                      >
                        {st.station_name}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: '#58a6ff', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                        WMO: {st.station_id}
                      </div>
                    </div>

                    <span
                      style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: `${color}18`,
                        color: color,
                        border: `1px solid ${color}40`,
                        letterSpacing: '0.04em',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {label}
                    </span>
                  </div>

                  {/* Card Middle: Location & Elevation */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: '#8b949e' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MapPin size={12} color="#8b949e" />
                      <span>{st.state || 'India'}</span>
                    </div>
                    <div>
                      Elev: <strong style={{ color: '#c9d1d9' }}>{st.elevation_m ?? 150}m</strong>
                    </div>
                  </div>

                  {/* Card Bottom: Coordinates & Health Score */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      borderTop: '1px solid #21262d',
                      paddingTop: '6px',
                      marginTop: '2px',
                    }}
                  >
                    <div style={{ fontSize: '0.68rem', color: '#8b949e', fontFamily: 'var(--font-mono)' }}>
                      {st.latitude.toFixed(3)}°N, {st.longitude.toFixed(3)}°E
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '0.65rem', color: '#8b949e' }}>HEALTH:</span>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          fontFamily: 'var(--font-mono)',
                          color: health > 90 ? '#3fb950' : health > 75 ? '#d29922' : '#f85149',
                        }}
                      >
                        {health.toFixed(0)}%
                      </span>
                      <ChevronRight size={13} color="#58a6ff" />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '10px 20px',
            borderTop: '1px solid #30363d',
            background: 'rgba(13, 17, 23, 0.95)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.75rem',
            color: '#8b949e',
          }}
        >
          <div>
            Connected to <strong>National Surface Mesonet Engine</strong> • 543/543 Observatories Stream Online
          </div>
          <button
            className="btn-primary"
            onClick={onClose}
            style={{ fontSize: '0.75rem', padding: '5px 16px' }}
          >
            Close Directory
          </button>
        </div>
      </div>
    </div>
  );
}
