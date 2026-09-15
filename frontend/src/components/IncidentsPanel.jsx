import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  UserCheck,
  RefreshCw,
  FileText,
  Sliders
} from 'lucide-react';

export default function IncidentsPanel({ station, latestResult, apiBase = '' }) {
  const [healthCard, setHealthCard] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  const stationId = station?.station_id || '42182099999';

  // Fetch health card, open incidents, and audit logs
  const fetchData = async () => {
    if (!stationId) return;
    setLoading(true);
    try {
      const [healthRes, incRes, auditRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/sensor-health/${stationId}`),
        fetch(`${apiBase}/api/v1/incidents?station_id=${stationId}`),
        fetch(`${apiBase}/api/v1/audit-logs?station_id=${stationId}&limit=10`)
      ]);

      if (healthRes.ok) {
        const hData = await healthRes.json();
        setHealthCard(hData);
      }
      if (incRes.ok) {
        const incData = await incRes.json();
        setIncidents(incData);
        if (incData.length > 0) {
          setSelectedIncident(incData[0]);
          fetchTimeline(incData[0].incident_id);
        } else {
          setSelectedIncident(null);
          setTimeline([]);
        }
      }
      if (auditRes.ok) {
        const auditData = await auditRes.json();
        setAuditLogs(auditData);
      }
    } catch (err) {
      console.error('Error fetching incident data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTimeline = async (incId) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/incidents/${incId}/timeline`);
      if (res.ok) {
        const data = await res.json();
        setTimeline(data);
      }
    } catch (err) {
      console.error('Error fetching incident timeline:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [stationId, latestResult]);

  // Operator Actions
  const handleAcknowledge = async (incId) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/incidents/${incId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operator_name: 'CHIEF_OPERATOR' })
      });
      if (res.ok) {
        setActionMessage('Incident acknowledged successfully.');
        fetchData();
        setTimeout(() => setActionMessage(''), 3000);
      }
    } catch (err) {
      console.error('Error acknowledging incident:', err);
    }
  };

  const handleResolve = async (incId, reason = 'OPERATOR_RESOLVED') => {
    try {
      const res = await fetch(`${apiBase}/api/v1/incidents/${incId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason, operator_name: 'CHIEF_OPERATOR' })
      });
      if (res.ok) {
        setActionMessage(`Incident resolved: ${reason}`);
        fetchData();
        setTimeout(() => setActionMessage(''), 3000);
      }
    } catch (err) {
      console.error('Error resolving incident:', err);
    }
  };

  const handleOperatorFeedback = async (action) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/operator/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_id: stationId,
          operator_action: action,
          incident_id: selectedIncident?.incident_id,
          reason: `Operator action ${action} submitted via HUD controls.`,
          operator_name: 'CHIEF_OPERATOR'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setActionMessage(`Feedback queued into recalibration queue (${data.candidate_id})`);
        fetchData();
        setTimeout(() => setActionMessage(''), 4000);
      }
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  const currentInc = selectedIncident || (latestResult?.incident ? latestResult.incident : null);
  const evidenceSummary = latestResult?.incident?.evidence_summary_json 
    ? (typeof latestResult.incident.evidence_summary_json === 'string' 
        ? JSON.parse(latestResult.incident.evidence_summary_json) 
        : latestResult.incident.evidence_summary_json)
    : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.8rem' }}>
      
      {actionMessage && (
        <div
          style={{
            padding: '8px 12px',
            background: 'rgba(63, 185, 80, 0.15)',
            border: '1px solid #3fb950',
            borderRadius: '6px',
            color: '#3fb950',
            fontWeight: 600,
            fontSize: '0.75rem'
          }}
        >
          {actionMessage}
        </div>
      )}


      {/* 1. Sensor Health Card Summary */}
      {healthCard && (
        <div
          className="glass-panel"
          style={{
            padding: '12px 14px',
            borderRadius: '6px',
            background: '#161b22',
            border: '1px solid #30363d'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={16} color="#58a6ff" />
              <span style={{ fontWeight: 700, color: '#f0f6fc', fontSize: '0.85rem' }}>
                Operational State Machine Card
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                onClick={fetchData}
                className="btn-ghost"
                style={{ padding: '2px 6px', fontSize: '0.68rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                title="Refresh State"
              >
                <RefreshCw size={11} className={loading ? 'spin' : ''} />
              </button>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background:
                    healthCard.current_state === 'HEALTHY'
                      ? 'rgba(63, 185, 80, 0.2)'
                      : healthCard.current_state === 'RECOVERING'
                      ? 'rgba(88, 166, 255, 0.2)'
                      : 'rgba(248, 81, 73, 0.2)',
                  color:
                    healthCard.current_state === 'HEALTHY'
                      ? '#3fb950'
                      : healthCard.current_state === 'RECOVERING'
                      ? '#58a6ff'
                      : '#f85149',
                  border: '1px solid currentColor'
                }}
              >
                STATE: {healthCard.current_state}
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '8px' }}>
            <div style={{ background: '#0d1117', padding: '8px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ fontSize: '0.65rem', color: '#8b949e' }}>COMMUNICATION</div>
              <div style={{ fontWeight: 700, color: healthCard.communication_status === 'HEALTHY' ? '#3fb950' : '#f85149' }}>
                {healthCard.communication_status}
              </div>
            </div>

            <div style={{ background: '#0d1117', padding: '8px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ fontSize: '0.65rem', color: '#8b949e' }}>OPEN INCIDENTS</div>
              <div style={{ fontWeight: 700, color: healthCard.open_incidents_count > 0 ? '#f85149' : '#3fb950' }}>
                {healthCard.open_incidents_count} Active
              </div>
            </div>

            <div style={{ background: '#0d1117', padding: '8px', borderRadius: '4px', border: '1px solid #21262d' }}>
              <div style={{ fontSize: '0.65rem', color: '#8b949e' }}>TREND</div>
              <div style={{ fontWeight: 700, color: healthCard.trend === 'STABLE' ? '#3fb950' : '#d29922' }}>
                {healthCard.trend}
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.72rem', color: '#c9d1d9', background: '#0d1117', padding: '8px', borderRadius: '4px' }}>
            <span style={{ fontWeight: 600, color: '#58a6ff' }}>Reason: </span>
            {healthCard.reason}
          </div>
        </div>
      )}

      {/* 2. Open Operational Incident Details & Operator Controls */}
      <div
        className="glass-panel"
        style={{
          padding: '12px 14px',
          borderRadius: '6px',
          background: '#161b22',
          border: '1px solid #30363d'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={16} color={currentInc ? '#f85149' : '#3fb950'} />
            <span style={{ fontWeight: 700, color: '#f0f6fc', fontSize: '0.85rem' }}>
              {currentInc ? `Incident: ${currentInc.incident_id}` : 'No Active Incident'}
            </span>
          </div>

          {currentInc && (
            <div style={{ display: 'flex', gap: '6px' }}>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: '#da3633',
                  color: '#ffffff'
                }}
              >
                {currentInc.status}
              </span>
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: '#21262d',
                  color: '#d29922',
                  border: '1px solid #d29922'
                }}
              >
                {currentInc.severity}
              </span>
            </div>
          )}
        </div>

        {currentInc ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
              <div style={{ background: '#0d1117', padding: '8px', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.65rem', color: '#8b949e' }}>AFFECTED PARAMETER</div>
                <div style={{ fontWeight: 700, color: '#58a6ff' }}>{currentInc.affected_parameter}</div>
              </div>
              <div style={{ background: '#0d1117', padding: '8px', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.65rem', color: '#8b949e' }}>ROOT CAUSE</div>
                <div style={{ fontWeight: 700, color: '#f0f6fc' }}>{currentInc.root_cause}</div>
              </div>
            </div>

            {/* "Why is this alert active?" Evidence Summary */}
            <div
              style={{
                background: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '4px',
                padding: '10px',
                marginBottom: '10px'
              }}
            >
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#58a6ff', marginBottom: '4px' }}>
                WHY IS THIS ALERT ACTIVE?
              </div>
              <div style={{ fontSize: '0.72rem', color: '#c9d1d9', marginBottom: '6px' }}>
                {evidenceSummary?.why_alert_active || 'Temperature sensor remains anomalous across consecutive readings. Physical & spatial verification checks engaged.'}
              </div>

              {evidenceSummary?.supporting_evidence?.length > 0 && (
                <div>
                  <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#f85149', marginTop: '4px' }}>
                    SUPPORTING EVIDENCE:
                  </div>
                  <ul style={{ margin: '2px 0 0 14px', padding: 0, fontSize: '0.68rem', color: '#8b949e' }}>
                    {evidenceSummary.supporting_evidence.map((ev, i) => (
                      <li key={i}>{ev}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Operator Workflow Action Buttons */}
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#8b949e', marginBottom: '6px' }}>
              OPERATOR WORKFLOW ACTIONS
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              <button
                onClick={() => handleAcknowledge(currentInc.incident_id)}
                className="btn-ghost"
                style={{ fontSize: '0.7rem', padding: '4px 8px', background: '#21262d', color: '#f0f6fc' }}
              >
                <UserCheck size={12} /> Acknowledge
              </button>

              <button
                onClick={() => handleOperatorFeedback('CONFIRM_ANOMALY')}
                className="btn-ghost"
                style={{ fontSize: '0.7rem', padding: '4px 8px', background: 'rgba(248, 81, 73, 0.15)', color: '#f85149', border: '1px solid #f85149' }}
              >
                <CheckCircle2 size={12} /> Confirm Anomaly
              </button>

              <button
                onClick={() => handleOperatorFeedback('REJECT_ANOMALY')}
                className="btn-ghost"
                style={{ fontSize: '0.7rem', padding: '4px 8px', background: '#21262d', color: '#d29922' }}
              >
                <XCircle size={12} /> Reject (False Alarm)
              </button>

              <button
                onClick={() => handleResolve(currentInc.incident_id, 'OPERATOR_RESOLVED')}
                className="btn-primary"
                style={{ fontSize: '0.7rem', padding: '4px 8px' }}
              >
                Resolve Incident
              </button>
            </div>
          </div>
        ) : (
          <div style={{ color: '#8b949e', padding: '12px', textAlign: 'center', background: '#0d1117', borderRadius: '4px' }}>
            Station sensors operating within normal climatological boundaries. No open incidents.
          </div>
        )}
      </div>

      {/* 3. Incident Evolution Timeline */}
      {timeline.length > 0 && (
        <div
          className="glass-panel"
          style={{
            padding: '12px 14px',
            borderRadius: '6px',
            background: '#161b22',
            border: '1px solid #30363d'
          }}
        >
          <div style={{ fontWeight: 700, color: '#f0f6fc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={14} color="#58a6ff" />
            Incident Evolution Timeline
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {timeline.map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                  background: '#0d1117',
                  padding: '6px 8px',
                  borderRadius: '4px',
                  borderLeft: '3px solid #58a6ff'
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: '#8b949e', whiteSpace: 'nowrap' }}>
                  {item.timestamp ? item.timestamp.substring(11, 19) : ''}
                </span>
                <div>
                  <span style={{ fontWeight: 700, color: '#f0f6fc', fontSize: '0.7rem', marginRight: '6px' }}>
                    {item.event_type}
                  </span>
                  <span style={{ color: '#8b949e', fontSize: '0.7rem' }}>{item.description}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. System Operational Audit Logs */}
      {auditLogs.length > 0 && (
        <div
          className="glass-panel"
          style={{
            padding: '12px 14px',
            borderRadius: '6px',
            background: '#161b22',
            border: '1px solid #30363d'
          }}
        >
          <div style={{ fontWeight: 700, color: '#f0f6fc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FileText size={14} color="#3fb950" />
            Operational Audit Log
          </div>

          <div style={{ maxHeight: '160px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {auditLogs.map((log, idx) => (
              <div key={idx} style={{ fontSize: '0.68rem', color: '#8b949e', background: '#0d1117', padding: '4px 6px', borderRadius: '4px' }}>
                <span style={{ color: '#58a6ff', fontWeight: 600 }}>[{log.actor}]</span> {log.event_type}: {log.reason}
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
