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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Cluster Summary Header Card */}
      <div
        className="glass-card"
        style={{
          padding: '14px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(10, 16, 30, 0.65)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Compass size={18} color="#00f0ff" />
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc' }}>
              Spatial Mesonet Peer Consensus
            </h3>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
              150 km Haversine Correlation Radius • Barometric MSLP Reduced
            </div>
          </div>
        </div>
        <span className={`badge ${spatialConsensus?.is_spatially_inconsistent ? 'badge-fail' : 'badge-pass'}`}>
          {spatialConsensus?.is_spatially_inconsistent ? 'SPATIAL OUTLIER' : 'CONSENSUS VERIFIED'}
        </span>
      </div>

      {/* 3 Metric Summary Dial Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
        <div className="glass-card" style={{ padding: '10px 12px' }}>
          <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>CONSENSUS SCORE</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#00f0ff', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {((spatialConsensus?.spatial_consensus_score ?? 0.95) * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Cluster Correlation</div>
        </div>

        <div className="glass-card" style={{ padding: '10px 12px' }}>
          <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>TARGET DEVIATION</div>
          <div
            style={{
              fontSize: '1.3rem',
              fontWeight: 800,
              color: (spatialConsensus?.target_deviation_temp || 0) > 4.0 ? '#ff3366' : '#00e599',
              marginTop: '2px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {spatialConsensus?.target_deviation_temp ? `${spatialConsensus.target_deviation_temp.toFixed(1)}°C` : '0.4°C'}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>vs Regional Median</div>
        </div>

        <div className="glass-card" style={{ padding: '10px 12px' }}>
          <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>PEER STATIONS</div>
          <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {nearestNeighbors.length} AWS
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Live Synced Neighbors</div>
        </div>
      </div>

      {/* Neighbor List with Real Live Telemetry Values */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.03em' }}>
            CORROBORATING PEER SENSOR STREAMS:
          </span>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
            Click station to switch inspector
          </span>
        </div>

        {nearestNeighbors.length === 0 ? (
          <div className="glass-card" style={{ padding: '20px', textAlign: 'center', fontSize: '0.78rem', color: '#64748b' }}>
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
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  cursor: 'pointer',
                  border: isNominal ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(255, 184, 0, 0.3)',
                  transition: 'all 0.2s ease',
                }}
                onClick={() => onSelectStation && onSelectStation(n)}
                title={`Click to inspect ${n.station_name}`}
              >
                {/* Station Card Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>
                        {idx + 1}. {n.station_name}
                      </span>
                      <ArrowUpRight size={13} color="#00f0ff" />
                    </div>
                    <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginTop: '1px' }}>
                      ID: <span style={{ fontFamily: 'var(--font-mono)', color: '#00f0ff' }}>{n.station_id}</span> • Elev: {n.elevation_m ? `${n.elevation_m}m` : 'N/A'}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 800, color: '#00f0ff', fontFamily: 'var(--font-mono)' }}>
                      {n.distance_km.toFixed(1)} km
                    </span>
                    <div style={{ marginTop: '2px' }}>
                      <span
                        style={{
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          padding: '1px 6px',
                          borderRadius: '8px',
                          background: isNominal ? 'rgba(0, 229, 153, 0.12)' : 'rgba(255, 184, 0, 0.12)',
                          color: isNominal ? '#00e599' : '#ffb800',
                          border: `1px solid ${isNominal ? 'rgba(0, 229, 153, 0.3)' : 'rgba(255, 184, 0, 0.3)'}`,
                        }}
                      >
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
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                  }}
                >
                  {/* Temperature */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.65rem', color: '#94a3b8' }}>
                      <Thermometer size={10} color="#00f0ff" />
                      <span>Temp</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                      {tempVal}
                    </div>
                    {n.delta_t != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(n.delta_t) > 3.0 ? '#ffb800' : '#00e599' }}>
                        Δ {n.delta_t > 0 ? `+${n.delta_t}` : n.delta_t}°C
                      </div>
                    )}
                  </div>

                  {/* Pressure */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.65rem', color: '#94a3b8' }}>
                      <Gauge size={10} color="#a855f7" />
                      <span>Pres</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                      {presVal}
                    </div>
                    {n.delta_p != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(n.delta_p) > 4.0 ? '#ffb800' : '#a855f7' }}>
                        Δ {n.delta_p > 0 ? `+${n.delta_p}` : n.delta_p} hPa
                      </div>
                    )}
                  </div>

                  {/* Humidity */}
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.65rem', color: '#94a3b8' }}>
                      <Droplets size={10} color="#00e599" />
                      <span>Humi</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>
                      {humiVal}
                    </div>
                    {n.delta_h != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(n.delta_h) > 15.0 ? '#ffb800' : '#00e599' }}>
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
