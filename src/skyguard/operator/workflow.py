"""
SkyGuard AI — Operator Workflow & Controlled Recalibration Queue
Handles explicit operator feedback actions (CONFIRM_ANOMALY, REJECT_ANOMALY, etc.)
and queues them into a controlled review pipeline without directly mutating live ML models.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from skyguard.db.database import DB


class OperatorAction:
    CONFIRM_ANOMALY = "CONFIRM_ANOMALY"
    REJECT_ANOMALY = "REJECT_ANOMALY"
    CONFIRM_CORRECTION = "CONFIRM_CORRECTION"
    REJECT_CORRECTION = "REJECT_CORRECTION"
    MARK_WEATHER_EVENT = "MARK_WEATHER_EVENT"
    MARK_SENSOR_FAULT = "MARK_SENSOR_FAULT"


class RecalibrationStatus:
    PENDING = "PENDING"
    VALIDATION = "VALIDATION"
    CANDIDATE = "CANDIDATE"
    VALIDATION_TEST = "VALIDATION_TEST"
    DEPLOYED = "DEPLOYED"
    REJECTED = "REJECTED"


class OperatorWorkflowManager:
    """Manages operator feedback actions and controlled recalibration review queue."""

    def submit_feedback(
        self,
        station_id: str,
        operator_action: str,
        incident_id: Optional[str] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        reason: Optional[str] = None,
        operator_name: str = "OPERATOR"
    ) -> Dict[str, Any]:
        """
        Records an explicit operator action into audit log and recalibration review queue.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        feedback_id = f"FBK-{uuid.uuid4().hex[:8].upper()}"

        # 1. Save operator feedback record
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO operator_feedback (
                feedback_id, incident_id, station_id, timestamp, operator_action,
                previous_state, new_state, reason, review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if DB.use_postgres:
                q = q.replace("?", "%s")
            cursor.execute(q, (feedback_id, incident_id, station_id, now_iso, operator_action, previous_state, new_state, reason, RecalibrationStatus.PENDING))
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()

        # 2. Queue into controlled recalibration candidate pipeline
        candidate_id = f"RCAL-{uuid.uuid4().hex[:8].upper()}"
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO recalibration_queue (
                candidate_id, feedback_id, created_at, status, validation_metrics_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            if DB.use_postgres:
                q = q.replace("?", "%s")
            cursor.execute(q, (
                candidate_id, feedback_id, now_iso, RecalibrationStatus.PENDING,
                json.dumps({"action": operator_action, "operator": operator_name}),
                f"Queued for model review following operator action {operator_action}."
            ))
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()

        # 3. Log operational audit
        DB.log_audit(
            station_id=station_id,
            event_type="OPERATOR_FEEDBACK_SUBMITTED",
            old_state=previous_state,
            new_state=new_state,
            reason=f"Operator {operator_name} submitted {operator_action}: {reason}",
            actor=operator_name,
            metadata={"feedback_id": feedback_id, "candidate_id": candidate_id}
        )

        return {
            "feedback_id": feedback_id,
            "candidate_id": candidate_id,
            "station_id": station_id,
            "operator_action": operator_action,
            "status": RecalibrationStatus.PENDING,
            "timestamp": now_iso
        }

    def advance_recalibration_candidate(self, candidate_id: str, target_status: str, notes: Optional[str] = None) -> bool:
        """
        Advances a recalibration candidate through the controlled pipeline:
        PENDING -> VALIDATION -> CANDIDATE -> VALIDATION_TEST -> DEPLOYED / REJECTED
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "UPDATE recalibration_queue SET status = ?, notes = ?, deployed_at = ? WHERE candidate_id = ?"
            if DB.use_postgres:
                q = q.replace("?", "%s")
            deployed_at = now_iso if target_status == RecalibrationStatus.DEPLOYED else None
            cursor.execute(q, (target_status, notes or f"Advanced to {target_status}", deployed_at, candidate_id))
            if not DB.use_postgres:
                conn.commit()
            
            DB.log_audit("SYSTEM", "RECALIBRATION_PIPELINE_ADVANCED", f"Candidate {candidate_id} status updated to {target_status}")
            return True
        finally:
            conn.close()

    def get_pending_recalibrations(self) -> List[Dict[str, Any]]:
        """Fetches pending recalibration review candidates."""
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "SELECT * FROM recalibration_queue WHERE status != 'DEPLOYED' AND status != 'REJECTED' ORDER BY created_at DESC"
            cursor.execute(q)
            if DB.use_postgres:
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                return [dict(zip(cols, r)) for r in rows]
            else:
                return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()


# Global Operator Workflow Manager
OPERATOR_WORKFLOW = OperatorWorkflowManager()
