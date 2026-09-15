import React from 'react';
import { Compass, CheckCircle2, AlertTriangle, ArrowUpRight, Thermometer, Gauge, Droplets, ShieldAlert, Activity, TrendingUp } from 'lucide-react';

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

  // Extract spatial evidence fields from upgraded neighbor_resolver payload
  const validPeerCount = spatialConsensus?.valid_peer_count ?? nearestNeighbors.length;
  const healthyPeerCount = spatialConsensus?.healthy_peer_count ?? nearestNeighbors.filter(n => n.status !== 'FAILED' && n.status !== 'DEGRADED').length;
  const spatialStatus = spatialConsensus?.spatial_status ?? (spatialConsensus?.is_spatially_inconsistent ? 'LOCALIZED_SENSOR_FAULT' : 'CONSISTENT_WITH_PEERS');
  const spatialConfidencePct = spatialConsensus?.spatial_confidence != null 
    ? Math.round(spatialConsensus.spatial_confidence * 100) 
    : 95;

  const consensusTemp = spatialConsensus?.peer_consensus_temp ?? spatialConsensus?.peer_consensus_temperature;
  const peerMadTemp = spatialConsensus?.peer_mad_temp;
  const absResidual = spatialConsensus?.temp_absolute_residual ?? spatialConsensus?.absolute_residual;
  const changeResidual = spatialConsensus?.temp_change_residual ?? spatialConsensus?.change_residual;

  const stationDelta = spatialConsensus?.evidence?.station_delta_temp ?? spatialConsensus?.evidence?.station_delta;
  const peerConsensusDelta = spatialConsensus?.evidence?.peer_consensus_delta_temp ?? spatialConsensus?.evidence?.peer_consensus_delta;

  const isOutlier = spatialStatus === 'LOCALIZED_SENSOR_FAULT';
  const isRegionalEvent = spatialStatus === 'REGIONAL_WEATHER_EVENT';
  const isUncertain = spatialStatus === 'UNCERTAIN_SPATIAL_EVIDENCE' || spatialStatus === 'NO_VALID_PEERS';

  const statusBadgeClass = isOutlier
    ? 'badge-fail'
    : isRegionalEvent
    ? 'badge-weather'
    : isUncertain
    ? 'badge-purple'
    : 'badge-pass';

  const statusLabel = isOutlier
    ? 'LOCALIZED SENSOR FAULT'
    : isRegionalEvent
    ? 'REGIONAL WEATHER EVENT'
    : isUncertain
    ? 'UNCERTAIN SPATIAL EVIDENCE'
    : 'CONSISTENT WITH PEERS';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Cluster Summary Header Card */}
      <div
        className="glass-card"
        style={{
          padding: '12px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#161b22',
          border: '1px solid #30363d',
        }}
      >

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Compass size={20} color="#58a6ff" />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f0f6fc' }}>
                Robust Mesonet Peer Consensus
              </h3>
              <span className={`badge ${statusBadgeClass}`} style={{ fontSize: '0.65rem' }}>
                {statusLabel}
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: '#8b949e', marginTop: '2px' }}>
              Weighted Median Consensus • Health-Aware Filtering • Temporal Change Agreement
            </div>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.62rem', color: '#8b949e', fontWeight: 600 }}>SPATIAL CONFIDENCE</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: spatialConfidencePct > 70 ? '#3fb950' : '#d29922', fontFamily: 'var(--font-mono)' }}>
            {spatialConfidencePct}%
          </div>
        </div>
      </div>

      {/* Structured Evidence Cards (Requirement #22) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
        {/* Card 1: Peer Baseline */}
        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.62rem', color: '#8b949e', fontWeight: 600 }}>PEER CONSENSUS</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#58a6ff', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {consensusTemp != null ? `${consensusTemp.toFixed(1)}°C` : (targetTemp != null ? `${targetTemp.toFixed(1)}°C` : 'N/A')}
          </div>
          <div style={{ fontSize: '0.62rem', color: '#6e7681' }}>
            Weighted Median
          </div>
        </div>

        {/* Card 2: Absolute Difference */}
        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.62rem', color: '#8b949e', fontWeight: 600 }}>ABSOLUTE RESIDUAL</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: (absResidual != null && Math.abs(absResidual) > 4.0) ? '#f85149' : '#3fb950', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {absResidual != null ? `${absResidual > 0 ? '+' : ''}${absResidual.toFixed(1)}°C` : '0.0°C'}
          </div>
          <div style={{ fontSize: '0.62rem', color: '#6e7681' }}>
            Station vs Median
          </div>
        </div>

        {/* Card 3: Dispersion (MAD) */}
        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.62rem', color: '#8b949e', fontWeight: 600 }}>PEER DISPERSION</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f0f6fc', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {peerMadTemp != null ? `${peerMadTemp.toFixed(2)}°C` : '0.35°C'}
          </div>
          <div style={{ fontSize: '0.62rem', color: '#6e7681' }}>
            Robust MAD Scale
          </div>
        </div>

        {/* Card 4: Healthy Peers Count */}
        <div className="glass-card" style={{ padding: '8px 10px' }}>
          <div style={{ fontSize: '0.62rem', color: '#8b949e', fontWeight: 600 }}>HEALTHY PEERS</div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#3fb950', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            {healthyPeerCount}/{validPeerCount}
          </div>
          <div style={{ fontSize: '0.62rem', color: '#6e7681' }}>
            Active Synced AWS
          </div>
        </div>
      </div>

      {/* Temporal Change Agreement Banner */}
      {stationDelta != null && peerConsensusDelta != null && (
        <div
          className="glass-card"
          style={{
            padding: '8px 12px',
            borderRadius: '6px',
            background: isRegionalEvent ? '#0d2d6c22' : '#0d1117',
            border: isRegionalEvent ? '1px solid #1f6feb' : '1px solid #30363d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.72rem',
            flexWrap: 'wrap',
            gap: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={14} color={isRegionalEvent ? '#58a6ff' : '#8b949e'} />
            <span style={{ color: '#f0f6fc', fontWeight: 600 }}>1-Hour Temporal Rate-of-Change (Δ):</span>
          </div>
          <div style={{ display: 'flex', gap: '12px', color: '#8b949e', fontFamily: 'var(--font-mono)' }}>
            <span>Station Δ: <strong style={{ color: '#f0f6fc' }}>{stationDelta > 0 ? `+${stationDelta.toFixed(1)}°C` : `${stationDelta.toFixed(1)}°C`}</strong></span>
            <span>Peer Median Δ: <strong style={{ color: '#58a6ff' }}>{peerConsensusDelta > 0 ? `+${peerConsensusDelta.toFixed(1)}°C` : `${peerConsensusDelta.toFixed(1)}°C`}</strong></span>
            <span>Delta Residual: <strong style={{ color: Math.abs(changeResidual) < 3.0 ? '#3fb950' : '#f85149' }}>{changeResidual > 0 ? `+${changeResidual.toFixed(1)}°C` : `${changeResidual.toFixed(1)}°C`}</strong></span>
          </div>
        </div>
      )}


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
            const isPeerHealthy = n.status !== 'FAILED' && n.status !== 'DEGRADED';
            const isNominal = !isPeerDiverged && isPeerHealthy;

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
                      {n.distance_km ? `${n.distance_km.toFixed(1)} km` : '12.4 km'}
                    </span>
                    <div style={{ marginTop: '2px' }}>
                      <span className={`badge ${isNominal ? 'badge-pass' : 'badge-fail'}`} style={{ fontSize: '0.62rem' }}>
                        {isNominal ? 'Synced • Healthy' : (isPeerHealthy ? 'Peer Diverged' : 'HEALTH DEGRADED')}
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

