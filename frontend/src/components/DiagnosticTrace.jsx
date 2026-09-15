import React from 'react';
import { Cpu, Cloud, CheckCircle, AlertTriangle, XCircle, Compass, ShieldCheck, Zap } from 'lucide-react';

export default function DiagnosticTrace({ latestResult }) {
  if (!latestResult) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
        Awaiting telemetry ingestion to render 3-tier diagnostic trace...
      </div>
    );
  }

  const { tier1, tier2, stage1_forecast, spatial_consensus, stage3_arbiter, final_status, wmo_qc_flag } = latestResult;

  // IMD / WMO Flag info (Biju et al., 2012)
  const qcFlag = wmo_qc_flag ?? (latestResult.final_anomaly ? 2 : 0);
  const qcBadgeColors = {
    0: { text: 'WMO Flag 0: Good', bg: 'rgba(0, 229, 153, 0.15)', border: '#00e599', color: '#00e599' },
    1: { text: 'WMO Flag 1: Suspect / Weather', bg: 'rgba(255, 184, 0, 0.15)', border: '#ffb800', color: '#ffb800' },
    2: { text: 'WMO Flag 2: Erroneous', bg: 'rgba(255, 51, 102, 0.15)', border: '#ff3366', color: '#ff3366' },
    3: { text: 'WMO Flag 3: Missing', bg: 'rgba(148, 163, 184, 0.15)', border: '#94a3b8', color: '#94a3b8' },
    4: { text: 'WMO Flag 4: Self-Healed Imputed', bg: 'rgba(0, 240, 255, 0.15)', border: '#00f0ff', color: '#00f0ff' },
  };
  const activeFlagBadge = qcBadgeColors[qcFlag] || qcBadgeColors[0];

  const t1Status = tier1?.status || 'PASS';
  const t1Rules = tier1?.rules_fired || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* Trace Header with Official WMO Standard Badge */}
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
          <Zap size={15} color="#58a6ff" />
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f0f6fc' }}>
            Multi-Tier Pipeline Verification
          </span>
        </div>

        <span
          className={`badge ${qcFlag === 0 ? 'badge-pass' : (qcFlag === 1 ? 'badge-warning' : (qcFlag === 4 ? 'badge-purple' : 'badge-fail'))}`}
        >
          {qcBadgeColors[qcFlag]?.text || 'WMO Flag 0: Good'}
        </span>
      </div>

      {/* Tier 1: ESP32 Edge Physical Invariants Card */}
      <div className="glass-card" style={{ padding: '12px 14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#58a6ff' }} />
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc' }}>
              TIER 1: ESP32 EDGE QC RULES
            </span>
          </div>
          <span className={`badge ${t1Status === 'PASS' ? 'badge-pass' : (t1Status === 'SUSPECT' ? 'badge-warning' : 'badge-fail')}`}>
            {t1Status}
          </span>
        </div>

        <div style={{ fontSize: '0.72rem', color: '#8b949e', lineHeight: '1.4' }}>
          Deterministic checks: Climatological range bounds (WMO Guide 8), 4σ rate-of-change limits, stuck sensor persistence, and thermodynamic dew point invariants (Dew Point &le; Air Temperature).
        </div>

        <div style={{ marginTop: '8px', padding: '8px 10px', borderRadius: '4px', background: '#0d1117', border: '1px solid #30363d' }}>
          {t1Rules.length > 0 ? (
            <div>
              <div style={{ fontSize: '0.72rem', color: '#f85149', fontWeight: 700, marginBottom: '2px' }}>
                Rules Triggered: {t1Rules.join(', ')}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#8b949e' }}>
                Physical atmospheric consistency violation detected at edge microcontroller.
              </div>
            </div>
          ) : (
            <div style={{ color: '#3fb950', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <CheckCircle size={13} color="#3fb950" />
              All physical laws and deterministic threshold checks passed.
            </div>
          )}
        </div>
      </div>

      {/* Tier 2: Micro-Autoencoder Reconstruction Card */}
      <div className="glass-card" style={{ padding: '12px 14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#bc8cff' }} />
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc' }}>
              TIER 2: EDGE AUTOENCODER RECONSTRUCTION
            </span>
          </div>
          <span className={`badge ${tier2?.is_anomaly ? 'badge-fail' : 'badge-pass'}`}>
            {tier2?.is_anomaly ? 'ANOMALOUS MANIFOLD' : 'NOMINAL MANIFOLD'}
          </span>
        </div>

        <div style={{ fontSize: '0.72rem', color: '#8b949e', lineHeight: '1.4' }}>
          Quantized edge neural network (10 → 8 → 4 → 8 → 10) checks nonlinear multivariate atmospheric correlations across temperature, pressure, and moisture.
        </div>

        <div style={{ marginTop: '8px', padding: '8px 10px', borderRadius: '4px', background: '#0d1117', border: '1px solid #30363d' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ fontSize: '0.7rem', color: '#8b949e' }}>Reconstruction Anomaly Score:</span>
            <strong style={{ fontSize: '0.8rem', color: tier2?.is_anomaly ? '#f85149' : '#58a6ff', fontFamily: 'var(--font-mono)' }}>
              {(tier2?.score ?? 0.04).toFixed(3)}
            </strong>
          </div>
          <div style={{ width: '100%', height: '4px', background: '#21262d', borderRadius: '2px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${Math.min(100, Math.max(5, (tier2?.score || 0.05) * 100))}%`,
                height: '100%',
                background: tier2?.is_anomaly ? '#f85149' : '#58a6ff',
                transition: 'width 0.2s ease',
              }}
            />
          </div>
        </div>
      </div>

      {/* Tier 3: Cloud Arbiter & Regional Mesonet Consensus Card */}
      <div className="glass-card" style={{ padding: '12px 14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3fb950' }} />
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc' }}>
              TIER 3: CLOUD ARBITER &amp; REGIONAL CONSENSUS
            </span>
          </div>
          <span className={`badge ${stage3_arbiter?.is_weather_event ? 'badge-weather' : (latestResult.final_anomaly ? 'badge-fail' : 'badge-pass')}`}>
            {stage3_arbiter?.is_weather_event ? 'WEATHER EVENT' : (latestResult.final_anomaly ? 'FAULT CONFIRMED' : 'PASSED')}
          </span>
        </div>

        <div style={{ fontSize: '0.72rem', color: '#8b949e', lineHeight: '1.4' }}>
          Hierarchical XGBoost arbiter resolves false alarms by comparing state-space Kalman residuals with {spatial_consensus?.neighbor_count ?? 5} neighboring AWS stations within 150 km.
        </div>

        <div style={{ marginTop: '8px', padding: '8px 10px', borderRadius: '4px', background: '#0d1117', border: '1px solid #30363d', display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.7rem', color: '#8b949e' }}>Diagnosis Verdict:</span>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f0f6fc' }}>
              {stage3_arbiter?.root_cause ?? 'Normal Atmospheric Invariants'}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.7rem', color: '#8b949e' }}>Classification Confidence:</span>
            <strong style={{ fontSize: '0.75rem', color: '#3fb950', fontFamily: 'var(--font-mono)' }}>
              {((stage3_arbiter?.confidence ?? 0.95) * 100).toFixed(1)}%
            </strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.7rem', color: '#8b949e' }}>Regional Mesonet Corroboration:</span>
            <span style={{ fontSize: '0.75rem', color: spatial_consensus?.is_spatially_inconsistent ? '#f85149' : '#3fb950', fontWeight: 600 }}>
              {spatial_consensus?.is_spatially_inconsistent ? 'Divergent from Peers' : `${spatial_consensus?.neighbor_count ?? 5} Peers In Agreement`}
            </span>
          </div>
        </div>
      </div>

      {/* Sensor Health & Predictive Maintenance Breakdown */}
      {latestResult?.sensor_health && (
        <div className="glass-card" style={{ padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#bc8cff' }} />
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f0f6fc' }}>
                SENSOR HEALTH &amp; PREDICTIVE MAINTENANCE
              </span>
            </div>
            <span className={`badge ${latestResult.sensor_health.status === 'CRITICAL' ? 'badge-fail' : (latestResult.sensor_health.status === 'DEGRADED' ? 'badge-warning' : 'badge-pass')}`}>
              {latestResult.sensor_health.status || 'NOMINAL'} ({((latestResult.sensor_health.health_score_pct ?? latestResult.sensor_health.score_pct ?? 100)).toFixed(0)}%)
            </span>
          </div>

          <div style={{ fontSize: '0.72rem', color: '#8b949e', lineHeight: '1.4', marginBottom: '8px' }}>
            Sliding 48-reading degradation tracker evaluating transducer calibration drift, consecutive anomalies, and telemetry packet dropouts.
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
            <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '4px', padding: '6px 8px' }}>
              <div style={{ fontSize: '0.66rem', color: '#8b949e' }}>ROLLING ANOMALY RATE (55% WT)</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: (latestResult.sensor_health.rolling_anomaly_rate ?? 0) > 0.15 ? '#f85149' : '#f0f6fc', fontFamily: 'var(--font-mono)' }}>
                {((latestResult.sensor_health.rolling_anomaly_rate ?? 0) * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.62rem', color: '#6e7681', marginTop: '2px' }}>
                Frequency of rejected readings in last 48 cycles
              </div>
            </div>

            <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '4px', padding: '6px 8px' }}>
              <div style={{ fontSize: '0.66rem', color: '#8b949e' }}>CONSECUTIVE FAILURES</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: (latestResult.sensor_health.consecutive_failures ?? 0) > 3 ? '#f85149' : '#f0f6fc', fontFamily: 'var(--font-mono)' }}>
                {latestResult.sensor_health.consecutive_failures ?? 0} cycles
              </div>
              <div style={{ fontSize: '0.62rem', color: '#6e7681', marginTop: '2px' }}>
                Unbroken string of hardware or physical faults
              </div>
            </div>

            <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '4px', padding: '6px 8px' }}>
              <div style={{ fontSize: '0.66rem', color: '#8b949e' }}>ZERO-POINT DRIFT (ACCUM)</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: (latestResult.sensor_health.drift_indicator ?? 0) > 5.0 ? '#d29922' : '#f0f6fc', fontFamily: 'var(--font-mono)' }}>
                {(latestResult.sensor_health.drift_indicator ?? 0).toFixed(1)} units
              </div>
              <div style={{ fontSize: '0.62rem', color: '#6e7681', marginTop: '2px' }}>
                Long-term calibration offset from baseline
              </div>
            </div>

            <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '4px', padding: '6px 8px' }}>
              <div style={{ fontSize: '0.66rem', color: '#8b949e' }}>PREDICTED MAINTENANCE</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700,
                color: latestResult.sensor_health.predicted_maintenance_days != null && latestResult.sensor_health.predicted_maintenance_days <= 7 ? '#f85149' : '#3fb950',
                fontFamily: 'var(--font-mono)'
              }}>
                {latestResult.sensor_health.predicted_maintenance_days != null
                  ? `${latestResult.sensor_health.predicted_maintenance_days} Days`
                  : 'No data'}
              </div>
              <div style={{ fontSize: '0.62rem', color: '#6e7681', marginTop: '2px' }}>
                Estimated time until mandatory technician visit
              </div>
            </div>
          </div>

          <div style={{ marginTop: '8px', padding: '6px 8px', background: 'rgba(56, 139, 253, 0.08)', border: '1px solid #1f6feb', borderRadius: '4px', fontSize: '0.68rem', color: '#58a6ff' }}>
            <strong>Action:</strong> {latestResult.sensor_health.recommended_action ?? latestResult.sensor_health.action ?? 'Continue monitoring'}
          </div>
        </div>
      )}
    </div>
  );
}
