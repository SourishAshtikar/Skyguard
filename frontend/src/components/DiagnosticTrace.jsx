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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Trace Header with Official WMO Standard Badge (Completely Removed Latency) */}
      <div
        className="glass-card"
        style={{
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(10, 16, 30, 0.65)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={16} color="#00f0ff" />
          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
            Multi-Tier Pipeline Verification
          </span>
        </div>

        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            padding: '3px 10px',
            borderRadius: '12px',
            background: activeFlagBadge.bg,
            border: `1px solid ${activeFlagBadge.border}`,
            color: activeFlagBadge.color,
          }}
        >
          {activeFlagBadge.text}
        </span>
      </div>

      {/* Tier 1: ESP32 Edge Physical Invariants Card */}
      <div className="glass-card" style={{ padding: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00f0ff' }} />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>
              TIER 1: ESP32 EDGE QC RULES
            </span>
          </div>
          <span className={`badge ${tier1.status === 'PASS' ? 'badge-pass' : (tier1.status === 'SUSPECT' ? 'badge-suspect' : 'badge-fail')}`}>
            {tier1.status}
          </span>
        </div>

        <div style={{ fontSize: '0.74rem', color: '#94a3b8', lineHeight: '1.45' }}>
          Deterministic checks: Climatological range bounds (WMO Guide 8), 4σ rate-of-change limits, stuck sensor persistence, and thermodynamic dew point invariants (Dew Point &le; Air Temperature).
        </div>

        <div style={{ marginTop: '10px', padding: '8px 10px', borderRadius: '6px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid var(--border-subtle)' }}>
          {tier1.rules_fired && tier1.rules_fired.length > 0 ? (
            <div>
              <div style={{ fontSize: '0.72rem', color: '#ff3366', fontWeight: 700, marginBottom: '2px' }}>
                Rules Triggered: {tier1.rules_fired.join(', ')}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#cbd5e1' }}>
                Physical atmospheric consistency violation detected at edge microcontroller.
              </div>
            </div>
          ) : (
            <div style={{ color: '#00e599', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
              <CheckCircle size={14} color="#00e599" />
              All physical laws and deterministic threshold checks passed.
            </div>
          )}
        </div>
      </div>

      {/* Tier 2: Micro-Autoencoder Reconstruction Card */}
      <div className="glass-card" style={{ padding: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#a855f7' }} />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>
              TIER 2: EDGE AUTOENCODER RECONSTRUCTION
            </span>
          </div>
          <span className={`badge ${tier2?.is_anomaly ? 'badge-fail' : 'badge-pass'}`}>
            {tier2?.is_anomaly ? 'ANOMALOUS MANIFOLD' : 'NOMINAL MANIFOLD'}
          </span>
        </div>

        <div style={{ fontSize: '0.74rem', color: '#94a3b8', lineHeight: '1.45' }}>
          Quantized edge neural network ($10 \to 8 \to 4 \to 8 \to 10$) checks nonlinear multivariate atmospheric correlations across temperature, pressure, and moisture.
        </div>

        <div style={{ marginTop: '10px', padding: '8px 10px', borderRadius: '6px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Reconstruction Anomaly Score:</span>
            <strong style={{ fontSize: '0.85rem', color: tier2?.is_anomaly ? '#ff3366' : '#00f0ff' }}>
              {(tier2?.score ?? 0.04).toFixed(3)}
            </strong>
          </div>
          <div style={{ width: '100%', height: '5px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${Math.min(100, Math.max(5, (tier2?.score || 0.05) * 100))}%`,
                height: '100%',
                background: tier2?.is_anomaly ? 'linear-gradient(90deg, #ffb800, #ff3366)' : '#00f0ff',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>
      </div>

      {/* Tier 3: Cloud Arbiter & Regional Mesonet Consensus Card */}
      <div className="glass-card" style={{ padding: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00e599' }} />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>
              TIER 3: CLOUD ARBITER &amp; REGIONAL CONSENSUS
            </span>
          </div>
          <span className={`badge ${stage3_arbiter?.is_weather_event ? 'badge-suspect' : (latestResult.final_anomaly ? 'badge-fail' : 'badge-pass')}`}>
            {stage3_arbiter?.is_weather_event ? 'WEATHER EVENT' : (latestResult.final_anomaly ? 'FAULT CONFIRMED' : 'PASSED')}
          </span>
        </div>

        <div style={{ fontSize: '0.74rem', color: '#94a3b8', lineHeight: '1.45' }}>
          Hierarchical XGBoost arbiter resolves false alarms by comparing state-space Kalman residuals with {spatial_consensus?.neighbor_count ?? 5} neighboring AWS stations within 150 km.
        </div>

        <div style={{ marginTop: '10px', padding: '10px', borderRadius: '6px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Diagnosis Verdict:</span>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f8fafc' }}>
              {stage3_arbiter?.root_cause ?? 'Normal Atmospheric Invariants'}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Classification Confidence:</span>
            <strong style={{ fontSize: '0.8rem', color: '#00e599' }}>
              {((stage3_arbiter?.confidence ?? 0.95) * 100).toFixed(1)}%
            </strong>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Regional Mesonet Corroboration:</span>
            <span style={{ fontSize: '0.78rem', color: spatial_consensus?.is_spatially_inconsistent ? '#ff3366' : '#00e599', fontWeight: 600 }}>
              {spatial_consensus?.is_spatially_inconsistent ? 'Divergent from Peers' : `${spatial_consensus?.neighbor_count ?? 5} Peers In Agreement`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
