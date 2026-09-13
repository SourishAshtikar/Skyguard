"""
SkyGuard AI — Sensor Health & Predictive Maintenance Tracker
Tracks rolling degradation metrics per station and per sensor:
- Rolling anomaly rate over 48-reading window
- Consecutive failure counter
- Missing data ratio
- Zero-point drift magnitude
- Health Score % (100% down to 0%)
- Predictive maintenance window & recommended actions
"""

from collections import deque
from typing import Dict, List, Optional
import numpy as np

from skyguard.config.contracts import SensorHealthMetric


class SensorHealthTracker:
    """Maintains sliding-window health indicators for AWS instruments."""

    def __init__(
        self,
        station_id: str,
        window_size: int = 48,
        critical_anomaly_rate: float = 0.35,
        warning_anomaly_rate: float = 0.15,
        consecutive_fail_limit: int = 5,
    ):
        self.station_id = station_id
        self.window_size = window_size
        self.critical_anomaly_rate = critical_anomaly_rate
        self.warning_anomaly_rate = warning_anomaly_rate
        self.consecutive_fail_limit = consecutive_fail_limit

        self.history: deque = deque(maxlen=window_size)
        self.consecutive_failures = 0
        self.last_healthy_timestamp: Optional[str] = None
        self.accumulated_drift = 0.0

    def update(
        self,
        timestamp: str,
        is_anomaly: bool,
        is_missing: bool = False,
        drift_delta: float = 0.0,
    ) -> SensorHealthMetric:
        """Updates health status with the latest reading observation."""
        self.history.append({
            "timestamp": timestamp,
            "is_anomaly": is_anomaly,
            "is_missing": is_missing,
        })

        if is_anomaly:
            self.consecutive_failures += 1
            self.accumulated_drift += abs(drift_delta)
        else:
            self.consecutive_failures = 0
            self.last_healthy_timestamp = timestamp

        n = len(self.history)
        anom_count = sum(1 for item in self.history if item["is_anomaly"])
        missing_count = sum(1 for item in self.history if item["is_missing"])

        anom_rate = anom_count / float(n) if n > 0 else 0.0
        missing_rate = missing_count / float(n) if n > 0 else 0.0

        # Health score computation (100% down to 0%)
        # Penalized by anomaly rate, missing data, and consecutive failures
        penalty = (anom_rate * 55.0) + (missing_rate * 30.0) + (min(10, self.consecutive_failures) * 3.5)
        health_score = float(np.clip(100.0 - penalty, 0.0, 100.0))

        # Status and Action determination
        if self.consecutive_failures >= self.consecutive_fail_limit or health_score < 40.0:
            status = "CRITICAL"
            action = "Urgent: Sensor failure suspected. Immediate on-site technician inspection required."
            days_to_maintenance = 1
        elif anom_rate >= self.warning_anomaly_rate or health_score < 75.0:
            status = "DEGRADED"
            action = "Warning: Intermittent anomalies detected. Schedule recalibration within 7 days."
            days_to_maintenance = 7
        else:
            status = "HEALTHY"
            action = "Nominal: Sensor operating within standard WMO parameters. No action required."
            days_to_maintenance = 90

        return SensorHealthMetric(
            health_score_pct=round(health_score, 1),
            rolling_anomaly_rate=round(anom_rate, 3),
            consecutive_failures=self.consecutive_failures,
            missing_data_ratio=round(missing_rate, 3),
            drift_indicator=round(self.accumulated_drift, 2),
            status=status,
            recommended_action=action,
            predicted_maintenance_days=days_to_maintenance,
        )
