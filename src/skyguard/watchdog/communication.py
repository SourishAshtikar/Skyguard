"""
SkyGuard AI — Communication Watchdog & Telemetry Health Tracker
Tracks packet arrival cadence per station, maintaining statistics for late, missing,
duplicate, and out-of-order packets. Distinguishes communication failures from sensor fault errors.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from skyguard.config.settings import SETTINGS
from skyguard.db.database import DB


class CommunicationStatus:
    HEALTHY = "HEALTHY"
    LATE = "LATE"
    DROPOUT = "DROPOUT"
    STALE = "STALE"


class CommunicationWatchdog:
    """Monitors telemetry arrival cadence and packet integrity for AWS stations."""

    def __init__(self):
        # In-memory station packet stats cache
        self.station_stats: Dict[str, Dict[str, Any]] = {}

    def record_packet(self, station_id: str, timestamp: datetime, quality_flags: Dict[str, bool]) -> Dict[str, Any]:
        """
        Updates communication watchdog metrics upon receiving a packet.
        
        Returns updated watchdog status dict.
        """
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if station_id not in self.station_stats:
            stats = {
                "station_id": station_id,
                "last_seen": timestamp,
                "expected_interval_s": SETTINGS.expected_interval_seconds,
                "actual_interval_s": 0.0,
                "late_packet_count": 0,
                "missing_packet_count": 0,
                "duplicate_packet_count": 0,
                "out_of_order_count": 0,
                "comm_status": CommunicationStatus.HEALTHY,
                "updated_at": now.isoformat()
            }
            self.station_stats[station_id] = stats
            self._persist_watchdog(stats)
            return stats

        stats = self.station_stats[station_id]
        last_seen = stats["last_seen"]
        
        actual_interval = (timestamp - last_seen).total_seconds()
        stats["actual_interval_s"] = actual_interval

        # Check packet anomalies from flags
        if quality_flags.get("duplicate_timestamp"):
            stats["duplicate_packet_count"] += 1
        elif quality_flags.get("out_of_order"):
            stats["out_of_order_count"] += 1
        elif actual_interval > SETTINGS.communication_timeout_seconds:
            stats["missing_packet_count"] += int(actual_interval // SETTINGS.expected_interval_seconds) - 1
            stats["comm_status"] = CommunicationStatus.DROPOUT
        elif actual_interval > SETTINGS.expected_interval_seconds * 1.5:
            stats["late_packet_count"] += 1
            stats["comm_status"] = CommunicationStatus.LATE
        else:
            stats["comm_status"] = CommunicationStatus.HEALTHY

        stats["last_seen"] = timestamp
        stats["updated_at"] = now.isoformat()
        
        self._persist_watchdog(stats)
        return stats

    def check_station_timeouts(self, station_id: str, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Periodic check for communication timeout when no packet has arrived."""
        now = current_time or datetime.now(timezone.utc)
        if station_id in self.station_stats:
            stats = self.station_stats[station_id]
            elapsed = (now - stats["last_seen"]).total_seconds()
            if elapsed > SETTINGS.communication_timeout_seconds:
                stats["comm_status"] = CommunicationStatus.DROPOUT
                stats["updated_at"] = now.isoformat()
                self._persist_watchdog(stats)
            return stats
        return {
            "station_id": station_id,
            "last_seen": now,
            "comm_status": CommunicationStatus.DROPOUT
        }

    def _persist_watchdog(self, stats: Dict[str, Any]):
        """Save watchdog metrics to database."""
        conn = DB.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO communication_watchdogs (
                station_id, last_seen, expected_interval_s, actual_interval_s,
                late_packet_count, missing_packet_count, duplicate_packet_count,
                out_of_order_count, comm_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if DB.use_postgres:
                q = q.replace("?", "%s") + " ON CONFLICT (station_id) DO UPDATE SET comm_status = EXCLUDED.comm_status, updated_at = EXCLUDED.updated_at"
            else:
                q = q.replace("INSERT INTO", "INSERT OR REPLACE INTO")

            cursor.execute(q, (
                stats["station_id"],
                stats["last_seen"].isoformat() if isinstance(stats["last_seen"], datetime) else str(stats["last_seen"]),
                stats["expected_interval_s"],
                stats["actual_interval_s"],
                stats["late_packet_count"],
                stats["missing_packet_count"],
                stats["duplicate_packet_count"],
                stats["out_of_order_count"],
                stats["comm_status"],
                stats["updated_at"]
            ))
            if not DB.use_postgres:
                conn.commit()
        finally:
            conn.close()


# Global Watchdog Instance
WATCHDOG = CommunicationWatchdog()
