import React, { useState } from 'react';
import { Sparkles, FileText, Check, Copy, ShieldAlert, Cpu } from 'lucide-react';

export default function ShapPanel({ latestResult }) {
  const [copied, setCopied] = useState(false);

  if (!latestResult) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
        Awaiting telemetry ingestion to generate TreeSHAP attributions and RCA log...
      </div>
    );
  }

  const shapTop = latestResult?.stage3_arbiter?.shap_top || [
    ['dew_point', 0.42],
    ['temp_delta_1', 0.38],
    ['dp_depress', -0.28],
    ['temp_persist_len', 0.19],
    ['spatial_consensus_score', -0.15],
  ];

  const maxAbs = Math.max(...shapTop.map(([_, val]) => Math.abs(val)), 0.1);

  const featureLabels = {
    dew_point: 'Dew Point Temperature',
    temp_delta_1: '1-Hour Temp Rate-of-Change',
    dp_depress: 'Dew Point Depression (T - Td)',
    temp_persist_len: 'Consecutive Value Persistence',
    spatial_consensus_score: 'Mesonet Spatial Agreement',
    vap_pres: 'Actual Vapor Pressure',
    heat_idx: 'Rothfusz Heat Index',
    temp_z: 'Diurnal Climatological Z-Score',
    pres_delta_1: '1-Hour Pressure Tendency',
    humi_delta_1: '1-Hour Humidity Tendency',
  };

  const handleCopyRca = () => {
    if (latestResult?.plain_english_rca) {
      navigator.clipboard.writeText(latestResult.plain_english_rca);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isAnomaly = latestResult?.final_anomaly ?? false;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* 1. BIG, EXPANDED OPERATOR ROOT CAUSE ANALYSIS (RCA) SECTION */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          border: isAnomaly ? '1px solid rgba(255, 51, 102, 0.35)' : '1px solid rgba(0, 229, 153, 0.35)',
          background: 'rgba(10, 16, 30, 0.85)',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        }}
      >
        {/* RCA Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color={isAnomaly ? '#ff3366' : '#00e599'} />
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
                Operator Root Cause Analysis (RCA)
              </h3>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Audited plain-English diagnostic narrative &amp; recommended engineering actions
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className="btn-secondary"
              onClick={handleCopyRca}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '4px 10px',
                fontSize: '0.72rem',
                borderRadius: '6px',
              }}
              title="Copy RCA report to clipboard"
            >
              {copied ? <Check size={12} color="#00e599" /> : <Copy size={12} />}
              <span>{copied ? 'Copied' : 'Copy Log'}</span>
            </button>

            <span className={`badge ${isAnomaly ? 'badge-fail' : 'badge-pass'}`} style={{ fontSize: '0.7rem' }}>
              {isAnomaly ? 'MALFUNCTION DETECTED' : 'SYSTEM NOMINAL'}
            </span>
          </div>
        </div>

        {/* Big, Spacious Terminal Incident Log Viewport */}
        <div
          style={{
            background: '#040711',
            border: '1px solid rgba(0, 240, 255, 0.15)',
            borderRadius: '10px',
            padding: '16px 18px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.82rem',
            color: '#e2e8f0',
            whiteSpace: 'pre-wrap',
            minHeight: '220px',
            maxHeight: '340px',
            overflowY: 'auto',
            lineHeight: '1.65',
            boxShadow: 'inset 0 2px 10px rgba(0, 0, 0, 0.7)',
          }}
        >
          {latestResult.plain_english_rca}
        </div>
      </div>

      {/* 2. FULL-WIDTH TREESHAP FEATURE ATTRIBUTION DEEP DIVE */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          borderRadius: '12px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="#00f0ff" />
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc' }}>
              TreeSHAP Feature Attributions &amp; Impact
            </h3>
          </div>
          <span style={{ fontSize: '0.7rem', color: '#00f0ff', fontWeight: 600 }}>
            Cooperative Game Theory Local Drivers
          </span>
        </div>

        <p style={{ fontSize: '0.74rem', color: '#94a3b8', lineHeight: '1.4' }}>
          Exact Shapley value decomposition showing how each atmospheric feature influenced the XGBoost diagnostic classifier towards the verdict:
        </p>

        {/* Feature Bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '2px' }}>
          {shapTop.map(([feat, val]) => {
            const isPositive = val >= 0;
            const pct = (Math.abs(val) / maxAbs) * 100;
            const label = featureLabels[feat] || feat;

            return (
              <div key={feat} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 600, color: '#f8fafc' }}>{label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#64748b' }}>({feat})</span>
                  </div>
                  <strong style={{ color: isPositive ? '#ff3366' : '#00f0ff', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {isPositive ? `+${val.toFixed(3)}` : val.toFixed(3)}
                  </strong>
                </div>

                {/* Attribution Bar */}
                <div style={{ width: '100%', height: '6px', background: '#0a0f1d', borderRadius: '3px', position: 'relative', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div
                    style={{
                      position: 'absolute',
                      left: '50%',
                      width: `${pct / 2}%`,
                      height: '100%',
                      background: isPositive ? 'linear-gradient(90deg, #ffb800, #ff3366)' : 'linear-gradient(90deg, #00e599, #00f0ff)',
                      borderRadius: '3px',
                      transform: isPositive ? 'none' : 'translateX(-100%)',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
