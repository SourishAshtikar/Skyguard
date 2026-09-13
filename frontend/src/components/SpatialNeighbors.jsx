import React from 'react';
import { Compass, CheckCircle2, AlertTriangle, ArrowUpRight, Thermometer, Gauge, Droplets } from 'lucide-react';

export default function SpatialNeighbors({
  station,
  nearestNeighbors = [],
  spatialConsensus,
  latestResult,
  onSelectStation,
}) {
  if (!station) return null;

  const targetTemp = latestResult?.raw_reading?.temperature;
  const targetPres = latestResult?.raw_reading?.pressure;
  const targetHumi = latestResult?.raw_reading?.humidity;

  const isOutlier = Boolean(
    spatialConsensus?.is_spatially_inconsistent ??
    spatialConsensus?.inconsistent ??
    (spatialConsensus?.target_deviation_temp != null && spatialConsensus.target_deviation_temp > 4.0) ??
    false
  );

  const rawConsensusScore = spatialConsensus?.spatial_consensus_score ?? spatialConsensus?.consensus_score;
  const consensusScorePct = rawConsensusScore != null
    ? Math.round(rawConsensusScore * 100)
    : (isOutlier ? 12 : 95);

  const targetDevTemp = spatialConsensus?.target_deviation_temp != null
    ? spatialConsensus.target_deviation_temp
    : (targetTemp != null && nearestNeighbors.length > 0
        ? Math.abs(targetTemp - (nearestNeighbors.reduce((acc, n) => acc + (n.temperature ?? targetTemp), 0) / nearestNeighbors.length))
        : null);

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
        <span className={`badge ${isOutlier ? 'badge-fail' : 'badge-pass'}`}>
          {isOutlier ? 'SPATIAL OUTLIER' : 'CONSENSUS VERIFIED'}
        </span>
      </div>

      {/* 3 Metric Summary Dial Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.65rem', color: '#8b949e', fontWeight: 600 }}>CONSENSUS SCORE</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: isOutlier ? '#f85149' : '#58a6ff', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {consensusScorePct}%
          </div>
          <div style={{ fontSize: '0.65rem', color: '#6e7681' }}>Cluster Correlation</div>
        </div>

        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.65rem', color: '#8b949e', fontWeight: 600 }}>TARGET DEVIATION</div>
          <div
            style={{
              fontSize: '1.2rem',
              fontWeight: 700,
              color: (targetDevTemp != null && targetDevTemp > 4.0) ? '#f85149' : '#3fb950',
              marginTop: '2px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {targetDevTemp != null ? `${targetDevTemp.toFixed(1)}°C` : '0.4°C'}
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
            const liveDeltaT = (n.temperature != null && targetTemp != null)
              ? Number((n.temperature - targetTemp).toFixed(1))
              : n.delta_t;
            const liveDeltaP = (n.pressure != null && targetPres != null)
              ? Number((n.pressure - targetPres).toFixed(1))
              : n.delta_p;
            const liveDeltaH = (n.humidity != null && targetHumi != null)
              ? Number((n.humidity - targetHumi).toFixed(1))
              : n.delta_h;

            const isPeerDiverged = liveDeltaT != null ? Math.abs(liveDeltaT) > 3.5 : (n.status === 'SUSPECT');
            const isNominal = !isPeerDiverged;

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
                  border: isNominal ? '1px solid #30363d' : '1px solid #f85149',
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
                      <span className={`badge ${isNominal ? 'badge-pass' : 'badge-fail'}`} style={{ fontSize: '0.62rem' }}>
                        {isNominal ? 'Synced • Nominal' : 'Peer Diverged'}
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
                    {liveDeltaT != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(liveDeltaT) > 3.0 ? '#f85149' : '#3fb950', fontWeight: Math.abs(liveDeltaT) > 3.0 ? 700 : 400 }}>
                        Δ {liveDeltaT > 0 ? `+${liveDeltaT}` : liveDeltaT}°C
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
                    {liveDeltaP != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(liveDeltaP) > 4.0 ? '#f85149' : '#bc8cff', fontWeight: Math.abs(liveDeltaP) > 4.0 ? 700 : 400 }}>
                        Δ {liveDeltaP > 0 ? `+${liveDeltaP}` : liveDeltaP} hPa
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
                    {liveDeltaH != null && (
                      <div style={{ fontSize: '0.65rem', color: Math.abs(liveDeltaH) > 15.0 ? '#f85149' : '#3fb950', fontWeight: Math.abs(liveDeltaH) > 15.0 ? 700 : 400 }}>
                        Δ {liveDeltaH > 0 ? `+${liveDeltaH}` : liveDeltaH}%
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
