"""
SkyGuard AI — Canonical Data Contracts and Schemas
Defines strictly-typed data models for input sensor telemetry, Tier 1 rule evaluations,
Tier 2 edge ML inference, Tier 3 cloud diagnostics, explainability reports, and health metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import numpy as np


class Severity(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class QCStatus(str, Enum):
    PASS = "PASS"
    SUSPECT = "SUSPECT"
    FAIL = "FAIL"


class AnomalyCategory(str, Enum):
    NONE = "NONE"
    GENUINE_WEATHER_EVENT = "GENUINE_WEATHER_EVENT"
    SENSOR_SPIKE = "SENSOR_SPIKE"
    FROZEN_SENSOR = "FROZEN_SENSOR"
    CALIBRATION_DRIFT = "CALIBRATION_DRIFT"
    COMMUNICATION_DROPOUT = "COMMUNICATION_DROPOUT"
    PACKET_CORRUPTION = "PACKET_CORRUPTION"
    PHYSICAL_INCONSISTENCY = "PHYSICAL_INCONSISTENCY"
    NOISE_JITTER = "NOISE_JITTER"
    RANGE_VIOLATION = "RANGE_VIOLATION"
    SPATIAL_INCONSISTENCY = "SPATIAL_INCONSISTENCY"
    TEMPORAL_PATTERN_BREAK = "TEMPORAL_PATTERN_BREAK"


@dataclass
class SensorReading:
    """Canonical input telemetry reading from an Automatic Weather Station (AWS)."""
    timestamp: Union[str, datetime]
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    temperature: Optional[float]  # °C
    pressure: Optional[float]     # hPa
    humidity: Optional[float]     # %
    elevation_m: Optional[float] = None
    battery_voltage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        ts = self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp)
        return {
            "timestamp": ts,
            "station_id": self.station_id,
            "station_name": self.station_name,
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
            "temperature": None if self.temperature is None or np.isnan(self.temperature) else float(self.temperature),
            "pressure": None if self.pressure is None or np.isnan(self.pressure) else float(self.pressure),
            "humidity": None if self.humidity is None or np.isnan(self.humidity) else float(self.humidity),
            "elevation_m": self.elevation_m,
            "battery_voltage": self.battery_voltage,
        }


@dataclass
class RuleResult:
    """Outcome of a single deterministic QC rule."""
    rule_name: str
    passed: bool
    severity: Severity
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tier1Output:
    """Aggregate result from the Tier 1 deterministic rule engine."""
    status: QCStatus
    rules_fired: List[str]
    rule_results: List[RuleResult]
    latency_ms: float = 0.0


@dataclass
class Tier2Output:
    """Result from the Tier 2 compact edge autoencoder."""
    reconstruction_error: float
    anomaly_score: float  # 0.0 to 1.0
    is_anomaly: bool
    threshold: float
    latency_ms: float = 0.0


@dataclass
class Stage1ForecastOutput:
    """Result from Tier 3 Stage 1 state-space Kalman forecaster."""
    predicted_temp: float
    predicted_pres: float
    predicted_humi: float
    residual_temp: float
    residual_pres: float
    residual_humi: float
    mahalanobis_distance: float
    is_suspicious: bool
    confidence_bound_3sigma: Dict[str, float]
    latency_ms: float = 0.0


@dataclass
class Stage2IsoForestOutput:
    """Result from Tier 3 Stage 2 Augmented Isolation Forest."""
    executed: bool
    anomaly_score: float
    is_anomaly: bool
    latency_ms: float = 0.0


@dataclass
class SpatialConsensusOutput:
    """Spatial verification using nearest neighboring AWS stations."""
    neighbor_count: int
    neighbor_ids: List[str]
    distances_km: List[float]
    median_temp: Optional[float]
    median_pres: Optional[float]
    median_humi: Optional[float]
    target_deviation_temp: float
    spatial_consensus_score: float  # 0.0 (anomalous deviation) to 1.0 (perfect consensus)
    is_spatially_inconsistent: bool


@dataclass
class Stage3ArbiterOutput:
    """Decision from the hierarchical XGBoost classifier."""
    is_weather_event: bool
    anomaly_category: AnomalyCategory
    root_cause_label: str
    confidence: float  # 0.0 to 1.0
    shap_attributions: Dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass
class SensorHealthMetric:
    """Rolling sensor health and predictive maintenance status."""
    health_score_pct: float  # 0 to 100%
    rolling_anomaly_rate: float
    consecutive_failures: int
    missing_data_ratio: float
    drift_indicator: float
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    recommended_action: str
    predicted_maintenance_days: Optional[int] = None


@dataclass
class CorrectedTelemetry:
    """Safe, auditable imputed readings (never overwrites raw telemetry)."""
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None
    applied: bool = False
    method: str = "NONE"  # "NONE", "KALMAN_FORECAST", "SPATIAL_MEDIAN"
    confidence: float = 0.0


@dataclass
class DiagnosticResult:
    """Master response object for an AWS reading processed by SkyGuard AI."""
    timestamp: str
    station_id: str
    station_name: str
    raw_reading: Dict[str, Any]
    engineered_features: Dict[str, float]
    tier1: Tier1Output
    tier2: Optional[Tier2Output]
    stage1_forecast: Optional[Stage1ForecastOutput]
    stage2_isoforest: Optional[Stage2IsoForestOutput]
    spatial_consensus: Optional[SpatialConsensusOutput]
    stage3_arbiter: Optional[Stage3ArbiterOutput]
    final_status: QCStatus
    final_anomaly: bool
    anomaly_category: AnomalyCategory
    root_cause: str
    severity: Severity
    confidence: float
    plain_english_rca: str
    sensor_health: SensorHealthMetric
    corrected_telemetry: CorrectedTelemetry
    total_latency_ms: float
    wmo_qc_flag: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "station_id": self.station_id,
            "station_name": self.station_name,
            "raw_reading": self.raw_reading,
            "engineered_features": self.engineered_features,
            "wmo_qc_flag": self.wmo_qc_flag,
            "tier1": {
                "status": self.tier1.status.value,
                "rules_fired": self.tier1.rules_fired,
                "latency_ms": self.tier1.latency_ms,
            },
            "tier2": {
                "score": self.tier2.anomaly_score if self.tier2 else 0.0,
                "is_anomaly": self.tier2.is_anomaly if self.tier2 else False,
            } if self.tier2 else None,
            "stage1_forecast": {
                "predicted": {
                    "temp": self.stage1_forecast.predicted_temp,
                    "pres": self.stage1_forecast.predicted_pres,
                    "humi": self.stage1_forecast.predicted_humi,
                },
                "residuals": {
                    "temp": self.stage1_forecast.residual_temp,
                    "pres": self.stage1_forecast.residual_pres,
                    "humi": self.stage1_forecast.residual_humi,
                },
                "mahalanobis_distance": self.stage1_forecast.mahalanobis_distance,
                "is_suspicious": self.stage1_forecast.is_suspicious,
            } if self.stage1_forecast else None,
            "spatial_consensus": {
                "neighbor_count": self.spatial_consensus.neighbor_count,
                "neighbor_ids": self.spatial_consensus.neighbor_ids,
                "distances_km": self.spatial_consensus.distances_km,
                "consensus_score": self.spatial_consensus.spatial_consensus_score,
                "inconsistent": self.spatial_consensus.is_spatially_inconsistent,
            } if self.spatial_consensus else None,
            "stage3_arbiter": {
                "is_weather_event": self.stage3_arbiter.is_weather_event,
                "root_cause": self.stage3_arbiter.root_cause_label,
                "confidence": self.stage3_arbiter.confidence,
                "shap_top": sorted(
                    self.stage3_arbiter.shap_attributions.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )[:5] if self.stage3_arbiter else [],
            } if self.stage3_arbiter else None,
            "final_status": self.final_status.value,
            "final_anomaly": self.final_anomaly,
            "anomaly_category": self.anomaly_category.value,
            "root_cause": self.root_cause,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "plain_english_rca": self.plain_english_rca,
            "sensor_health": {
                "score_pct": self.sensor_health.health_score_pct,
                "status": self.sensor_health.status,
                "action": self.sensor_health.recommended_action,
            },
            "corrected_telemetry": {
                "applied": self.corrected_telemetry.applied,
                "temp": self.corrected_telemetry.temperature,
                "pres": self.corrected_telemetry.pressure,
                "humi": self.corrected_telemetry.humidity,
                "method": self.corrected_telemetry.method,
            },
            "total_latency_ms": self.total_latency_ms,
        }
