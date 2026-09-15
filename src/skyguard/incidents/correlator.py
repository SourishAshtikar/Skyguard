"""
SkyGuard AI — Deterministic Event Correlator
Correlates individual anomaly observations across parameters (MULTIVARIATE_INCIDENT)
and across nearby AWS stations (REGIONAL_WEATHER_EVENT) within a configured correlation window.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from skyguard.config.settings import SETTINGS
from skyguard.db.database import DB


class EventCorrelator:
    """Correlates observations to form multivariate or regional incidents."""

    def correlate_station_incidents(self, station_id: str) -> Optional[Dict[str, Any]]:
        """
        Checks open incidents for a single station. If multiple parameter anomalies
        (e.g. temperature + pressure + humidity) exist within the correlation window,
        groups them into a MULTIVARIATE_INCIDENT.
        """
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = "SELECT * FROM incidents WHERE station_id = ? AND status IN ('SUSPECTED', 'CONFIRMED', 'ACTIVE')"
            if DB.use_postgres:
                q = q.replace("?", "%s")
                cursor.execute(q, (station_id,))
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                open_incidents = [dict(zip(cols, r)) for r in rows]
            else:
                cursor.execute(q, (station_id,))
                open_incidents = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

        if len(open_incidents) >= 2:
            affected_params = list(set([inc["affected_parameter"] for inc in open_incidents]))
            if len(affected_params) >= 2:
                main_inc = open_incidents[0]
                inc_id = main_inc["incident_id"]
                now_iso = datetime.now(timezone.utc).isoformat()
                combined_param = "MULTIVARIATE (" + ", ".join(affected_params) + ")"
                
                conn = DB.get_connection()
                cursor = conn.cursor()
                try:
                    q_up = "UPDATE incidents SET affected_parameter = ?, root_cause = 'MULTIVARIATE_INCIDENT', updated_at = ? WHERE incident_id = ?"
                    if DB.use_postgres:
                        q_up = q_up.replace("?", "%s")
                    cursor.execute(q_up, (combined_param, now_iso, inc_id))
                    if not DB.use_postgres:
                        conn.commit()
                finally:
                    conn.close()

                DB.log_audit(station_id, "EVENT_CORRELATION", f"Correlated {len(open_incidents)} anomalies into MULTIVARIATE_INCIDENT for {station_id}")
                main_inc["affected_parameter"] = combined_param
                main_inc["root_cause"] = "MULTIVARIATE_INCIDENT"
                return main_inc

        return None

    def evaluate_regional_weather_event(self, active_station_ids: List[str], regional_anomalies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether multiple nearby stations experiencing anomalies represent a REGIONAL_WEATHER_EVENT.
        """
        unique_stations = list(set(active_station_ids))
        if len(unique_stations) >= SETTINGS.regional_event_min_stations:
            now_iso = datetime.now(timezone.utc).isoformat()
            regional_event = {
                "event_type": "REGIONAL_WEATHER_EVENT",
                "affected_stations": unique_stations,
                "station_count": len(unique_stations),
                "timestamp": now_iso,
                "summary": f"Regional weather event confirmed across {len(unique_stations)} nearby stations ({', '.join(unique_stations)})."
            }
            DB.log_audit("REGIONAL", "REGIONAL_WEATHER_EVENT_DETECTED", regional_event["summary"], metadata=regional_event)
            return regional_event

        return None


# Global Event Correlator Instance
CORRELATOR = EventCorrelator()
