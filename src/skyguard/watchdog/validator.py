"""
SkyGuard AI — Timestamp Integrity & Data Quality Validator
Validates every incoming reading against physical and temporal constraints, assigning
immutable quality states (GOOD, SUSPECT, BAD, MISSING, CORRECTED) and quality flags.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from skyguard.config.settings import SETTINGS


class QualityState:
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    BAD = "BAD"
    MISSING = "MISSING"
    CORRECTED = "CORRECTED"


class TimestampValidator:
    """Validates timestamp integrity and data quality for AWS sensor telemetry."""

    def __init__(self):
        # Store last seen timestamp per station for order/duplicate checking
        self.last_seen_timestamps: Dict[str, datetime] = {}

    def validate_reading(self, reading_data: Dict[str, Any], current_time: Optional[datetime] = None) -> Tuple[str, Dict[str, bool]]:
        """
        Validates timestamp integrity and sensor availability.
        
        Returns:
            Tuple of (quality_state, quality_flags_dict)
        """
        now = current_time or datetime.now(timezone.utc)
        flags = {
            "missing_timestamp": False,
            "invalid_timestamp": False,
            "future_timestamp": False,
            "duplicate_timestamp": False,
            "out_of_order": False,
            "excessive_clock_jump": False,
            "stale_data": False,
            "missing_values": False,
        }

        station_id = reading_data.get("station_id", "UNKNOWN")
        raw_ts = reading_data.get("timestamp")

        # 1. Missing timestamp check
        if not raw_ts:
            flags["missing_timestamp"] = True
            return QualityState.BAD, flags

        # 2. Parse timestamp
        parsed_ts: Optional[datetime] = None
        if isinstance(raw_ts, datetime):
            parsed_ts = raw_ts
        else:
            try:
                # Handle ISO format strings
                ts_str = str(raw_ts).replace("Z", "+00:00")
                parsed_ts = datetime.fromisoformat(ts_str)
            except Exception:
                flags["invalid_timestamp"] = True
                return QualityState.BAD, flags

        if parsed_ts.tzinfo is None:
            parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)

        # 3. Future timestamp check
        delta_future = (parsed_ts - now).total_seconds()
        if delta_future > SETTINGS.max_clock_skew_seconds:
            flags["future_timestamp"] = True
            return QualityState.BAD, flags

        # 4. Station order & duplicate check
        if station_id in self.last_seen_timestamps:
            last_ts = self.last_seen_timestamps[station_id]
            diff = (parsed_ts - last_ts).total_seconds()

            if diff == 0:
                flags["duplicate_timestamp"] = True
            elif diff < 0:
                flags["out_of_order"] = True
            elif diff > SETTINGS.max_out_of_order_gap_seconds:
                flags["excessive_clock_jump"] = True

        # Update last seen timestamp if not out of order or duplicate
        if not flags["out_of_order"] and not flags["duplicate_timestamp"]:
            self.last_seen_timestamps[station_id] = parsed_ts

        # 5. Missing sensor values check
        temp = reading_data.get("temperature")
        pres = reading_data.get("pressure")
        humi = reading_data.get("humidity")

        if temp is None and pres is None and humi is None:
            flags["missing_values"] = True
            return QualityState.MISSING, flags

        # 6. Determine final quality state
        if flags["duplicate_timestamp"] or flags["out_of_order"] or flags["excessive_clock_jump"]:
            return QualityState.SUSPECT, flags
        
        if temp is None or pres is None or humi is None:
            return QualityState.SUSPECT, flags

        return QualityState.GOOD, flags
