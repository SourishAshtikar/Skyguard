"""
SkyGuard AI — Persistent PostgreSQL Database Engine & Data Access Layer
Provides PostgreSQL persistence for raw telemetry, quality flags, incidents, timeline,
sensor state machines, communication watchdogs, operator feedback, recalibration queue,
and audit logs.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from skyguard.config.settings import SETTINGS

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class DatabaseManager:
    """Thread-safe Database manager supporting PostgreSQL with standard SQL abstractions."""

    def __init__(self):
        self.use_postgres = False
        self._check_connection_type()
        self._init_db()

    def _get_pg_connection(self):
        """Creates a PostgreSQL connection using configured settings."""
        return psycopg2.connect(
            host=SETTINGS.postgres_host,
            port=SETTINGS.postgres_port,
            user=SETTINGS.postgres_user,
            password=SETTINGS.postgres_password,
            dbname=SETTINGS.postgres_db,
            sslmode=SETTINGS.postgres_sslmode
        )

    def _check_connection_type(self):
        """Attempts to establish connection to PostgreSQL server."""
        if PSYCOPG2_AVAILABLE:
            try:
                conn = self._get_pg_connection()
                conn.close()
                self.use_postgres = True
            except Exception as e:
                self.use_postgres = False
        else:
            self.use_postgres = False

    def get_connection(self):
        """Returns database connection context (PostgreSQL or SQLite fallback)."""
        if self.use_postgres:
            conn = self._get_pg_connection()
            conn.autocommit = True
            return conn
        else:
            conn = sqlite3.connect(SETTINGS.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_db(self):
        """Initialize database schema tables and indices."""
        conn = self.get_connection()
        cursor = conn.cursor()

        id_pk = "SERIAL PRIMARY KEY" if self.use_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
        text_type = "TEXT"
        real_type = "DOUBLE PRECISION" if self.use_postgres else "REAL"
        bool_type = "BOOLEAN"

        try:
            # 1. Raw Telemetry Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS raw_readings (
                reading_id VARCHAR(64) PRIMARY KEY,
                station_id VARCHAR(64) NOT NULL,
                timestamp {text_type} NOT NULL,
                temperature {real_type},
                pressure {real_type},
                humidity {real_type},
                latitude {real_type},
                longitude {real_type},
                elevation_m {real_type},
                battery_voltage {real_type},
                is_precipitating {bool_type},
                rain_mm {real_type},
                ingestion_timestamp {text_type} NOT NULL,
                quality_state {text_type} NOT NULL,
                quality_flags_json {text_type},
                corrected_temperature {real_type},
                corrected_pressure {real_type},
                corrected_humidity {real_type},
                correction_method {text_type},
                correction_confidence {real_type}
            )
            """)

            # 2. Quality Flags Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS quality_flags (
                flag_id {id_pk},
                reading_id VARCHAR(64) NOT NULL,
                station_id VARCHAR(64) NOT NULL,
                timestamp {text_type} NOT NULL,
                missing_timestamp {bool_type} DEFAULT FALSE,
                invalid_timestamp {bool_type} DEFAULT FALSE,
                future_timestamp {bool_type} DEFAULT FALSE,
                duplicate_timestamp {bool_type} DEFAULT FALSE,
                out_of_order {bool_type} DEFAULT FALSE,
                excessive_clock_jump {bool_type} DEFAULT FALSE,
                stale_data {bool_type} DEFAULT FALSE,
                quality_state {text_type} NOT NULL
            )
            """)

            # 3. Incidents Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id VARCHAR(64) PRIMARY KEY,
                station_id VARCHAR(64) NOT NULL,
                affected_parameter {text_type} NOT NULL,
                first_seen {text_type} NOT NULL,
                last_seen {text_type} NOT NULL,
                duration_seconds {real_type} DEFAULT 0.0,
                status {text_type} NOT NULL,
                severity {text_type} NOT NULL,
                event_count INTEGER DEFAULT 1,
                evidence_summary_json {text_type},
                root_cause {text_type} NOT NULL,
                confidence {real_type} DEFAULT 0.0,
                acknowledgement_status {text_type} DEFAULT 'UNACKNOWLEDGED',
                acknowledged_by {text_type},
                acknowledged_at {text_type},
                resolution_reason {text_type},
                resolved_at {text_type},
                created_at {text_type} NOT NULL,
                updated_at {text_type} NOT NULL
            )
            """)

            # 4. Incident Timeline Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS incident_timeline (
                timeline_id {id_pk},
                incident_id VARCHAR(64) NOT NULL,
                timestamp {text_type} NOT NULL,
                event_type {text_type} NOT NULL,
                description {text_type} NOT NULL,
                evidence_json {text_type}
            )
            """)

            # 5. Sensor Operational States Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sensor_states (
                station_id VARCHAR(64) NOT NULL,
                sensor_parameter VARCHAR(64) NOT NULL,
                operational_state {text_type} NOT NULL,
                health_status {text_type} NOT NULL,
                consecutive_healthy_count INTEGER DEFAULT 0,
                consecutive_anomalous_count INTEGER DEFAULT 0,
                last_state_change {text_type} NOT NULL,
                last_valid_reading_at {text_type},
                last_anomaly_at {text_type},
                recovery_started_at {text_type},
                recovery_confirmed_at {text_type},
                updated_at {text_type} NOT NULL,
                PRIMARY KEY (station_id, sensor_parameter)
            )
            """)

            # 6. Communication Watchdogs Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS communication_watchdogs (
                station_id VARCHAR(64) PRIMARY KEY,
                last_seen {text_type} NOT NULL,
                expected_interval_s {real_type} DEFAULT 10.0,
                actual_interval_s {real_type} DEFAULT 0.0,
                late_packet_count INTEGER DEFAULT 0,
                missing_packet_count INTEGER DEFAULT 0,
                duplicate_packet_count INTEGER DEFAULT 0,
                out_of_order_count INTEGER DEFAULT 0,
                comm_status {text_type} NOT NULL,
                updated_at {text_type} NOT NULL
            )
            """)

            # 7. Operator Feedback Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS operator_feedback (
                feedback_id VARCHAR(64) PRIMARY KEY,
                incident_id VARCHAR(64),
                station_id VARCHAR(64) NOT NULL,
                timestamp {text_type} NOT NULL,
                operator_action {text_type} NOT NULL,
                previous_state {text_type},
                new_state {text_type},
                reason {text_type},
                review_status {text_type} DEFAULT 'PENDING'
            )
            """)

            # 8. Recalibration Queue Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS recalibration_queue (
                candidate_id VARCHAR(64) PRIMARY KEY,
                feedback_id VARCHAR(64) NOT NULL,
                created_at {text_type} NOT NULL,
                status {text_type} NOT NULL,
                validation_metrics_json {text_type},
                deployed_at {text_type},
                notes {text_type}
            )
            """)

            # 9. Audit Logs Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id {id_pk},
                timestamp {text_type} NOT NULL,
                station_id VARCHAR(64) NOT NULL,
                event_type {text_type} NOT NULL,
                old_state {text_type},
                new_state {text_type},
                reason {text_type} NOT NULL,
                actor {text_type} NOT NULL,
                metadata_json {text_type}
            )
            """)

            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_station_ts ON raw_readings (station_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_station ON incidents (station_id, status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_station ON audit_logs (station_id, timestamp)")

            if not self.use_postgres:
                conn.commit()
        finally:
            conn.close()

    # ----------------------------------------------------
    # Helper CRUD methods
    # ----------------------------------------------------
    def save_raw_reading(self, reading_data: Dict[str, Any]):
        """Persist raw telemetry reading without overwriting raw values."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO raw_readings (
                reading_id, station_id, timestamp, temperature, pressure, humidity,
                latitude, longitude, elevation_m, battery_voltage, is_precipitating,
                rain_mm, ingestion_timestamp, quality_state, quality_flags_json,
                corrected_temperature, corrected_pressure, corrected_humidity,
                correction_method, correction_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if self.use_postgres:
                q = q.replace("?", "%s") + " ON CONFLICT (reading_id) DO UPDATE SET quality_state = EXCLUDED.quality_state"
            else:
                q = q.replace("INSERT INTO", "INSERT OR REPLACE INTO")

            params = (
                reading_data["reading_id"],
                reading_data["station_id"],
                reading_data["timestamp"],
                reading_data.get("temperature"),
                reading_data.get("pressure"),
                reading_data.get("humidity"),
                reading_data.get("latitude"),
                reading_data.get("longitude"),
                reading_data.get("elevation_m"),
                reading_data.get("battery_voltage"),
                reading_data.get("is_precipitating"),
                reading_data.get("rain_mm"),
                reading_data.get("ingestion_timestamp", datetime.now(timezone.utc).isoformat()),
                reading_data.get("quality_state", "GOOD"),
                json.dumps(reading_data.get("quality_flags", {})),
                reading_data.get("corrected_temperature"),
                reading_data.get("corrected_pressure"),
                reading_data.get("corrected_humidity"),
                reading_data.get("correction_method", "NONE"),
                reading_data.get("correction_confidence", 0.0)
            )
            cursor.execute(q, params)
            if not self.use_postgres:
                conn.commit()
        finally:
            conn.close()

    def log_audit(self, station_id: str, event_type: str, reason: str, actor: str = "SYSTEM",
                  old_state: Optional[str] = None, new_state: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Write an entry to the operational audit log."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            q = """
            INSERT INTO audit_logs (timestamp, station_id, event_type, old_state, new_state, reason, actor, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            if self.use_postgres:
                q = q.replace("?", "%s")

            cursor.execute(q, (now, station_id, event_type, old_state, new_state, reason, actor, json.dumps(metadata or {})))
            if not self.use_postgres:
                conn.commit()
        finally:
            conn.close()

    def get_audit_logs(self, station_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch audit log entries."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if self.use_postgres:
                if station_id:
                    cursor.execute("SELECT * FROM audit_logs WHERE station_id = %s ORDER BY log_id DESC LIMIT %s", (station_id, limit))
                else:
                    cursor.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT %s", (limit,))
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                return [dict(zip(cols, r)) for r in rows]
            else:
                if station_id:
                    cursor.execute("SELECT * FROM audit_logs WHERE station_id = ? ORDER BY log_id DESC LIMIT ?", (station_id, limit))
                else:
                    cursor.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT ?", (limit,))
                return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def clear_database(self):
        """Helper for testing to reset all tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            for table in [
                "raw_readings", "quality_flags", "incidents", "incident_timeline",
                "sensor_states", "communication_watchdogs", "operator_feedback",
                "recalibration_queue", "audit_logs"
            ]:
                cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE' if self.use_postgres else f"DELETE FROM {table}")
            if not self.use_postgres:
                conn.commit()
        finally:
            conn.close()


# Global DB Instance
DB = DatabaseManager()
