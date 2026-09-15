"""
SkyGuard AI — Sensor Operational State Machine & Hysteresis Controller
Maintains per-station and per-sensor operational states (HEALTHY, WATCH, SUSPECT,
DEGRADED, FAILED, RECOVERING) using deterministic hysteresis thresholds to prevent state oscillation.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from skyguard.config.settings import SETTINGS
from skyguard.db.database import DB


class SensorOperationalState:
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    SUSPECT = "SUSPECT"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"


class SensorStateMachine:
    """Manages sensor state transitions with hysteresis and audit logging."""

    def __init__(self):
        # Cache sensor state in memory: (station_id, parameter) -> state_dict
        self.states: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def get_or_create_state(self, station_id: str, parameter: str) -> Dict[str, Any]:
        key = (station_id, parameter)
        if key not in self.states:
            now = datetime.now(timezone.utc).isoformat()
            state = {
                "station_id": station_id,
                "sensor_parameter": parameter,
                "operational_state": SensorOperationalState.HEALTHY,
                "health_status": "HEALTHY",
                "consecutive_healthy_count": 0,
                "consecutive_anomalous_count": 0,
                "last_state_change": now,
                "last_valid_reading_at": now,
                "last_anomaly_at": None,
                "recovery_started_at": None,
                "recovery_confirmed_at": None,
                "updated_at": now
            }
            self.states[key] = state
            self._persist_state(state)
        return self.states[key]

    def update_state(self, station_id: str, parameter: str, is_anomaly: bool,
                     confidence: float = 0.0, is_comm_timeout: bool = False,
                     reading_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Evaluates state transition rules with hysteresis based on latest reading.
        
        Returns updated sensor state dictionary.
        """
        now = reading_time or datetime.now(timezone.utc)
        now_iso = now.isoformat()
        state = self.get_or_create_state(station_id, parameter)

        old_op_state = state["operational_state"]
        new_op_state = old_op_state

        # Handle communication dropout failure state
        if is_comm_timeout:
            new_op_state = SensorOperationalState.FAILED
            state["consecutive_anomalous_count"] += 1
            state["consecutive_healthy_count"] = 0
            state["health_status"] = "CRITICAL"
        elif is_anomaly:
            state["consecutive_anomalous_count"] += 1
            state["consecutive_healthy_count"] = 0
            state["last_anomaly_at"] = now_iso
            state["recovery_started_at"] = None  # Reset recovery if anomaly reoccurs

            count = state["consecutive_anomalous_count"]

            if count >= SETTINGS.sensor_degraded_enter_anomalies or confidence >= 0.85:
                new_op_state = SensorOperationalState.DEGRADED
                state["health_status"] = "DEGRADED"
            elif count >= SETTINGS.sensor_suspect_enter_anomalies:
                new_op_state = SensorOperationalState.SUSPECT
                state["health_status"] = "WARNING"
            else:
                new_op_state = SensorOperationalState.WATCH
                state["health_status"] = "WATCH"

        else:
            # Healthy reading
            state["consecutive_healthy_count"] += 1
            state["consecutive_anomalous_count"] = 0
            state["last_valid_reading_at"] = now_iso

            healthy_count = state["consecutive_healthy_count"]

            if old_op_state in [SensorOperationalState.DEGRADED, SensorOperationalState.SUSPECT, SensorOperationalState.FAILED, SensorOperationalState.WATCH]:
                if state["recovery_started_at"] is None:
                    state["recovery_started_at"] = now_iso
                new_op_state = SensorOperationalState.RECOVERING
                state["health_status"] = "RECOVERING"

            if old_op_state == SensorOperationalState.RECOVERING:
                if healthy_count >= SETTINGS.sensor_degraded_exit_healthy:
                    new_op_state = SensorOperationalState.HEALTHY
                    state["health_status"] = "HEALTHY"
                    state["recovery_confirmed_at"] = now_iso

        # Log audit if state changed
        if new_op_state != old_op_state:
            state["operational_state"] = new_op_state
            state["last_state_change"] = now_iso
            DB.log_audit(
                station_id=station_id,
                event_type="SENSOR_STATE_CHANGE",
                old_state=old_op_state,
                new_state=new_op_state,
                reason=f"Transitioned for {parameter}: anomaly={is_anomaly}, healthy_streak={state['consecutive_healthy_count']}, anomaly_streak={state['consecutive_anomalous_count']}",
                actor="SENSOR_STATE_MACHINE"
            )

        state["updated_at"] = now_iso
        self._persist_state(state)
        return state

    def _persist_state(self, state: Dict[str, Any]):
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO sensor_states (
                station_id, sensor_parameter, operational_state, health_status,
                consecutive_healthy_count, consecutive_anomalous_count,
                last_state_change, last_valid_reading_at, last_anomaly_at,
                recovery_started_at, recovery_confirmed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if DB.use_postgres:
                q = q.replace("?", "%s") + " ON CONFLICT (station_id, sensor_parameter) DO UPDATE SET operational_state = EXCLUDED.operational_state, health_status = EXCLUDED.health_status, consecutive_healthy_count = EXCLUDED.consecutive_healthy_count, consecutive_anomalous_count = EXCLUDED.consecutive_anomalous_count, updated_at = EXCLUDED.updated_at"
            else:
                q = q.replace("INSERT INTO", "INSERT OR REPLACE INTO")

            cursor.execute(q, (
                state["station_id"],
                state["sensor_parameter"],
                state["operational_state"],
                state["health_status"],
                state["consecutive_healthy_count"],
                state["consecutive_anomalous_count"],
                state["last_state_change"],
                state["last_valid_reading_at"],
                state["last_anomaly_at"],
                state["recovery_started_at"],
                state["recovery_confirmed_at"],
                state["updated_at"]
            ))
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()


# Global Sensor State Machine
SENSOR_STATE_MACHINE = SensorStateMachine()
