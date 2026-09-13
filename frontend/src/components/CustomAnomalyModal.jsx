import React, { useState } from 'react';
import { X, Sparkles, AlertTriangle, BatteryCharging, Thermometer, Gauge, Droplets, Sliders } from 'lucide-react';

export default function CustomAnomalyModal({
  isOpen,
  onClose,
  onInjectCustom,
  selectedStation,
  latestResult,
}) {
  if (!isOpen) return null;

  const currentTemp = latestResult?.raw_reading?.temperature ?? 28.0;
  const currentPres = latestResult?.raw_reading?.pressure ?? 1012.0;
  const currentHumi = latestResult?.raw_reading?.humidity ?? 60.0;
  const currentBatt = latestResult?.raw_reading?.battery_voltage ?? 12.6;

  const [param, setParam] = useState('temperature');
  const [mode, setMode] = useState('DIRECT_VALUE'); // 'DIRECT_VALUE' | 'OFFSET' | 'STUCK' | 'INVERSION' | 'DROPOUT' | 'LOW_BATTERY'
  const [directVal, setDirectVal] = useState(65.0);
  const [offsetDelta, setOffsetDelta] = useState(18.0);
  const [stuckCycles, setStuckCycles] = useState(8);

  const handleSubmit = (e) => {
    e.preventDefault();
    onInjectCustom({
      param,
      mode,
      custom_value: mode === 'DIRECT_VALUE' ? parseFloat(directVal) : null,
      offset_delta: mode === 'OFFSET' ? parseFloat(offsetDelta) : null,
      stuck_cycles: mode === 'STUCK' ? parseInt(stuckCycles, 10) : null,
    });
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 2000,
        background: 'rgba(5, 8, 17, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '520px',
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: '6px',
          boxShadow: '0 16px 32px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid #30363d',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: '#161b22',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={16} color="#58a6ff" />
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f0f6fc' }}>
              Custom Fault Injector
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8b949e',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Target Station Info */}
          <div
            style={{
              padding: '8px 10px',
              borderRadius: '4px',
              background: '#0d1117',
              border: '1px solid #30363d',
              fontSize: '0.72rem',
              color: '#8b949e',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>Target: <strong style={{ color: '#f0f6fc' }}>{selectedStation?.station_name || 'Selected AWS'}</strong></span>
            <span>Current: {currentTemp.toFixed(1)}°C | {currentPres.toFixed(1)} hPa | {currentHumi.toFixed(1)}%</span>
          </div>

          {/* 1. Select Parameter */}
          <div>
            <label style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              1. TARGET SENSOR PARAMETER
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
              <button
                type="button"
                className={`btn-ghost ${param === 'temperature' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '6px 4px' }}
                onClick={() => { setParam('temperature'); setDirectVal(68.0); setOffsetDelta(18.0); }}
              >
                <Thermometer size={13} /> Temp
              </button>
              <button
                type="button"
                className={`btn-ghost ${param === 'pressure' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '6px 4px' }}
                onClick={() => { setParam('pressure'); setDirectVal(850.0); setOffsetDelta(-45.0); }}
              >
                <Gauge size={13} /> Pres
              </button>
              <button
                type="button"
                className={`btn-ghost ${param === 'humidity' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '6px 4px' }}
                onClick={() => { setParam('humidity'); setDirectVal(105.0); setOffsetDelta(40.0); }}
              >
                <Droplets size={13} /> Humi
              </button>
              <button
                type="button"
                className={`btn-ghost ${param === 'battery' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '6px 4px' }}
                onClick={() => { setParam('battery'); setDirectVal(10.6); setOffsetDelta(-2.0); }}
              >
                <BatteryCharging size={13} /> Battery
              </button>
            </div>
          </div>

          {/* 2. Select Failure / Injection Mode */}
          <div>
            <label style={{ fontSize: '0.7rem', color: '#8b949e', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              2. INJECTION MECHANISM
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
              <button
                type="button"
                className={`btn-ghost ${mode === 'DIRECT_VALUE' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('DIRECT_VALUE')}
              >
                Direct Value
              </button>
              <button
                type="button"
                className={`btn-ghost ${mode === 'OFFSET' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('OFFSET')}
              >
                Delta Offset
              </button>
              <button
                type="button"
                className={`btn-ghost ${mode === 'STUCK' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('STUCK')}
              >
                Freeze / Stuck
              </button>
              <button
                type="button"
                className={`btn-ghost ${mode === 'INVERSION' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('INVERSION')}
              >
                Td &gt; T Inversion
              </button>
              <button
                type="button"
                className={`btn-ghost ${mode === 'DROPOUT' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('DROPOUT')}
              >
                Signal Dropout
              </button>
              <button
                type="button"
                className={`btn-ghost ${mode === 'LOW_BATTERY' ? 'btn-ghost-active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('LOW_BATTERY')}
              >
                Battery Sag (&lt;11.2V)
              </button>
            </div>
          </div>

          {/* 3. Value Input Controls */}
          <div style={{ background: '#0d1117', padding: '10px 12px', borderRadius: '4px', border: '1px solid #30363d' }}>
            {mode === 'DIRECT_VALUE' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.72rem', color: '#8b949e' }}>
                  <span>Specify Numerical Value:</span>
                  <strong style={{ color: '#58a6ff', fontFamily: 'var(--font-mono)' }}>
                    {directVal} {param === 'temperature' ? '°C' : (param === 'pressure' ? 'hPa' : (param === 'battery' ? 'V' : '%'))}
                  </strong>
                </div>
                <input
                  type="number"
                  step="0.1"
                  value={directVal}
                  onChange={(e) => setDirectVal(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#161b22',
                    border: '1px solid #30363d',
                    borderRadius: '4px',
                    padding: '6px 10px',
                    color: '#f0f6fc',
                    fontSize: '0.85rem',
                    outline: 'none',
                  }}
                />
              </div>
            )}

            {mode === 'OFFSET' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.72rem', color: '#8b949e' }}>
                  <span>Specify Rate-of-Change Delta Offset (+/-):</span>
                  <strong style={{ color: '#d29922', fontFamily: 'var(--font-mono)' }}>
                    {offsetDelta > 0 ? `+${offsetDelta}` : offsetDelta} {param === 'temperature' ? '°C' : (param === 'pressure' ? 'hPa' : '%')}
                  </strong>
                </div>
                <input
                  type="range"
                  min={param === 'pressure' ? -100 : -40}
                  max={param === 'pressure' ? 100 : 40}
                  step={0.5}
                  value={offsetDelta}
                  onChange={(e) => setOffsetDelta(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: '#d29922' }}
                />
                <input
                  type="number"
                  step="0.1"
                  value={offsetDelta}
                  onChange={(e) => setOffsetDelta(parseFloat(e.target.value))}
                  style={{
                    width: '100%',
                    marginTop: '6px',
                    background: '#161b22',
                    border: '1px solid #30363d',
                    borderRadius: '4px',
                    padding: '4px 8px',
                    color: '#f0f6fc',
                    fontSize: '0.8rem',
                    outline: 'none',
                  }}
                />
              </div>
            )}

            {mode === 'STUCK' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.72rem', color: '#8b949e' }}>
                  <span>Consecutive Frozen Cycles:</span>
                  <strong style={{ color: '#f85149', fontFamily: 'var(--font-mono)' }}>{stuckCycles} readings (Threshold = 6)</strong>
                </div>
                <input
                  type="range"
                  min={4}
                  max={24}
                  value={stuckCycles}
                  onChange={(e) => setStuckCycles(parseInt(e.target.value, 10))}
                  style={{ width: '100%', accentColor: '#f85149' }}
                />
              </div>
            )}

            {mode === 'INVERSION' && (
              <div style={{ fontSize: '0.72rem', color: '#c9d1d9', lineHeight: '1.4' }}>
                <strong style={{ color: '#f85149' }}>Thermodynamic Invariant Violation:</strong> Forces dew point temperature to exceed air temperature (Dew Point &gt; Air Temp), violating the Clausius-Clapeyron equation and triggering deterministic Tier 1 rule and TreeSHAP attribution.
              </div>
            )}

            {mode === 'DROPOUT' && (
              <div style={{ fontSize: '0.72rem', color: '#c9d1d9', lineHeight: '1.4' }}>
                <strong style={{ color: '#8b949e' }}>Telemetry Packet Loss:</strong> Simulates transmitter outage or solar battery exhaustion causing missing observation values (null).
              </div>
            )}

            {mode === 'LOW_BATTERY' && (
              <div style={{ fontSize: '0.72rem', color: '#c9d1d9', lineHeight: '1.4' }}>
                <strong style={{ color: '#f85149' }}>ADC Excitation Sag:</strong> Drops battery voltage to 10.7V (below critical 11.2V threshold), causing ADC reference distortion and artificial negative sensor spikes.
              </div>
            )}
          </div>

          {/* Submit / Action Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '2px' }}>
            <button
              type="button"
              className="btn-ghost"
              onClick={onClose}
              style={{ padding: '5px 12px', fontSize: '0.75rem' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{
                padding: '5px 14px',
                fontSize: '0.75rem',
                background: '#1f6feb',
              }}
            >
              Inject Fault &amp; Run Pipeline
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
