import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { Thermometer, Gauge, Droplets, BatteryCharging, ShieldCheck } from 'lucide-react';

// Client-side fallback thermodynamic computations if backend features are still streaming
function computeClientDewPoint(temp, humi) {
  if (temp == null || humi == null) return null;
  const a = 17.27;
  const b = 237.7;
  const alpha = ((a * temp) / (b + temp)) + Math.log(Math.max(0.01, humi) / 100.0);
  return (b * alpha) / (a - alpha);
}

function computeClientVaporPressure(temp, humi) {
  if (temp == null || humi == null) return null;
  const es = 6.112 * Math.exp((17.67 * temp) / (temp + 243.5));
  return (humi / 100.0) * es;
}

function computeClientHeatIndex(temp, humi) {
  if (temp == null || humi == null) return null;
  if (temp < 27.0 || humi < 40.0) return temp;
  // Rothfusz regression
  const T = temp * 1.8 + 32.0;
  const R = humi;
  let hi = -42.379 + 2.04901523 * T + 10.14333127 * R - 0.22475541 * T * R
    - 0.00683783 * T * T - 0.05481717 * R * R + 0.00122874 * T * T * R
    + 0.00085282 * T * R * R - 0.00000199 * T * T * R * R;
  return (hi - 32.0) / 1.8;
}

