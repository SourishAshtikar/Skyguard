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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {/* 1. OPERATOR ROOT CAUSE ANALYSIS (RCA) SECTION */}
      <div
        className="glass-card"
        style={{
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          border: isAnomaly ? '1px solid #f85149' : '1px solid #30363d',
          background: '#161b22',
        }}
      >
        {/* RCA Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={16} color={isAnomaly ? '#f85149' : '#3fb950'} />
            <div>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f0f6fc' }}>
                Operator Root Cause Analysis (RCA)
              </h3>
              <div style={{ fontSize: '0.7rem', color: '#8b949e' }}>
                Audited diagnostic narrative &amp; engineering recommendations
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              className="btn-ghost"
              onClick={handleCopyRca}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 8px',
                fontSize: '0.7rem',
              }}
              title="Copy RCA report to clipboard"
            >
              {copied ? <Check size={11} color="#3fb950" /> : <Copy size={11} />}
              <span>{copied ? 'Copied' : 'Copy Log'}</span>
            </button>

            <span className={`badge ${isAnomaly ? 'badge-fail' : 'badge-pass'}`} style={{ fontSize: '0.65rem' }}>
              {isAnomaly ? 'FAULT DETECTED' : 'SYSTEM NOMINAL'}
            </span>
          </div>
        </div>

        {/* Terminal Incident Log Viewport */}
        <div
          style={{
            background: '#0d1117',
            border: '1px solid #30363d',
            borderRadius: '4px',
            padding: '12px 14px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: '#f0f6fc',
            whiteSpace: 'pre-wrap',
            minHeight: '180px',
            maxHeight: '300px',
            overflowY: 'auto',
            lineHeight: '1.5',
          }}
        >
          {latestResult.plain_english_rca}
        </div>
      </div>

      {/* 2. TREESHAP FEATURE ATTRIBUTION DEEP DIVE */}
      <div
        className="glass-card"
        style={{
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          background: '#161b22',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={15} color="#58a6ff" />
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f0f6fc' }}>
              TreeSHAP Feature Attributions &amp; Impact
            </h3>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#8b949e', fontWeight: 600 }}>
            Shapley Local Explanations
          </span>
        </div>

        <p style={{ fontSize: '0.72rem', color: '#8b949e', lineHeight: '1.4' }}>
          Exact Shapley value decomposition showing feature contribution towards the classifier decision:
        </p>

        {/* Feature Bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '2px' }}>
          {shapTop.map(([feat, val]) => {
            const isPositive = val >= 0;
            const pct = (Math.abs(val) / maxAbs) * 100;
            const label = featureLabels[feat] || feat;

            return (
              <div key={feat} style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 600, color: '#f0f6fc' }}>{label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: '#6e7681' }}>({feat})</span>
                  </div>
                  <strong style={{ color: isPositive ? '#f85149' : '#58a6ff', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    {isPositive ? `+${val.toFixed(3)}` : val.toFixed(3)}
                  </strong>
                </div>

                {/* Attribution Bar */}
                <div style={{ width: '100%', height: '4px', background: '#0d1117', borderRadius: '2px', position: 'relative', border: '1px solid #30363d' }}>
                  <div
                    style={{
                      position: 'absolute',
                      left: '50%',
                      width: `${pct / 2}%`,
                      height: '100%',
                      background: isPositive ? '#f85149' : '#3fb950',
                      borderRadius: '2px',
                      transform: isPositive ? 'none' : 'translateX(-100%)',
                      transition: 'width 0.2s ease',
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
