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
    UNKNOWN = "UNKNOWN"


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
    is_precipitating: Optional[bool] = None
    rain_mm: Optional[float] = None

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
            "is_precipitating": self.is_precipitating,
            "rain_mm": self.rain_mm,
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
    target_deviation_pres: float = 0.0
    target_deviation_humi: float = 0.0
    spatial_consensus_score: float = 1.0  # 0.0 (anomalous deviation) to 1.0 (perfect consensus)
    is_spatially_inconsistent: bool = False
    valid_peer_count: int = 0
    healthy_peer_count: int = 0
    effective_peer_count: float = 0.0
    peer_mad_temp: float = 0.0
    peer_mad_pres: float = 0.0
    peer_mad_humi: float = 0.0
    temp_absolute_residual: float = 0.0
    temp_change_residual: float = 0.0
    spatial_confidence: float = 1.0
    spatial_status: str = "CONSISTENT_WITH_PEERS"
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SatelliteCrossCheckOutput:
    """Spaceborne satellite imagery & thermal infrared cross-check result (e.g. INSAT-3D/3DR)."""
    satellite_id: str
    pixel_latitude: float
    pixel_longitude: float
    land_surface_temp_c: Optional[float] = None
    cloud_top_temp_c: Optional[float] = None
    cloud_fraction_pct: Optional[float] = None
    brightness_temp_k: Optional[float] = None
    temp_consistency_score: float = 1.0  # 0.0 to 1.0
    cloud_consistency_score: float = 1.0  # 0.0 to 1.0
    satellite_consensus_score: float = 1.0  # Combined score
    is_satellite_inconsistent: bool = False
    is_convective_storm_confirmed: bool = False
    satellite_note: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


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
    satellite_cross_check: Optional[SatelliteCrossCheckOutput]
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
                "spatial_consensus_score": self.spatial_consensus.spatial_consensus_score,
                "inconsistent": self.spatial_consensus.is_spatially_inconsistent,
                "is_spatially_inconsistent": self.spatial_consensus.is_spatially_inconsistent,
                "target_deviation_temp": self.spatial_consensus.target_deviation_temp,
                "target_deviation_pres": self.spatial_consensus.target_deviation_pres,
                "target_deviation_humi": self.spatial_consensus.target_deviation_humi,
                "median_temp": self.spatial_consensus.median_temp,
                "median_pres": self.spatial_consensus.median_pres,
                "median_humi": self.spatial_consensus.median_humi,
                "valid_peer_count": getattr(self.spatial_consensus, "valid_peer_count", self.spatial_consensus.neighbor_count),
                "healthy_peer_count": getattr(self.spatial_consensus, "healthy_peer_count", self.spatial_consensus.neighbor_count),
                "effective_peer_count": getattr(self.spatial_consensus, "effective_peer_count", float(self.spatial_consensus.neighbor_count)),
                "peer_mad_temp": getattr(self.spatial_consensus, "peer_mad_temp", 0.0),
                "peer_mad_pres": getattr(self.spatial_consensus, "peer_mad_pres", 0.0),
                "peer_mad_humi": getattr(self.spatial_consensus, "peer_mad_humi", 0.0),
                "temp_absolute_residual": getattr(self.spatial_consensus, "temp_absolute_residual", self.spatial_consensus.target_deviation_temp),
                "temp_change_residual": getattr(self.spatial_consensus, "temp_change_residual", 0.0),
                "spatial_confidence": getattr(self.spatial_consensus, "spatial_confidence", 1.0),
                "spatial_status": getattr(self.spatial_consensus, "spatial_status", "CONSISTENT_WITH_PEERS"),
                "evidence": getattr(self.spatial_consensus, "evidence", {}),
            } if self.spatial_consensus else None,
            "satellite_cross_check": {
                "satellite_id": self.satellite_cross_check.satellite_id,
                "land_surface_temp_c": self.satellite_cross_check.land_surface_temp_c,
                "cloud_top_temp_c": self.satellite_cross_check.cloud_top_temp_c,
                "cloud_fraction_pct": self.satellite_cross_check.cloud_fraction_pct,
                "brightness_temp_k": self.satellite_cross_check.brightness_temp_k,
                "temp_consistency_score": self.satellite_cross_check.temp_consistency_score,
                "cloud_consistency_score": self.satellite_cross_check.cloud_consistency_score,
                "consensus_score": self.satellite_cross_check.satellite_consensus_score,
                "satellite_consensus_score": self.satellite_cross_check.satellite_consensus_score,
                "inconsistent": self.satellite_cross_check.is_satellite_inconsistent,
                "is_satellite_inconsistent": self.satellite_cross_check.is_satellite_inconsistent,
                "convective_storm_confirmed": self.satellite_cross_check.is_convective_storm_confirmed,
                "is_convective_storm_confirmed": self.satellite_cross_check.is_convective_storm_confirmed,
                "note": self.satellite_cross_check.satellite_note,
                "satellite_note": self.satellite_cross_check.satellite_note,
                "evidence": self.satellite_cross_check.evidence,
                "latency_ms": self.satellite_cross_check.latency_ms,
            } if self.satellite_cross_check else None,
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
                "health_score_pct": self.sensor_health.health_score_pct,
                "status": self.sensor_health.status,
                "action": self.sensor_health.recommended_action,
                "recommended_action": self.sensor_health.recommended_action,
                "rolling_anomaly_rate": self.sensor_health.rolling_anomaly_rate,
                "consecutive_failures": self.sensor_health.consecutive_failures,
                "drift_indicator": self.sensor_health.drift_indicator,
                "missing_data_ratio": self.sensor_health.missing_data_ratio,
                "predicted_maintenance_days": self.sensor_health.predicted_maintenance_days,
            },
            "corrected_telemetry": {
                "applied": self.corrected_telemetry.applied,
                "temp": self.corrected_telemetry.temperature,
                "temperature": self.corrected_telemetry.temperature,
                "pres": self.corrected_telemetry.pressure,
                "pressure": self.corrected_telemetry.pressure,
                "humi": self.corrected_telemetry.humidity,
                "humidity": self.corrected_telemetry.humidity,
                "method": self.corrected_telemetry.method,
            },
            "total_latency_ms": self.total_latency_ms,
        }