export default function TelemetryHUD({
  station,
  telemetry,
  latestResult,
  showCorrected,
  setShowCorrected,
}) {
  const [activeParam, setActiveParam] = useState('temperature');

  if (!station) {
    return (
      <div className="glass-card" style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
        Select an AWS station to inspect sensor streams.
      </div>
    );
  }

  const rawTemp = latestResult?.raw_reading?.temperature ?? (telemetry.length ? telemetry[telemetry.length - 1]?.temperature : 28.0);
  const rawPres = latestResult?.raw_reading?.pressure ?? (telemetry.length ? telemetry[telemetry.length - 1]?.pressure : 1012.0);
  const rawHumi = latestResult?.raw_reading?.humidity ?? (telemetry.length ? telemetry[telemetry.length - 1]?.humidity : 60.0);
  const rawBatt = latestResult?.raw_reading?.battery_voltage ?? 12.6;
  const isAnomaly = latestResult?.final_anomaly ?? false;

  // Secondary metrics from backend engineered_features, or fallback calculation
  const dewPoint = latestResult?.engineered_features?.dew_point ?? computeClientDewPoint(rawTemp, rawHumi);
  const vaporPres = latestResult?.engineered_features?.vap_pres ?? computeClientVaporPressure(rawTemp, rawHumi);
  const heatIndex = latestResult?.engineered_features?.heat_idx ?? computeClientHeatIndex(rawTemp, rawHumi);

  // WMO QC Flag (Biju et al., 2012)
  const qcFlag = latestResult?.wmo_qc_flag ?? 0;
  const qcLabels = ['Flag 0: Good', 'Flag 1: Suspect', 'Flag 2: Erroneous', 'Flag 3: Missing', 'Flag 4: Imputed'];
  const qcColors = ['#00e599', '#ffb800', '#ff3366', '#94a3b8', '#00f0ff'];

  // Format telemetry series for chart
  const chartData = telemetry.map((item, idx) => {
    const isLast = idx === telemetry.length - 1;
    const tVal = (isLast && latestResult?.raw_reading?.temperature !== undefined)
      ? latestResult.raw_reading.temperature
      : item.temperature;
    const pVal = (isLast && latestResult?.raw_reading?.pressure !== undefined)
      ? latestResult.raw_reading.pressure
      : item.pressure;
    const hVal = (isLast && latestResult?.raw_reading?.humidity !== undefined)
      ? latestResult.raw_reading.humidity
      : item.humidity;

    const corrT = (isLast && latestResult?.corrected_telemetry?.applied)
      ? latestResult.corrected_telemetry.temp
      : tVal;

    return {
      time: item.timestamp.includes('T') ? item.timestamp.split('T')[1].slice(0, 5) : item.timestamp.slice(-5),
      temperature: tVal,
      pressure: pVal,
      humidity: hVal,
      corrected_temp: corrT,
      is_anomaly: isLast && isAnomaly,
    };
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Sensor Metric HUD Cards (Completely removed latency, replaced with Battery / WMO Power card) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
        {/* Temperature Card */}
        <div
          className={`glass-card metric-card ${activeParam === 'temperature' ? 'metric-card-active' : ''}`}
          onClick={() => setActiveParam('temperature')}
        >
          <div className="metric-header">
            <span className="metric-label">TEMPERATURE</span>
            <Thermometer size={14} color="#00f0ff" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">
              {rawTemp != null ? rawTemp.toFixed(1) : 'N/A'}
            </span>
            <span className="metric-unit">°C</span>
          </div>
          <div className="metric-subtext">
            Dew Pt: {dewPoint != null ? `${dewPoint.toFixed(1)}°C` : '--'}
          </div>
        </div>

        {/* Pressure Card */}
        <div
          className={`glass-card metric-card ${activeParam === 'pressure' ? 'metric-card-active' : ''}`}
          onClick={() => setActiveParam('pressure')}
        >
          <div className="metric-header">
            <span className="metric-label">PRESSURE</span>
            <Gauge size={14} color="#a855f7" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">
              {rawPres != null ? rawPres.toFixed(1) : 'N/A'}
            </span>
            <span className="metric-unit">hPa</span>
          </div>
          <div className="metric-subtext">
            Vapor: {vaporPres != null ? `${vaporPres.toFixed(1)} hPa` : '--'}
          </div>
        </div>

        {/* Humidity Card */}
        <div
          className={`glass-card metric-card ${activeParam === 'humidity' ? 'metric-card-active' : ''}`}
          onClick={() => setActiveParam('humidity')}
        >
          <div className="metric-header">
            <span className="metric-label">HUMIDITY</span>
            <Droplets size={14} color="#00e599" />
          </div>
          <div className="metric-value-row">
            <span className="metric-number">
              {rawHumi != null ? rawHumi.toFixed(1) : 'N/A'}
            </span>
            <span className="metric-unit">%</span>
          </div>
          <div className="metric-subtext">
            Heat Idx: {heatIndex != null ? `${heatIndex.toFixed(1)}°C` : '--'}
          </div>
        </div>

        {/* Operational Battery & WMO Integrity Card (Replaces Latency per User Request) */}
        <div
          className="glass-card metric-card"
          style={{
            borderColor: rawBatt < 11.2 ? 'rgba(255, 51, 102, 0.4)' : 'rgba(255, 255, 255, 0.08)',
          }}
        >
          <div className="metric-header">
            <span className="metric-label">STATION BATTERY</span>
            <BatteryCharging size={14} color={rawBatt < 11.2 ? '#ff3366' : '#00e599'} />
          </div>
          <div className="metric-value-row">
            <span className="metric-number" style={{ color: rawBatt < 11.2 ? '#ff3366' : '#00e599' }}>
              {rawBatt.toFixed(1)}
            </span>
            <span className="metric-unit">V</span>
          </div>
          <div className="metric-subtext" style={{ color: qcColors[qcFlag] }}>
            {rawBatt < 11.2 ? 'Low (< 11.2V Sag)' : qcLabels[qcFlag]}
          </div>
        </div>
      </div>

      {/* Continuous Telemetry Chart */}
      <div className="glass-card" style={{ padding: '16px', position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>
              Real-Time Sensor Ingestion Stream
            </span>
            <span style={{ fontSize: '0.72rem', color: '#64748b', marginLeft: '8px' }}>
              ({activeParam.toUpperCase()} / 48-Hour Historical Window)
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showCorrected}
                onChange={(e) => setShowCorrected(e.target.checked)}
                style={{ accentColor: '#00f0ff' }}
              />
              Show Kalman Self-Healing
            </label>
          </div>
        </div>

        <div style={{ width: '100%', height: '220px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <XAxis
                dataKey="time"
                stroke="#475569"
                fontSize={10}
                tickLine={false}
                interval={Math.max(1, Math.floor(chartData.length / 8))}
              />
              <YAxis
                stroke="#475569"
                fontSize={10}
                tickLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(8, 14, 26, 0.95)',
                  border: '1px solid rgba(0, 240, 255, 0.25)',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#f8fafc',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />

              {activeParam === 'temperature' && (
                <Line
                  type="monotone"
                  dataKey="temperature"
                  name="Raw Temp (°C)"
                  stroke="#00f0ff"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#00f0ff' }}
                  activeDot={{ r: 5 }}
                />
              )}

              {activeParam === 'temperature' && showCorrected && (
                <Line
                  type="monotone"
                  dataKey="corrected_temp"
                  name="Kalman Imputed (°C)"
                  stroke="#a855f7"
                  strokeWidth={1.8}
                  strokeDasharray="4 4"
                  dot={false}
                />
              )}

              {activeParam === 'pressure' && (
                <Line
                  type="monotone"
                  dataKey="pressure"
                  name="Pressure (hPa)"
                  stroke="#a855f7"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#a855f7' }}
                  activeDot={{ r: 5 }}
                />
              )}

              {activeParam === 'humidity' && (
                <Line
                  type="monotone"
                  dataKey="humidity"
                  name="Relative Humidity (%)"
                  stroke="#00e599"
                  strokeWidth={2}
                  dot={{ r: 2, fill: '#00e599' }}
                  activeDot={{ r: 5 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
