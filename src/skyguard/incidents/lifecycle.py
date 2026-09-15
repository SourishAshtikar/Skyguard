"""
SkyGuard AI — Incident Lifecycle Manager
Manages the complete lifecycle of operational incidents (NORMAL -> SUSPECTED -> CONFIRMED ->
ACTIVE -> RECOVERING -> RESOLVED) with full evidence aggregation, timeline tracking,
and operator acknowledgement support.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from skyguard.config.settings import SETTINGS
from skyguard.db.database import DB


class IncidentStatus:
    NORMAL = "NORMAL"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    RECOVERING = "RECOVERING"
    RESOLVED = "RESOLVED"


class IncidentSeverity:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentLifecycleManager:
    """Manages creation, escalation, timeline tracking, and resolution of incidents."""

    def process_anomaly_event(
        self,
        station_id: str,
        affected_parameter: str,
        is_anomaly: bool,
        root_cause: str,
        confidence: float,
        evidence: Dict[str, Any],
        reading_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Processes an observation event, updating existing active incident or creating a new one.
        
        Returns updated/created Incident object dict, or None if reading is normal and no active incident.
        """
        now = reading_time or datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Find existing open incident for station and parameter
        active_incident = self._find_active_incident(station_id, affected_parameter)

        if is_anomaly:
            if not active_incident:
                # 1. Create SUSPECTED incident for single anomalous observation (EVENT -> INCIDENT transition)
                incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
                severity = self._compute_severity(confidence, event_count=1, evidence=evidence)
                
                evidence_summary = self._build_evidence_summary(evidence, active=True)
                
                incident = {
                    "incident_id": incident_id,
                    "station_id": station_id,
                    "affected_parameter": affected_parameter,
                    "first_seen": now_iso,
                    "last_seen": now_iso,
                    "duration_seconds": 0.0,
                    "status": IncidentStatus.SUSPECTED,
                    "severity": severity,
                    "event_count": 1,
                    "evidence_summary_json": json.dumps(evidence_summary),
                    "root_cause": root_cause,
                    "confidence": confidence,
                    "acknowledgement_status": "UNACKNOWLEDGED",
                    "acknowledged_by": None,
                    "acknowledged_at": None,
                    "resolution_reason": None,
                    "resolved_at": None,
                    "created_at": now_iso,
                    "updated_at": now_iso
                }
                self._save_incident(incident)
                self._add_timeline_entry(incident_id, now_iso, "FIRST_ANOMALY", f"First anomalous observation detected for {affected_parameter}.", evidence)
                DB.log_audit(station_id, "INCIDENT_CREATED", f"Created incident {incident_id} ({affected_parameter})", new_state=IncidentStatus.SUSPECTED)
                return incident

            else:
                # 2. Existing active incident: Update count, last_seen, severity, and status
                inc_id = active_incident["incident_id"]
                event_count = active_incident["event_count"] + 1
                try:
                    first_seen_dt = datetime.fromisoformat(active_incident["first_seen"])
                    duration = (now - first_seen_dt).total_seconds()
                except Exception:
                    duration = 0.0

                old_status = active_incident["status"]
                new_status = old_status

                if old_status in [IncidentStatus.SUSPECTED, IncidentStatus.RECOVERING] and event_count >= SETTINGS.confirmation_count:
                    new_status = IncidentStatus.CONFIRMED if old_status == IncidentStatus.SUSPECTED else IncidentStatus.ACTIVE
                    self._add_timeline_entry(inc_id, now_iso, "INCIDENT_CONFIRMED", f"Incident confirmed after {event_count} consecutive anomalous observations.", evidence)

                if new_status == IncidentStatus.CONFIRMED and event_count > SETTINGS.confirmation_count:
                    new_status = IncidentStatus.ACTIVE

                new_severity = self._compute_severity(confidence, event_count, evidence)
                if new_severity != active_incident["severity"]:
                    self._add_timeline_entry(inc_id, now_iso, "SEVERITY_ESCALATED", f"Severity escalated from {active_incident['severity']} to {new_severity}.", evidence)

                evidence_summary = self._build_evidence_summary(evidence, active=True)

                active_incident.update({
                    "last_seen": now_iso,
                    "duration_seconds": duration,
                    "status": new_status,
                    "severity": new_severity,
                    "event_count": event_count,
                    "evidence_summary_json": json.dumps(evidence_summary),
                    "confidence": max(active_incident["confidence"], confidence),
                    "updated_at": now_iso
                })
                self._save_incident(active_incident)
                return active_incident

        else:
            # Healthy reading
            if active_incident:
                old_status = active_incident["status"]
                inc_id = active_incident["incident_id"]
                try:
                    first_seen_dt = datetime.fromisoformat(active_incident["first_seen"])
                    duration = (now - first_seen_dt).total_seconds()
                except Exception:
                    duration = 0.0

                if old_status in [IncidentStatus.CONFIRMED, IncidentStatus.ACTIVE, IncidentStatus.SUSPECTED]:
                    new_status = IncidentStatus.RECOVERING
                    self._add_timeline_entry(inc_id, now_iso, "RECOVERY_STARTED", "Healthy observation received. Entering recovery confirmation window.", evidence)
                    active_incident.update({
                        "status": new_status,
                        "duration_seconds": duration,
                        "updated_at": now_iso
                    })
                    self._save_incident(active_incident)
                    return active_incident

                elif old_status == IncidentStatus.RECOVERING:
                    timeline_entries = self._get_timeline_entries(inc_id)
                    healthy_streak = len([t for t in timeline_entries if t["event_type"] in ["RECOVERY_STARTED", "HEALTHY_CONFIRMATION"]]) + 1
                    
                    if healthy_streak >= SETTINGS.recovery_count:
                        new_status = IncidentStatus.RESOLVED
                        active_incident.update({
                            "status": new_status,
                            "resolution_reason": "AUTO_RESOLVED",
                            "resolved_at": now_iso,
                            "duration_seconds": duration,
                            "updated_at": now_iso
                        })
                        self._add_timeline_entry(inc_id, now_iso, "INCIDENT_RESOLVED", f"Incident fully resolved after {healthy_streak} consecutive healthy readings.", evidence)
                        DB.log_audit(station_id, "INCIDENT_RESOLVED", f"Resolved incident {inc_id}", old_state=old_status, new_state=new_status)
                        self._save_incident(active_incident)
                        return active_incident
                    else:
                        self._add_timeline_entry(inc_id, now_iso, "HEALTHY_CONFIRMATION", f"Healthy confirmation reading {healthy_streak}/{SETTINGS.recovery_count}.", evidence)
                        active_incident.update({"updated_at": now_iso, "duration_seconds": duration})
                        self._save_incident(active_incident)
                        return active_incident

            else:
                return None

    def acknowledge_incident(self, incident_id: str, operator_name: str) -> bool:
        """Sets incident acknowledgement status without resolving it."""
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "UPDATE incidents SET acknowledgement_status = 'ACKNOWLEDGED', acknowledged_by = ?, acknowledged_at = ?, updated_at = ? WHERE incident_id = ?"
            if DB.use_postgres:
                q = q.replace("?", "%s")
            cursor.execute(q, (operator_name, now_iso, now_iso, incident_id))
            affected = cursor.rowcount
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()

        if affected > 0:
            self._add_timeline_entry(incident_id, now_iso, "OPERATOR_ACKNOWLEDGED", f"Incident acknowledged by operator {operator_name}.", {})
            DB.log_audit("SYSTEM", "INCIDENT_ACKNOWLEDGED", f"Incident {incident_id} acknowledged by {operator_name}")
            return True
        return False

    def resolve_incident(self, incident_id: str, reason: str, operator_name: Optional[str] = None) -> bool:
        """Manually resolves an incident with reason tracking."""
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "UPDATE incidents SET status = 'RESOLVED', resolution_reason = ?, resolved_at = ?, updated_at = ? WHERE incident_id = ?"
            if DB.use_postgres:
                q = q.replace("?", "%s")
            cursor.execute(q, (reason, now_iso, now_iso, incident_id))
            affected = cursor.rowcount
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()

        if affected > 0:
            actor = operator_name or "SYSTEM"
            self._add_timeline_entry(incident_id, now_iso, "OPERATOR_RESOLVED", f"Incident resolved with reason: {reason} by {actor}.", {})
            DB.log_audit("SYSTEM", "INCIDENT_MANUALLY_RESOLVED", f"Incident {incident_id} resolved by {actor} ({reason})")
            return True
        return False

    def _compute_severity(self, confidence: float, event_count: int, evidence: Dict[str, Any]) -> str:
        if evidence.get("is_comm_timeout") or event_count >= 10:
            return IncidentSeverity.CRITICAL
        if confidence >= 0.85 or event_count >= 5:
            return IncidentSeverity.HIGH
        if confidence >= 0.60 or event_count >= 2:
            return IncidentSeverity.MEDIUM
        return IncidentSeverity.LOW

    def _build_evidence_summary(self, evidence: Dict[str, Any], active: bool) -> Dict[str, Any]:
        supporting = []
        contradicting = []

        if evidence.get("rate_change"):
            supporting.append("Abnormal rate of change detected in parameter.")
        if evidence.get("range_check"):
            supporting.append("Value violated physical climatological range boundaries.")
        if evidence.get("physical_consistency"):
            supporting.append("Cross-parameter physical consistency check failed (e.g. Dew Point > Temperature).")
        if evidence.get("spatial_consistency"):
            supporting.append("Neighboring station spatial consensus disagreement.")

        why_text = "Incident remains active due to persistent anomaly evidence." if active else "No alert generated because physical and spatial checks passed."

        return {
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "why_alert_active": why_text,
            "raw_evidence": evidence
        }

    def _find_active_incident(self, station_id: str, parameter: str) -> Optional[Dict[str, Any]]:
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "SELECT * FROM incidents WHERE station_id = ? AND affected_parameter = ? AND status IN ('SUSPECTED', 'CONFIRMED', 'ACTIVE', 'RECOVERING') ORDER BY created_at DESC LIMIT 1"
            if DB.use_postgres:
                q = q.replace("?", "%s")
            cursor.execute(q, (station_id, parameter))
            if DB.use_postgres:
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                return dict(zip(cols, rows[0])) if rows else None
            else:
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def _save_incident(self, incident: Dict[str, Any]):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO incidents (
                incident_id, station_id, affected_parameter, first_seen, last_seen,
                duration_seconds, status, severity, event_count, evidence_summary_json,
                root_cause, confidence, acknowledgement_status, acknowledged_by,
                acknowledged_at, resolution_reason, resolved_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if DB.use_postgres:
                q = q.replace("?", "%s") + " ON CONFLICT (incident_id) DO UPDATE SET status = EXCLUDED.status, severity = EXCLUDED.severity, event_count = EXCLUDED.event_count, last_seen = EXCLUDED.last_seen, duration_seconds = EXCLUDED.duration_seconds, updated_at = EXCLUDED.updated_at"
            else:
                q = q.replace("INSERT INTO", "INSERT OR REPLACE INTO")

            cursor.execute(q, (
                incident["incident_id"],
                incident["station_id"],
                incident["affected_parameter"],
                incident["first_seen"],
                incident["last_seen"],
                incident["duration_seconds"],
                incident["status"],
                incident["severity"],
                incident["event_count"],
                incident["evidence_summary_json"],
                incident["root_cause"],
                incident["confidence"],
                incident["acknowledgement_status"],
                incident.get("acknowledged_by"),
                incident.get("acknowledged_at"),
                incident.get("resolution_reason"),
                incident.get("resolved_at"),
                incident["created_at"],
                incident["updated_at"]
            ))
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()

    def _add_timeline_entry(self, incident_id: str, timestamp: str, event_type: str, description: str, evidence: Dict[str, Any]):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO incident_timeline (incident_id, timestamp, event_type, description, evidence_json)
            VALUES (?, ?, ?, ?, ?)
            """
            if DB.use_postgres:
                q = q.replace("?", "%s")
            cursor.execute(q, (incident_id, timestamp, event_type, description, json.dumps(evidence or {})))
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()

    def _get_timeline_entries(self, incident_id: str) -> List[Dict[str, Any]]:
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "SELECT * FROM incident_timeline WHERE incident_id = ? ORDER BY timeline_id ASC"
            if DB.use_postgres:
                q = q.replace("?", "%s")
                cursor.execute(q, (incident_id,))
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                return [dict(zip(cols, r)) for r in rows]
            else:
                cursor.execute(q, (incident_id,))
                return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()


# Global Incident Lifecycle Manager Instance
INCIDENT_MANAGER = IncidentLifecycleManager()
