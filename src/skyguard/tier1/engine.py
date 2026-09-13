"""
SkyGuard AI — Tier 1 Deterministic QC Engine
Coordinates individual QC rules and produces aggregate explainable Tier 1 decisions.
Latency budget: < 0.2 ms on modern x86 / < 1 ms on ESP32.
"""

import time
from typing import Any, Dict, Optional, Union
import numpy as np

from skyguard.config.contracts import QCStatus, Severity, Tier1Output
from .rules import Tier1Rules


class Tier1Engine:
    """Deterministic Quality Control engine executing all rules in sequence."""

    def __init__(self, rules: Optional[Tier1Rules] = None):
        self.rules = rules or Tier1Rules()

    def evaluate(
        self,
        temp: Optional[float],
        pres: Optional[float],
        humi: Optional[float],
        features: Dict[str, float],
        latitude: Optional[float] = None,
        timestamp: Optional[Any] = None,
        is_precipitating: Optional[bool] = None,
    ) -> Tier1Output:
        """Executes all Tier 1 QC rules on the current reading and engineered features."""
        t0 = time.perf_counter()

        lat = latitude if latitude is not None else (features.get("latitude") if features else 20.0)
        
        # Determine month for seasonal climatological check
        month = None
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                month = dt.month
            except Exception:
                pass
        if month is None and features and "month" in features:
            month = int(features["month"])

        results = [
            self.rules.check_missing(temp, pres, humi),
            self.rules.check_range(temp, pres, humi),
            self.rules.check_seasonal_range(temp, pres, humi, latitude=lat, month=month, features=features),
            self.rules.check_rain_thermal_consistency(temp, humi, features=features, is_precipitating=is_precipitating),
            self.rules.check_step(features),
            self.rules.check_persistence(features),
            self.rules.check_dew_point_consistency(features),
        ]

        fired_rules = []
        has_critical = False
        has_high = False
        has_fail = False

        for r in results:
            if not r.passed:
                fired_rules.append(r.rule_name)
                has_fail = True
                if r.severity == Severity.CRITICAL:
                    has_critical = True
                elif r.severity == Severity.HIGH:
                    has_high = True

        # Aggregate status determination: Critical rules or stuck sensors trigger FAIL; single transient steps trigger SUSPECT
        is_stuck = "PERSISTENCE_CHECK" in fired_rules
        if has_critical or is_stuck or (has_high and len(fired_rules) > 1):
            status = QCStatus.FAIL
        elif has_fail:
            status = QCStatus.SUSPECT
        else:
            status = QCStatus.PASS

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return Tier1Output(
            status=status,
            rules_fired=fired_rules,
            rule_results=results,
            latency_ms=latency_ms,
        )
