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

    def check_seasonal_range(
        self,
        temp: Optional[float],
        pres: Optional[float],
        humi: Optional[float],
        latitude: Optional[float] = None,
        month: Optional[int] = None,
        features: Optional[Dict[str, float]] = None,
    ) -> RuleResult:
        """
        Seasonal and geographical climatological range check based on IMD (India Meteorological Department)
        monsoon, pre-monsoon, post-monsoon, and winter temperature envelopes.
        """
        if temp is None or np.isnan(temp):
            return RuleResult(
                rule_name="SEASONAL_RANGE_CHECK",
                passed=False,
                severity=Severity.LOW,
                message="Cannot perform seasonal check on missing temperature value",
                evidence={"temp": temp},
            )

        lat = latitude if latitude is not None else (features.get("latitude") if features else 20.0)
        if lat is None:
            lat = 20.0

        m = month
        if m is None and features:
            m = int(features.get("month", 0)) if features.get("month") else None
        if m is None:
            from datetime import datetime
            m = datetime.now().month

        violations = []

        # 1. Southwest Monsoon Season (June - September: Months 6, 7, 8, 9)
        # Deep cloud cover, high albedo, maritime monsoonal air mass severely suppresses surface heating.
        if m in (6, 7, 8, 9):
            # Zone A: Coastal & Peninsular India (lat < 23.0°N, e.g. Mumbai, Goa, Kerala, Karnataka coast, Chennai)
            # All-time historical IMD extreme maximums for Mumbai: July 34.8°C, Aug 33.5°C, Sept 36.4°C.
            if lat < 23.0:
                max_allowed_temp = 36.5
                if temp > max_allowed_temp:
                    violations.append(
                        f"Temperature {temp:.1f}°C exceeds Southwest Monsoon ceiling ({max_allowed_temp}°C) "
                        f"for Peninsular/Coastal India (lat={lat:.2f}°N in month {m})"
                    )
            # Zone B: North / Central Plains (lat 23.0°N to 30.0°N, e.g. Delhi, Rajasthan, UP, MP)
            elif lat < 30.0:
                max_allowed_temp = 41.5
                if temp > max_allowed_temp:
                    violations.append(
                        f"Temperature {temp:.1f}°C exceeds Southwest Monsoon ceiling ({max_allowed_temp}°C) "
                        f"for Northern/Central Plains (lat={lat:.2f}°N in month {m})"
                    )
            # Zone C: Himalayan / High Altitude (lat >= 30.0°N)
            else:
                max_allowed_temp = 33.0
                if temp > max_allowed_temp:
                    violations.append(
                        f"Temperature {temp:.1f}°C exceeds Monsoon ceiling ({max_allowed_temp}°C) "
                        f"for Himalayan/Mountain station (lat={lat:.2f}°N in month {m})"
                    )

        # 2. Winter Season (December - February: Months 12, 1, 2)
        elif m in (12, 1, 2):
            if lat >= 30.0:
                max_allowed_temp = 22.0
                if temp > max_allowed_temp:
                    violations.append(
                        f"Temperature {temp:.1f}°C exceeds Winter ceiling ({max_allowed_temp}°C) "
                        f"for Northern/Himalayan region (lat={lat:.2f}°N in month {m})"
                    )
            elif lat >= 23.0:
                max_allowed_temp = 33.5
                if temp > max_allowed_temp:
                    violations.append(
                        f"Temperature {temp:.1f}°C exceeds Winter ceiling ({max_allowed_temp}°C) "
                        f"for Northern/Central India (lat={lat:.2f}°N in month {m})"
                    )

        # 3. Post-Monsoon Season (October - November: Months 10, 11)
        elif m in (10, 11):
            if lat < 23.0:
                max_allowed_temp = 37.5
                if temp > max_allowed_temp:
                    violations.append(
                        f"Temperature {temp:.1f}°C exceeds Post-Monsoon ceiling ({max_allowed_temp}°C) "
                        f"for Peninsular India (lat={lat:.2f}°N in month {m})"
                    )

        if violations:
            return RuleResult(
                rule_name="SEASONAL_RANGE_CHECK",
                passed=False,
                severity=Severity.CRITICAL,
                message="; ".join(violations),
                evidence={"temp": temp, "latitude": lat, "month": m, "violations": violations},
            )

        return RuleResult(
            rule_name="SEASONAL_RANGE_CHECK",
            passed=True,
            severity=Severity.NORMAL,
            message=f"Temperature {temp:.1f}°C conforms to seasonal climatological envelope (Month {m}, Lat {lat:.1f}°N)",
            evidence={"temp": temp, "latitude": lat, "month": m},
        )

    def check_rain_thermal_consistency(
        self,
        temp: Optional[float],
        humi: Optional[float],
        features: Optional[Dict[str, float]] = None,
        is_precipitating: Optional[bool] = None,
    ) -> RuleResult:
        """
        Thermodynamic precipitation & wet-bulb evaporative cooling consistency check.
        Under active rainfall or saturated relative humidity (RH >= 80%), evaporative cooling
        enforces a strict upper thermal limit on surface air (max 33.5°C).
        Furthermore, tropospheric vapor pressure cannot physically exceed 42.0 hPa on Earth.
        """
        if temp is None or np.isnan(temp):
            return RuleResult(
                rule_name="RAIN_THERMAL_INCONSISTENCY",
                passed=False,
                severity=Severity.LOW,
                message="Cannot perform rain-thermal consistency check on missing temperature",
                evidence={"temp": temp},
            )

        h_val = humi if humi is not None and not np.isnan(humi) else (features.get("humi", 50.0) if features else 50.0)
        rain_active = bool(is_precipitating)

        import math
        # Compute or retrieve actual water vapor partial pressure e (hPa)
        e_vap = features.get("vap_pres") if features else None
        if e_vap is None or e_vap <= 0.0:
            e_sat = 6.112 * math.exp((17.67 * temp) / (temp + 243.5))
            e_vap = (h_val / 100.0) * e_sat

        violations = []

        # 1. Evaporative Cooling Limit during Active Rainfall
        # Sub-cloud rain droplet evaporation cools the air towards the wet-bulb temperature.
        # In India, air temperature during active rainfall never exceeds 33.5°C.
        if rain_active and temp > 33.5:
            violations.append(
                f"Air temperature {temp:.1f}°C during active rainfall exceeds thermodynamic wet-bulb envelope (max 33.5°C). "
                f"Rain droplet sub-cloud evaporation enforces strict thermal cooling."
            )

        # 2. Saturated Moisture-Thermal Inconsistency
        # At RH >= 85%, temperature > 34.0°C generates an impossible wet-bulb runaway (Tw > 32°C)
        elif h_val >= 85.0 and temp > 34.0:
            violations.append(
                f"Saturated moisture-thermal inconsistency: Relative humidity {h_val:.1f}% with temperature {temp:.1f}°C "
                f"generates an unphysical wet-bulb condition. Monsoonal precipitation air masses cannot sustain T > 34.0°C at saturation."
            )
        elif h_val >= 80.0 and temp > 35.5:
            violations.append(
                f"High humidity ({h_val:.1f}%) with extreme heat ({temp:.1f}°C) violates atmospheric evaporative equilibrium."
            )

        # 3. Maximum Earth Tropospheric Vapor Pressure Ceiling (42.0 hPa)
        # Saturated vapor pressure at 44°C and 85% RH would be ~77 hPa, violating physical laws.
        if e_vap > 42.0:
            violations.append(
                f"Thermodynamic vapor pressure violation: Actual water vapor partial pressure {e_vap:.1f} hPa exceeds "
                f"Earth's atmospheric surface maximum (42.0 hPa). Saturated air at {temp:.1f}°C is physically impossible."
            )

        if violations:
            return RuleResult(
                rule_name="RAIN_THERMAL_INCONSISTENCY",
                passed=False,
                severity=Severity.CRITICAL,
                message="; ".join(violations),
                evidence={"temp": temp, "humi": h_val, "vap_pres": round(e_vap, 2), "is_precipitating": rain_active},
            )

        return RuleResult(
            rule_name="RAIN_THERMAL_INCONSISTENCY",
            passed=True,
            severity=Severity.NORMAL,
            message="Temperature and atmospheric moisture conform to precipitation evaporative equilibrium",
            evidence={"temp": temp, "humi": h_val, "vap_pres": round(e_vap, 2), "is_precipitating": rain_active},
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
