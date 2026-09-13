"""
SkyGuard AI — Tier 1 Deterministic WMO QC Rules
Implements explainable WMO/IMD meteorological quality-control checks:
- Physical Range Checks (Patro & Bartakke Table II)
- Step / Rate-of-change Checks (4-sigma & physical rate limits)
- Persistence Checks (Stuck sensor detection)
- Dew-point Invariant Check (Td <= T)
- Cross-parameter Consistency
- Telemetry Dropout / Missing Value Check
"""

from typing import Dict, Any, List, Optional
import numpy as np

from skyguard.config.contracts import RuleResult, Severity


class Tier1Rules:
    """Individual deterministic QC rules for AWS sensor readings."""

    def __init__(
        self,
        temp_range: tuple = (-40.0, 55.0),
        pres_range: tuple = (500.0, 1080.0),
        humi_range: tuple = (0.0, 100.0),
        max_step_temp: float = 6.0,
        max_step_pres: float = 5.0,
        max_step_humi: float = 30.0,
        persistence_limit: int = 6,
    ):
        self.temp_range = temp_range
        self.pres_range = pres_range
        self.humi_range = humi_range
        self.max_step_temp = max_step_temp
        self.max_step_pres = max_step_pres
        self.max_step_humi = max_step_humi
        self.persistence_limit = persistence_limit

    def check_range(self, temp: Optional[float], pres: Optional[float], humi: Optional[float]) -> RuleResult:
        """Flags readings outside physically possible atmospheric limits in India."""
        if temp is None or pres is None or humi is None or np.isnan(temp) or np.isnan(pres) or np.isnan(humi):
            return RuleResult(
                rule_name="RANGE_CHECK",
                passed=False,
                severity=Severity.LOW,
                message="Cannot perform range check on missing telemetry values",
                evidence={"temp": temp, "pres": pres, "humi": humi},
            )

        violations = []
        if not (self.temp_range[0] <= temp <= self.temp_range[1]):
            violations.append(f"Temperature {temp:.1f}°C outside [{self.temp_range[0]}, {self.temp_range[1]}]")
        if not (self.pres_range[0] <= pres <= self.pres_range[1]):
            violations.append(f"Pressure {pres:.1f} hPa outside [{self.pres_range[0]}, {self.pres_range[1]}]")
        if not (self.humi_range[0] <= humi <= self.humi_range[1]):
            violations.append(f"Humidity {humi:.1f}% outside [{self.humi_range[0]}, {self.humi_range[1]}]")

        if violations:
            return RuleResult(
                rule_name="RANGE_CHECK",
                passed=False,
                severity=Severity.CRITICAL,
                message="; ".join(violations),
                evidence={"temp": temp, "pres": pres, "humi": humi, "violations": violations},
            )
        return RuleResult(
            rule_name="RANGE_CHECK",
            passed=True,
            severity=Severity.NORMAL,
            message="All sensor readings within valid climatological bounds",
            evidence={"temp": temp, "pres": pres, "humi": humi},
        )

    def check_step(self, features: Dict[str, float]) -> RuleResult:
        """Flags rate-of-change jumps exceeding 4-sigma or absolute step limits."""
        dt = abs(features.get("temp_delta_1", 0.0))
        dp = abs(features.get("pres_delta_1", 0.0))
        dh = abs(features.get("humi_delta_1", 0.0))

        # 4-sigma check using 6h rolling std
        sigma_t = features.get("temp_rstd_6h", 0.0)
        sigma_p = features.get("pres_rstd_6h", 0.0)
        sigma_h = features.get("humi_rstd_6h", 0.0)

        violations = []
        if dt > self.max_step_temp or (sigma_t > 0.1 and dt > 4.0 * sigma_t and dt > 3.0):
            violations.append(f"Temp step jump {dt:.1f}°C/h exceeds limit (max={self.max_step_temp}, 4σ={4*sigma_t:.1f})")
        if dp > self.max_step_pres or (sigma_p > 0.1 and dp > 4.0 * sigma_p and dp > 2.5):
            violations.append(f"Pres step jump {dp:.1f} hPa/h exceeds limit (max={self.max_step_pres}, 4σ={4*sigma_p:.1f})")
        if dh > self.max_step_humi or (sigma_h > 0.5 and dh > 4.0 * sigma_h and dh > 15.0):
            violations.append(f"Humi step jump {dh:.1f}%/h exceeds limit (max={self.max_step_humi}, 4σ={4*sigma_h:.1f})")

        if violations:
            return RuleResult(
                rule_name="STEP_CHECK",
                passed=False,
                severity=Severity.HIGH,
                message="; ".join(violations),
                evidence={"temp_delta": dt, "pres_delta": dp, "humi_delta": dh},
            )
        return RuleResult(
            rule_name="STEP_CHECK",
            passed=True,
            severity=Severity.NORMAL,
            message="Rates of change consistent with atmospheric gradient",
            evidence={"temp_delta": dt, "pres_delta": dp, "humi_delta": dh},
        )

    def check_persistence(self, features: Dict[str, float]) -> RuleResult:
        """Flags sensor reporting constant unchanged values for consecutive readings."""
        t_len = features.get("temp_persist_len", 0.0)
        p_len = features.get("pres_persist_len", 0.0)
        h_len = features.get("humi_persist_len", 0.0)

        stuck = []
        if t_len >= self.persistence_limit:
            stuck.append(f"Temperature stuck for {int(t_len)} consecutive readings")
        if p_len >= self.persistence_limit:
            stuck.append(f"Pressure stuck for {int(p_len)} consecutive readings")
        if h_len >= self.persistence_limit:
            stuck.append(f"Humidity stuck for {int(h_len)} consecutive readings")

        if stuck:
            return RuleResult(
                rule_name="PERSISTENCE_CHECK",
                passed=False,
                severity=Severity.HIGH,
                message="; ".join(stuck),
                evidence={"temp_persist": t_len, "pres_persist": p_len, "humi_persist": h_len},
            )
        return RuleResult(
            rule_name="PERSISTENCE_CHECK",
            passed=True,
            severity=Severity.NORMAL,
            message="Sensor output exhibits normal dynamic variance",
            evidence={"temp_persist": t_len, "pres_persist": p_len, "humi_persist": h_len},
        )

    def check_dew_point_consistency(self, features: Dict[str, float]) -> RuleResult:
        """Thermodynamic invariant check: Dew point temperature can never exceed air temperature."""
        dp_depress = features.get("dp_depress", 0.0)
        temp = features.get("temp", 0.0)
        dew_point = features.get("dew_point", 0.0)

        # Allow 0.1°C tolerance for rounding and sensor discretization
        if dp_depress < -0.1:
            return RuleResult(
                rule_name="DEW_POINT_INVARIANT",
                passed=False,
                severity=Severity.CRITICAL,
                message=f"Thermodynamic violation: Dew point ({dew_point:.1f}°C) exceeds air temperature ({temp:.1f}°C)",
                evidence={"temp": temp, "dew_point": dew_point, "dp_depress": dp_depress},
            )
        return RuleResult(
            rule_name="DEW_POINT_INVARIANT",
            passed=True,
            severity=Severity.NORMAL,
            message="Dew point thermodynamically consistent with air temperature",
            evidence={"temp": temp, "dew_point": dew_point, "dp_depress": dp_depress},
        )

    def check_missing(self, temp: Optional[float], pres: Optional[float], humi: Optional[float]) -> RuleResult:
        """Flags missing or unreadable telemetry values."""
        missing = []
        if temp is None or np.isnan(temp):
            missing.append("temperature")
        if pres is None or np.isnan(pres):
            missing.append("pressure")
        if humi is None or np.isnan(humi):
            missing.append("humidity")

        if missing:
            return RuleResult(
                rule_name="MISSING_DATA_CHECK",
                passed=False,
                severity=Severity.LOW if len(missing) < 3 else Severity.MEDIUM,
                message=f"Missing telemetry readings for: {', '.join(missing)}",
                evidence={"missing_sensors": missing},
            )
        return RuleResult(
            rule_name="MISSING_DATA_CHECK",
            passed=True,
            severity=Severity.NORMAL,
            message="All sensor telemetry fields present",
            evidence={"missing_sensors": []},
        )
