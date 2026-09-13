"""
SkyGuard AI — Deterministic Anomaly Injector
Injects 10 canonical anomaly classes into baseline NOAA weather telemetry with ground-truth labels.
Preserves original clean observations for precision/recall evaluation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from skyguard.config.contracts import AnomalyCategory


@dataclass
class AnomalyInjectionMeta:
    injection_id: str
    anomaly_type: str
    affected_sensor: str
    start_idx: int
    end_idx: int
    severity: str
    root_cause: str


class AnomalyInjector:
    """Deterministic synthetic anomaly injector supporting all 10 canonical anomaly classes."""

    def __init__(self, random_seed: int = 42):
        self.rng = np.random.default_rng(random_seed)

    def inject_spike(
        self,
        df: pd.DataFrame,
        sensor: str = "temperature",
        start_idx: Optional[int] = None,
        jump_val: Optional[float] = None,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 1: Spike / Outlier (Single reading jump and immediate revert)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, n - 5)

        if jump_val is None:
            if sensor == "temperature":
                jump_val = self.rng.choice([15.0, 18.0, 22.0]) * self.rng.choice([-1, 1])
            elif sensor == "pressure":
                jump_val = self.rng.choice([12.0, 15.0, 20.0]) * self.rng.choice([-1, 1])
            else:
                jump_val = self.rng.choice([30.0, 40.0, 50.0]) * self.rng.choice([-1, 1])

        out.loc[idx, sensor] = out.loc[idx, sensor] + jump_val
        out.loc[idx, "is_anomaly"] = 1
        out.loc[idx, "anomaly_type"] = AnomalyCategory.SENSOR_SPIKE.value
        out.loc[idx, "affected_sensor"] = sensor
        out.loc[idx, "ground_truth_root_cause"] = "Sensor Spike: Transient electrical impulse or hardware glitch"

        meta = AnomalyInjectionMeta(
            injection_id=f"SPIKE_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.SENSOR_SPIKE.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=idx + 1,
            severity="MEDIUM",
            root_cause="Sensor Spike",
        )
        return out, meta

    def inject_frozen(
        self,
        df: pd.DataFrame,
        sensor: str = "humidity",
        start_idx: Optional[int] = None,
        duration: int = 12,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 2: Frozen / Stuck Sensor (Sensor reports identical reading for >= duration steps)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)

        frozen_val = float(out.loc[idx, sensor])
        out.loc[idx:end_idx, sensor] = frozen_val
        out.loc[idx:end_idx, "is_anomaly"] = 1
        out.loc[idx:end_idx, "anomaly_type"] = AnomalyCategory.FROZEN_SENSOR.value
        out.loc[idx:end_idx, "affected_sensor"] = sensor
        out.loc[idx:end_idx, "ground_truth_root_cause"] = "Stuck Sensor: Mechanical or ADC latchup"

        meta = AnomalyInjectionMeta(
            injection_id=f"FROZEN_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.FROZEN_SENSOR.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=end_idx,
            severity="HIGH",
            root_cause="Stuck Sensor",
        )
        return out, meta

    def inject_calibration_drift(
        self,
        df: pd.DataFrame,
        sensor: str = "pressure",
        start_idx: Optional[int] = None,
        duration: int = 48,
        drift_rate: float = 0.25,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 3: Calibration Drift (Gradual cumulative deviation over multiple days)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)
        drift_steps = end_idx - idx

        drift_curve = np.linspace(0.0, drift_rate * drift_steps, drift_steps)
        out.loc[idx:end_idx - 1, sensor] = out.loc[idx:end_idx - 1, sensor].values + drift_curve
        out.loc[idx:end_idx - 1, "is_anomaly"] = 1
        out.loc[idx:end_idx - 1, "anomaly_type"] = AnomalyCategory.CALIBRATION_DRIFT.value
        out.loc[idx:end_idx - 1, "affected_sensor"] = sensor
        out.loc[idx:end_idx - 1, "ground_truth_root_cause"] = "Calibration Drift: Transducer aging or membrane creep"

        meta = AnomalyInjectionMeta(
            injection_id=f"DRIFT_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.CALIBRATION_DRIFT.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=end_idx,
            severity="MEDIUM",
            root_cause="Calibration Drift",
        )
        return out, meta

    def inject_communication_dropout(
        self,
        df: pd.DataFrame,
        sensor: str = "all",
        start_idx: Optional[int] = None,
        duration: int = 6,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 4: Communication Dropout (telemetry lost / NaN values)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)

        cols = ["temperature", "pressure", "humidity"] if sensor == "all" else [sensor]
        for col in cols:
            out.loc[idx:end_idx - 1, col] = np.nan

        out.loc[idx:end_idx - 1, "is_anomaly"] = 1
        out.loc[idx:end_idx - 1, "anomaly_type"] = AnomalyCategory.COMMUNICATION_DROPOUT.value
        out.loc[idx:end_idx - 1, "affected_sensor"] = sensor
        out.loc[idx:end_idx - 1, "ground_truth_root_cause"] = "Communication Dropout: Telemetry RF/Cellular outage"

        meta = AnomalyInjectionMeta(
            injection_id=f"DROPOUT_{idx}",
            anomaly_type=AnomalyCategory.COMMUNICATION_DROPOUT.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=end_idx,
            severity="LOW",
            root_cause="Communication Dropout",
        )
        return out, meta

    def inject_packet_corruption(
        self,
        df: pd.DataFrame,
        sensor: str = "temperature",
        start_idx: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 5: Packet Corruption (Bit shifts or decimal place errors, e.g. 26.5°C -> 265.0°C)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, n - 5)

        curr_val = out.loc[idx, sensor]
        out.loc[idx, sensor] = curr_val * 10.0  # Decadic framing error
        out.loc[idx, "is_anomaly"] = 1
        out.loc[idx, "anomaly_type"] = AnomalyCategory.PACKET_CORRUPTION.value
        out.loc[idx, "affected_sensor"] = sensor
        out.loc[idx, "ground_truth_root_cause"] = "Packet Corruption: UART baud framing or bit-flip error"

        meta = AnomalyInjectionMeta(
            injection_id=f"CORRUPT_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.PACKET_CORRUPTION.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=idx + 1,
            severity="CRITICAL",
            root_cause="Packet Corruption",
        )
        return out, meta

    def inject_physical_inconsistency(
        self,
        df: pd.DataFrame,
        start_idx: Optional[int] = None,
        duration: int = 4,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 6: Physical Inconsistency (Temp drops drastically while humidity drops or dew-point exceeds T)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)

        # Force temperature below dew point by dropping T to 5°C with 95% humidity
        out.loc[idx:end_idx - 1, "temperature"] = 2.0
        out.loc[idx:end_idx - 1, "humidity"] = 99.0
        out.loc[idx:end_idx - 1, "is_anomaly"] = 1
        out.loc[idx:end_idx - 1, "anomaly_type"] = AnomalyCategory.PHYSICAL_INCONSISTENCY.value
        out.loc[idx:end_idx - 1, "affected_sensor"] = "temperature"
        out.loc[idx:end_idx - 1, "ground_truth_root_cause"] = "Physical Inconsistency: Thermodynamic cross-sensor violation"

        meta = AnomalyInjectionMeta(
            injection_id=f"PHYS_INCONSIST_{idx}",
            anomaly_type=AnomalyCategory.PHYSICAL_INCONSISTENCY.value,
            affected_sensor="temperature_humidity",
            start_idx=idx,
            end_idx=end_idx,
            severity="HIGH",
            root_cause="Physical Inconsistency",
        )
        return out, meta

    def inject_noise_jitter(
        self,
        df: pd.DataFrame,
        sensor: str = "temperature",
        start_idx: Optional[int] = None,
        duration: int = 16,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 7: Noise / Jitter (High-frequency erratic fluctuations)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)
        noise_steps = end_idx - idx

        noise = self.rng.normal(0.0, 3.5, size=noise_steps)
        out.loc[idx:end_idx - 1, sensor] = out.loc[idx:end_idx - 1, sensor].values + noise
        out.loc[idx:end_idx - 1, "is_anomaly"] = 1
        out.loc[idx:end_idx - 1, "anomaly_type"] = AnomalyCategory.NOISE_JITTER.value
        out.loc[idx:end_idx - 1, "affected_sensor"] = sensor
        out.loc[idx:end_idx - 1, "ground_truth_root_cause"] = "Sensor Noise: High impedance ground loop or RF interference"

        meta = AnomalyInjectionMeta(
            injection_id=f"NOISE_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.NOISE_JITTER.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=end_idx,
            severity="MEDIUM",
            root_cause="Noise / Jitter",
        )
        return out, meta

    def inject_range_violation(
        self,
        df: pd.DataFrame,
        sensor: str = "temperature",
        start_idx: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 8: Range Violation (Reading outside physical climatological limits in India)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, n - 5)

        val = 63.5 if sensor == "temperature" else (1150.0 if sensor == "pressure" else 135.0)
        out.loc[idx, sensor] = val
        out.loc[idx, "is_anomaly"] = 1
        out.loc[idx, "anomaly_type"] = AnomalyCategory.RANGE_VIOLATION.value
        out.loc[idx, "affected_sensor"] = sensor
        out.loc[idx, "ground_truth_root_cause"] = "Range Violation: Reading beyond Indian climatological envelope"

        meta = AnomalyInjectionMeta(
            injection_id=f"RANGE_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.RANGE_VIOLATION.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=idx + 1,
            severity="CRITICAL",
            root_cause="Range Violation",
        )
        return out, meta

    def inject_spatial_inconsistency(
        self,
        df: pd.DataFrame,
        sensor: str = "temperature",
        start_idx: Optional[int] = None,
        duration: int = 8,
        delta: float = 14.0,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 9: Spatial Inconsistency (Single station diverges while local mesonet is calm)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)

        out.loc[idx:end_idx - 1, sensor] = out.loc[idx:end_idx - 1, sensor].values + delta
        out.loc[idx:end_idx - 1, "is_anomaly"] = 1
        out.loc[idx:end_idx - 1, "anomaly_type"] = AnomalyCategory.SPATIAL_INCONSISTENCY.value
        out.loc[idx:end_idx - 1, "affected_sensor"] = sensor
        out.loc[idx:end_idx - 1, "ground_truth_root_cause"] = "Spatial Inconsistency: Isolated station bias vs mesonet cluster"

        meta = AnomalyInjectionMeta(
            injection_id=f"SPATIAL_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.SPATIAL_INCONSISTENCY.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=end_idx,
            severity="HIGH",
            root_cause="Spatial Inconsistency",
        )
        return out, meta

    def inject_temporal_pattern_break(
        self,
        df: pd.DataFrame,
        sensor: str = "temperature",
        start_idx: Optional[int] = None,
        duration: int = 24,
    ) -> Tuple[pd.DataFrame, AnomalyInjectionMeta]:
        """Class 10: Temporal Pattern Break (Diurnal cycle absent / flat line during day)."""
        out = df.copy()
        n = len(out)
        idx = start_idx if start_idx is not None else self.rng.integers(5, max(6, n - duration - 5))
        end_idx = min(idx + duration, n)

        mean_val = float(out.loc[idx:end_idx - 1, sensor].mean())
        out.loc[idx:end_idx - 1, sensor] = mean_val
        out.loc[idx:end_idx - 1, "is_anomaly"] = 1
        out.loc[idx:end_idx - 1, "anomaly_type"] = AnomalyCategory.TEMPORAL_PATTERN_BREAK.value
        out.loc[idx:end_idx - 1, "affected_sensor"] = sensor
        out.loc[idx:end_idx - 1, "ground_truth_root_cause"] = "Temporal Pattern Break: Diurnal solar cycle lost"

        meta = AnomalyInjectionMeta(
            injection_id=f"PATTERN_BREAK_{sensor.upper()}_{idx}",
            anomaly_type=AnomalyCategory.TEMPORAL_PATTERN_BREAK.value,
            affected_sensor=sensor,
            start_idx=idx,
            end_idx=end_idx,
            severity="MEDIUM",
            root_cause="Temporal Pattern Break",
        )
        return out, meta
