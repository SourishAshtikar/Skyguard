import React, { useState } from 'react';
import { Zap, RotateCcw, Play, ChevronDown, Sliders } from 'lucide-react';

export default function AnomalySandbox({ onInject, onRestore, onOpenCustom, isSimulating }) {
  const [anomalyType, setAnomalyType] = useState('SPIKE');
  const [magnitude, setMagnitude] = useState(1.0);

  const handleInjectClick = () => {
    onInject(anomalyType, magnitude);
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '8px 14px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        backdropFilter: 'blur(16px)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Zap size={15} color="#ffb800" />
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap' }}>
          ANOMALY INJECTOR:
        </span>
      </div>

      {/* Dropdown Selector */}
      <select
        value={anomalyType}
        onChange={(e) => setAnomalyType(e.target.value)}
        style={{
          background: '#0a101f',
          color: '#f8fafc',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          borderRadius: '6px',
          padding: '5px 10px',
          fontSize: '0.75rem',
          outline: 'none',
          cursor: 'pointer',
        }}
      >
        <option value="SPIKE">⚡ Sensor Spike (+18°C)</option>
        <option value="FROZEN">❄️ Stuck / Frozen Sensor</option>
        <option value="DRIFT">📈 Calibration Drift (+8.5 hPa)</option>
        <option value="DROPOUT">📡 Comms Telemetry Dropout</option>
        <option value="CORRUPTION">👾 Bit Framing Corruption (x10)</option>
        <option value="PHYSICAL">🧪 Dew Point &gt; Air Temp</option>
        <option value="NOISE">〰️ High-Frequency Noise Jitter</option>
        <option value="RANGE">🚨 Extreme Range Violation (64.5°C)</option>
      </select>

      {/* Preset Inject Button */}
      <button
        className="btn-danger"
        onClick={handleInjectClick}
        disabled={isSimulating}
        style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', padding: '5px 12px' }}
      >
        <Play size={11} />
        Inject Preset
      </button>

      {/* Custom Anomaly Builder Modal Trigger */}
      <button
        type="button"
        className="btn-secondary"
        onClick={onOpenCustom}
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
        }}
        title="Open Custom Anomaly Builder with direct values and offset sliders"
      >
        <Sliders size={12} color="#00f0ff" />
        + Custom Anomaly
      </button>

      <button
        className="btn-secondary"
        onClick={onRestore}
        style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', padding: '5px 10px' }}
      >
        <RotateCcw size={11} />
        Restore
      </button>
    </div>
  );
}
