"""
SkyGuard AI — Centralized Operational Settings & System Parameters
Loads operational thresholds, database credentials, and environment configuration
dynamically from the project .env file.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    # Load .env file from workspace root
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass


@dataclass
class OperationalSettings:
    """Central configuration for SkyGuard AI operational intelligence logic."""
    
    # ----------------------------------------------------
    # Central Database Configuration (Loaded from .env)
    # ----------------------------------------------------
    postgres_host: str = os.getenv("DB_HOST", "localhost")
    postgres_port: int = int(os.getenv("DB_PORT", "5432"))
    postgres_db: str = os.getenv("DB_NAME", "postgres")
    postgres_user: str = os.getenv("DB_USER", "postgres")
    postgres_password: str = os.getenv("DB_PASSWORD", "")
    postgres_sslmode: str = os.getenv("DB_SSLMODE", "require")
    
    postgres_url: str = os.getenv(
        "POSTGRES_URL",
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', '')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'postgres')}?sslmode={os.getenv('DB_SSLMODE', 'require')}"
    )
    db_path: str = os.getenv("DB_PATH", "skyguard.db")
    
    # ----------------------------------------------------
    # Incident & Anomaly Confirmation Boundaries
    # ----------------------------------------------------
    confirmation_count: int = int(os.getenv("CONFIRMATION_COUNT", "3"))
    recovery_count: int = int(os.getenv("RECOVERY_COUNT", "5"))
    incident_merge_window_seconds: int = int(os.getenv("INCIDENT_MERGE_WINDOW_SECONDS", "600"))
    alert_cooldown_seconds: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "300"))
    
    # ----------------------------------------------------
    # Communication & Telemetry Integrity
    # ----------------------------------------------------
    expected_interval_seconds: float = float(os.getenv("EXPECTED_INTERVAL_SECONDS", "10.0"))
    communication_timeout_seconds: float = float(os.getenv("COMMUNICATION_TIMEOUT_SECONDS", "30.0"))
    max_clock_skew_seconds: float = float(os.getenv("MAX_CLOCK_SKEW_SECONDS", "300.0"))
    max_out_of_order_gap_seconds: float = float(os.getenv("MAX_OUT_OF_ORDER_GAP_SECONDS", "3600.0"))
    
    # ----------------------------------------------------
    # Sensor Operational State Machine & Hysteresis
    # ----------------------------------------------------
    sensor_degraded_enter_anomalies: int = 3
    sensor_degraded_exit_healthy: int = 5
    sensor_suspect_enter_anomalies: int = 2
    sensor_suspect_exit_healthy: int = 3
    
    # ----------------------------------------------------
    # Spatial & Regional Correlation Parameters
    # ----------------------------------------------------
    regional_event_min_stations: int = 3
    regional_event_distance_km: float = 50.0
    spatial_isolation_threshold: float = 2.5
    
    # ----------------------------------------------------
    # Safe Auto-Correction Policies
    # ----------------------------------------------------
    auto_correct_high_confidence_min: float = 0.85
    auto_correct_suggest_medium_min: float = 0.60

# Global default settings instance
SETTINGS = OperationalSettings()
