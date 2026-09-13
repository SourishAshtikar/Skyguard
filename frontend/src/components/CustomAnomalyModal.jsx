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
          background: '#090e1a',
          border: '1px solid rgba(0, 240, 255, 0.25)',
          borderRadius: '12px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 240, 255, 0.1)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(13, 21, 38, 0.6)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={18} color="#00f0ff" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
              Custom User Anomaly Injector
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Target Station Info */}
          <div
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'rgba(0, 240, 255, 0.05)',
              border: '1px solid rgba(0, 240, 255, 0.15)',
              fontSize: '0.75rem',
              color: '#cbd5e1',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>Target Station: <strong style={{ color: '#00f0ff' }}>{selectedStation?.station_name || 'Selected AWS'}</strong></span>
            <span>Current: {currentTemp.toFixed(1)}°C | {currentPres.toFixed(1)} hPa | {currentHumi.toFixed(1)}%</span>
          </div>

          {/* 1. Select Parameter */}
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              1. TARGET SENSOR PARAMETER
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
              <button
                type="button"
                className={`filter-pill ${param === 'temperature' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '8px 4px' }}
                onClick={() => { setParam('temperature'); setDirectVal(68.0); setOffsetDelta(18.0); }}
              >
                <Thermometer size={13} color="#00f0ff" /> Temp
              </button>
              <button
                type="button"
                className={`filter-pill ${param === 'pressure' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '8px 4px' }}
                onClick={() => { setParam('pressure'); setDirectVal(850.0); setOffsetDelta(-45.0); }}
              >
                <Gauge size={13} color="#a855f7" /> Pres
              </button>
              <button
                type="button"
                className={`filter-pill ${param === 'humidity' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '8px 4px' }}
                onClick={() => { setParam('humidity'); setDirectVal(105.0); setOffsetDelta(40.0); }}
              >
                <Droplets size={13} color="#00e599" /> Humi
              </button>
              <button
                type="button"
                className={`filter-pill ${param === 'battery' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center', padding: '8px 4px' }}
                onClick={() => { setParam('battery'); setDirectVal(10.6); setOffsetDelta(-2.0); }}
              >
                <BatteryCharging size={13} color="#ffb800" /> Battery
              </button>
            </div>
          </div>

          {/* 2. Select Failure / Injection Mode */}
          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              2. INJECTION MODE / MECHANISM
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              <button
                type="button"
                className={`filter-pill ${mode === 'DIRECT_VALUE' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('DIRECT_VALUE')}
              >
                Direct Value
              </button>
              <button
                type="button"
                className={`filter-pill ${mode === 'OFFSET' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('OFFSET')}
              >
                Delta Offset
              </button>
              <button
                type="button"
                className={`filter-pill ${mode === 'STUCK' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('STUCK')}
              >
                Freeze / Stuck
              </button>
              <button
                type="button"
                className={`filter-pill ${mode === 'INVERSION' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('INVERSION')}
              >
                Td &gt; T Inversion
              </button>
              <button
                type="button"
                className={`filter-pill ${mode === 'DROPOUT' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('DROPOUT')}
              >
                Signal Dropout
              </button>
              <button
                type="button"
                className={`filter-pill ${mode === 'LOW_BATTERY' ? 'active' : ''}`}
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => setMode('LOW_BATTERY')}
              >
                Battery Sag (&lt;11.2V)
              </button>
            </div>
          </div>

          {/* 3. Value Input Controls (Dynamic based on selected mode) */}
          <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            {mode === 'DIRECT_VALUE' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.75rem', color: '#cbd5e1' }}>
                  <span>Specify Absolute Numerical Value:</span>
                  <strong style={{ color: '#00f0ff', fontSize: '0.9rem' }}>
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
                    background: '#070b12',
                    border: '1px solid rgba(0, 240, 255, 0.3)',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    color: '#f8fafc',
                    fontSize: '0.9rem',
                    outline: 'none',
                  }}
                />
                <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '6px' }}>
                  Tip: WMO Guide 8 range limits: Temp [-40°C, 55°C], Pressure [500, 1080 hPa], Humidity [0, 100%].
                </div>
              </div>
            )}

            {mode === 'OFFSET' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.75rem', color: '#cbd5e1' }}>
                  <span>Specify Rate-of-Change Delta Offset (+/-):</span>
                  <strong style={{ color: '#ffb800', fontSize: '0.9rem' }}>
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
                  style={{ width: '100%', accentColor: '#ffb800' }}
                />
                <input
                  type="number"
                  step="0.1"
                  value={offsetDelta}
                  onChange={(e) => setOffsetDelta(parseFloat(e.target.value))}
                  style={{
                    width: '100%',
                    marginTop: '8px',
                    background: '#070b12',
                    border: '1px solid rgba(255, 184, 0, 0.3)',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    color: '#f8fafc',
                    fontSize: '0.85rem',
                    outline: 'none',
                  }}
                />
              </div>
            )}

            {mode === 'STUCK' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.75rem', color: '#cbd5e1' }}>
                  <span>Consecutive Frozen Cycles:</span>
                  <strong style={{ color: '#ff3366', fontSize: '0.9rem' }}>{stuckCycles} readings (Limit = 6)</strong>
                </div>
                <input
                  type="range"
                  min={4}
                  max={24}
                  value={stuckCycles}
                  onChange={(e) => setStuckCycles(parseInt(e.target.value, 10))}
                  style={{ width: '100%', accentColor: '#ff3366' }}
                />
                <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '6px' }}>
                  Simulates mechanical potentiometer freeze, transducer debris blockage, or ADC bus latchup.
                </div>
              </div>
            )}

            {mode === 'INVERSION' && (
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                <strong style={{ color: '#ff3366' }}>Thermodynamic Invariant Violation:</strong> Forces dew point temperature to exceed air temperature (Dew Point &gt; Air Temp), violating the Clausius-Clapeyron equation and triggering instant Tier 1 and TreeSHAP attribution.
              </div>
            )}

            {mode === 'DROPOUT' && (
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                <strong style={{ color: '#94a3b8' }}>Packet Loss / Signal Dropout:</strong> Simulates INSAT-3A DCP burst transmitter failure or solar battery exhaustion, causing missing telemetry values (`null`).
              </div>
            )}

            {mode === 'LOW_BATTERY' && (
              <div style={{ fontSize: '0.75rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                <strong style={{ color: '#ff3366' }}>Ranalkar et al. (2012) ADC Excitation Sag:</strong> Drops battery voltage to 10.7V (below critical 11.2V threshold), causing ADC reference distortion and artificial negative sensor spikes.
              </div>
            )}
          </div>

          {/* Submit / Action Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              style={{ padding: '8px 16px', fontSize: '0.8rem' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{
                padding: '8px 18px',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: 'linear-gradient(135deg, #ff3366 0%, #a855f7 100%)',
                boxShadow: '0 0 16px rgba(255, 51, 102, 0.4)',
              }}
            >
              <Sparkles size={14} />
              Inject Custom Anomaly &amp; Run Pipeline
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
