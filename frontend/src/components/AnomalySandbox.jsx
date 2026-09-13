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
        padding: '6px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: '6px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Zap size={14} color="#d29922" />
        <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#8b949e', whiteSpace: 'nowrap' }}>
          FAULT INJECTION:
        </span>
      </div>

      {/* Dropdown Selector */}
      <select
        value={anomalyType}
        onChange={(e) => setAnomalyType(e.target.value)}
        style={{
          background: '#0d1117',
          color: '#f0f6fc',
          border: '1px solid #30363d',
          borderRadius: '4px',
          padding: '4px 8px',
          fontSize: '0.72rem',
          outline: 'none',
          cursor: 'pointer',
        }}
      >
        <option value="SPIKE">Sensor Spike (+18°C)</option>
        <option value="FROZEN">Stuck / Frozen Sensor</option>
        <option value="DRIFT">Calibration Drift (+8.5 hPa)</option>
        <option value="DROPOUT">Comms Telemetry Dropout</option>
        <option value="CORRUPTION">Bit Framing Corruption (x10)</option>
        <option value="PHYSICAL">Dew Point &gt; Air Temp</option>
        <option value="NOISE">High-Frequency Noise Jitter</option>
        <option value="RANGE">Physical Range Violation (64.5°C)</option>
      </select>

      {/* Preset Inject Button */}
      <button
        className="btn-ghost"
        onClick={handleInjectClick}
        disabled={isSimulating}
        style={{
          fontSize: '0.72rem',
          padding: '4px 10px',
          color: '#f85149',
          borderColor: 'rgba(248, 81, 73, 0.4)',
        }}
      >
        <Play size={11} />
        Inject Fault
      </button>

      {/* Custom Anomaly Builder Modal Trigger */}
      <button
        type="button"
        className="btn-ghost"
        onClick={onOpenCustom}
        style={{
          fontSize: '0.72rem',
          padding: '4px 10px',
          color: '#58a6ff',
          borderColor: 'rgba(88, 166, 255, 0.4)',
        }}
        title="Open Custom Anomaly Builder with direct values and offset sliders"
      >
        <Sliders size={11} />
        Custom Fault
      </button>

      <button
        className="btn-ghost"
        onClick={onRestore}
        style={{ fontSize: '0.72rem', padding: '4px 10px' }}
      >
        <RotateCcw size={11} />
        Restore Nominal
      </button>
    </div>
  );
}
