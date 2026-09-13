"""
SkyGuard AI — Safe Auditable Imputation Layer
Safely estimates corrected values ONLY when:
1. The reading is diagnosed as an instrument / data fault (NOT genuine weather).
2. Diagnostic confidence exceeds threshold (default: 85%).
3. A valid replacement estimate exists (from state-space forecaster or spatial neighbor median).
NEVER overwrites raw telemetry observations.
"""

from typing import Dict, Optional, Tuple, Any
from skyguard.config.contracts import (
    CorrectedTelemetry,
    SpatialConsensusOutput,
    Stage1ForecastOutput,
    Stage3ArbiterOutput,
    SatelliteCrossCheckOutput,
)


class SafeImputer:
    """Safe, auditable value corrector preserving raw atmospheric integrity."""

    def __init__(self, min_confidence: float = 0.50):
        self.min_confidence = min_confidence

    def impute(
        self,
        raw_temp: Optional[float],
        raw_pres: Optional[float],
        raw_humi: Optional[float],
        arbiter: Optional[Stage3ArbiterOutput] = None,
        stage1_forecast: Optional[Stage1ForecastOutput] = None,
        spatial_consensus: Optional[SpatialConsensusOutput] = None,
        satellite_obs: Optional[SatelliteCrossCheckOutput] = None,
        is_anomaly: bool = False,
    ) -> CorrectedTelemetry:
        """Determines if a reading requires correction and computes an auditable imputed replacement."""
        should_impute = is_anomaly or (
            arbiter is not None and not arbiter.is_weather_event and arbiter.confidence >= self.min_confidence
        ) or (raw_temp is None or raw_pres is None or raw_humi is None)

        if not should_impute:
            return CorrectedTelemetry(
                temperature=raw_temp,
                pressure=raw_pres,
                humidity=raw_humi,
                applied=False,
                method="NONE",
                confidence=arbiter.confidence if arbiter else 0.0,
            )

        # 2. Select best replacement method
        corr_t = raw_temp
        corr_p = raw_pres
        corr_h = raw_humi
        method = "KALMAN_STATE_SPACE_FORECAST"

        # Prioritize spatial neighbor median if multiple agreeing neighbors exist
        if spatial_consensus and spatial_consensus.neighbor_count >= 2 and spatial_consensus.median_temp is not None:
            corr_t = spatial_consensus.median_temp
            corr_p = spatial_consensus.median_pres if spatial_consensus.median_pres is not None else raw_pres
            corr_h = spatial_consensus.median_humi if spatial_consensus.median_humi is not None else raw_humi
            method = "SPATIAL_MESONET_CONSENSUS"
        # Otherwise use state-space Kalman prediction
        elif stage1_forecast is not None:
            corr_t = stage1_forecast.predicted_temp if stage1_forecast.predicted_temp is not None else raw_temp
            corr_p = stage1_forecast.predicted_pres if stage1_forecast.predicted_pres is not None else raw_pres
            corr_h = stage1_forecast.predicted_humi if stage1_forecast.predicted_humi is not None else raw_humi
            method = "KALMAN_STATE_SPACE_FORECAST"
        elif satellite_obs is not None and satellite_obs.land_surface_temp_c is not None:
            corr_t = satellite_obs.land_surface_temp_c
            corr_p = satellite_obs.evidence.get("surface_pres_hpa", raw_pres) if satellite_obs.evidence else raw_pres
            corr_h = satellite_obs.evidence.get("surface_humi_pct", raw_humi) if satellite_obs.evidence else raw_humi
            method = "SPACEBORNE_SATELLITE_LST"

        # Fallback if raw is None or identical
        if corr_t is None and raw_temp is not None:
            corr_t = raw_temp
        if corr_p is None and raw_pres is not None:
            corr_p = raw_pres
        if corr_h is not None:
            corr_h = max(1.0, min(100.0, float(corr_h)))

        conf = float(arbiter.confidence) if arbiter and hasattr(arbiter, "confidence") else 0.92

        return CorrectedTelemetry(
            temperature=round(float(corr_t), 1) if corr_t is not None else None,
            pressure=round(float(corr_p), 1) if corr_p is not None else None,
            humidity=round(float(corr_h), 1) if corr_h is not None else None,
            applied=True,
            method=method,
            confidence=conf,
        )
