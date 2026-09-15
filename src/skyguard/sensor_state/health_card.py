"""
SkyGuard AI — Sensor Health Card Generator
Generates detailed, operator-ready health cards per station/sensor without requiring
the operator to open full ML explanation panels.
"""

from typing import Dict, Any, List, Optional
from skyguard.db.database import DB
from skyguard.sensor_state.state_machine import SENSOR_STATE_MACHINE


class SensorHealthCardGenerator:
    """Generates sensor health summary cards combining state machine, watchdog, and incident metrics."""

    @staticmethod
    def generate_health_card(station_id: str, parameter: str = "ALL") -> Dict[str, Any]:
        """
        Builds a comprehensive sensor health card.
        """
        # Fetch operational state
        state = SENSOR_STATE_MACHINE.get_or_create_state(station_id, parameter)

        # Fetch communication watchdog status
        comm_stats = {}
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q_comm = "SELECT * FROM communication_watchdogs WHERE station_id = ?"
            if DB.use_postgres:
                q_comm = q_comm.replace("?", "%s")
                cursor.execute(q_comm, (station_id,))
                rows = cursor.fetchall()
                if rows:
                    cols = [desc[0] for desc in cursor.description]
                    comm_stats = dict(zip(cols, rows[0]))
            else:
                cursor.execute(q_comm, (station_id,))
                row = cursor.fetchone()
                if row:
                    comm_stats = dict(row)
        finally:
            conn.close()

        # Fetch open incidents for station
        open_incidents = []
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q_inc = "SELECT * FROM incidents WHERE station_id = ? AND status IN ('SUSPECTED', 'CONFIRMED', 'ACTIVE', 'RECOVERING')"
            if DB.use_postgres:
                q_inc = q_inc.replace("?", "%s")
                cursor.execute(q_inc, (station_id,))
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                open_incidents = [dict(zip(cols, r)) for r in rows]
            else:
                cursor.execute(q_inc, (station_id,))
                open_incidents = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

        recent_anomaly_count = state.get("consecutive_anomalous_count", 0)

        if state["consecutive_anomalous_count"] > 0:
            trend = "DEGRADATING"
        elif state["operational_state"] == "RECOVERING":
            trend = "IMPROVING"
        else:
            trend = "STABLE"

        reason = f"Operational state is {state['operational_state']}."
        if comm_stats.get("comm_status") == "DROPOUT":
            reason = "Communication timeout exceeded 30s. No telemetry received."
        elif len(open_incidents) > 0:
            reason = f"{len(open_incidents)} open incident(s) currently active."
        elif state["consecutive_healthy_count"] > 0:
            reason = f"Normal telemetry stream with {state['consecutive_healthy_count']} consecutive healthy readings."

        return {
            "station_id": station_id,
            "sensor_parameter": parameter,
            "current_state": state["operational_state"],
            "health_status": state["health_status"],
            "last_valid_reading": state["last_valid_reading_at"],
            "last_anomaly": state["last_anomaly_at"],
            "open_incidents_count": len(open_incidents),
            "open_incidents": open_incidents,
            "communication_status": comm_stats.get("comm_status", "HEALTHY"),
            "recent_anomaly_count": recent_anomaly_count,
            "trend": trend,
            "reason": reason
        }
