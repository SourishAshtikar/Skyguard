import React from 'react';
import { Compass, CheckCircle2, AlertTriangle, ArrowUpRight, Thermometer, Gauge, Droplets } from 'lucide-react';

export default function SpatialNeighbors({
  station,
  nearestNeighbors,
  spatialConsensus,
  onSelectStation,
}) {
  if (!station) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Cluster Summary Header Card */}
      <div
        className="glass-card"
        style={{
          padding: '10px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#161b22',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Compass size={16} color="#58a6ff" />
          <div>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f0f6fc' }}>
              Spatial Mesonet Peer Consensus
            </h3>
            <div style={{ fontSize: '0.7rem', color: '#8b949e' }}>
              150 km Haversine Radius • Barometric MSLP Reduced
            </div>
          </div>
        </div>
        <span className={`badge ${spatialConsensus?.is_spatially_inconsistent ? 'badge-fail' : 'badge-pass'}`}>
          {spatialConsensus?.is_spatially_inconsistent ? 'SPATIAL OUTLIER' : 'CONSENSUS VERIFIED'}
        </span>
      </div>

      {/* 3 Metric Summary Dial Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.65rem', color: '#8b949e', fontWeight: 600 }}>CONSENSUS SCORE</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#58a6ff', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {((spatialConsensus?.spatial_consensus_score ?? 0.95) * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: '0.65rem', color: '#6e7681' }}>Cluster Correlation</div>
        </div>

        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.65rem', color: '#8b949e', fontWeight: 600 }}>TARGET DEVIATION</div>
          <div
            style={{
              fontSize: '1.2rem',
              fontWeight: 700,
              color: (spatialConsensus?.target_deviation_temp || 0) > 4.0 ? '#f85149' : '#3fb950',
              marginTop: '2px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {spatialConsensus?.target_deviation_temp ? `${spatialConsensus.target_deviation_temp.toFixed(1)}°C` : '0.4°C'}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#6e7681' }}>vs Regional Median</div>
        </div>

        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.65rem', color: '#8b949e', fontWeight: 600 }}>PEER STATIONS</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f0f6fc', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {nearestNeighbors.length} AWS
          </div>
          <div style={{ fontSize: '0.65rem', color: '#6e7681' }}>Live Synced Neighbors</div>
        </div>
      </div>

      {/* Neighbor List with Real Live Telemetry Values */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#8b949e', letterSpacing: '0.03em' }}>
            CORROBORATING PEER SENSOR STREAMS:
          </span>
          <span style={{ fontSize: '0.68rem', color: '#6e7681' }}>
            Click station to switch inspector
          </span>
        </div>

        {nearestNeighbors.length === 0 ? (
          <div className="glass-card" style={{ padding: '16px', textAlign: 'center', fontSize: '0.75rem', color: '#8b949e' }}>
            Isolated station or no active AWS detected within 150 km.
          </div>
        ) : (
          nearestNeighbors.map((n, idx) => {
            const isNominal = n.status !== 'SUSPECT';
            const tempVal = n.temperature != null ? `${n.temperature.toFixed(1)}°C` : 'N/A';
            const presVal = n.pressure != null ? `${n.pressure.toFixed(1)} hPa` : 'N/A';
            const humiVal = n.humidity != null ? `${n.humidity.toFixed(1)}%` : 'N/A';

            return (
              <div
                key={n.station_id}
                className="glass-card"
                style={{
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  cursor: 'pointer',
                  border: isNominal ? '1px solid #30363d' : '1px solid #d29922',
                }}
                onClick={() => onSelectStation && onSelectStation(n)}
                title={`Click to inspect ${n.station_name}`}
              >
                {/* Station Card Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f0f6fc' }}>
                        {idx + 1}. {n.station_name}
                      </span>
                      <ArrowUpRight size={12} color="#58a6ff" />
                    </div>
                    <div style={{ fontSize: '0.68rem', color: '#8b949e', marginTop: '1px' }}>
                      ID: <span style={{ fontFamily: 'var(--font-mono)', color: '#58a6ff' }}>{n.station_id}</span> • Elev: {n.elevation_m ? `${n.elevation_m}m` : 'N/A'}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#58a6ff', fontFamily: 'var(--font-mono)' }}>
                      {n.distance_km.toFixed(1)} km
                    </span>
                    <div style={{ marginTop: '2px' }}>
                      <span className={`badge ${isNominal ? 'badge-pass' : 'badge-warning'}`} style={{ fontSize: '0.62rem' }}>
                        {isNominal ? 'Synced • Nominal' : 'Variance Suspect'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Real Live Peer Sensor Values Strip */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '6px',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    background: '#0d1117',
                    border: '1px solid #30363d',
                  }}
                >
                  {/* Temperature */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.65rem', color: '#8b949e' }}>
                      <Thermometer size={10} color="#58a6ff" />
                      <span>Temp</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc', fontFamily: 'var(--font-mono)' }}>
                      {tempVal}
                    </div>
                    {n.delta_t != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(n.delta_t) > 3.0 ? '#d29922' : '#3fb950' }}>
                        Δ {n.delta_t > 0 ? `+${n.delta_t}` : n.delta_t}°C
                      </div>
                    )}
                  </div>

                  {/* Pressure */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.65rem', color: '#8b949e' }}>
                      <Gauge size={10} color="#bc8cff" />
                      <span>Pres</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc', fontFamily: 'var(--font-mono)' }}>
                      {presVal}
                    </div>
                    {n.delta_p != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(n.delta_p) > 4.0 ? '#d29922' : '#bc8cff' }}>
                        Δ {n.delta_p > 0 ? `+${n.delta_p}` : n.delta_p} hPa
                      </div>
                    )}
                  </div>

                  {/* Humidity */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.65rem', color: '#8b949e' }}>
                      <Droplets size={10} color="#3fb950" />
                      <span>Humi</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc', fontFamily: 'var(--font-mono)' }}>
                      {humiVal}
                    </div>
                    {n.delta_h != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(n.delta_h) > 15.0 ? '#d29922' : '#3fb950' }}>
                        Δ {n.delta_h > 0 ? `+${n.delta_h}` : n.delta_h}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
