"""
SkyGuard AI — Safe Auditable Imputation Layer
Safely estimates corrected values ONLY when:
1. The reading is diagnosed as an instrument / data fault (NOT genuine weather).
2. Diagnostic confidence exceeds threshold (default: 85%).
3. A valid replacement estimate exists (from state-space forecaster or spatial neighbor median).
NEVER overwrites raw telemetry observations.
"""

from typing import Dict, Optional, Tuple
from skyguard.config.contracts import (
    CorrectedTelemetry,
    SpatialConsensusOutput,
    Stage1ForecastOutput,
    Stage3ArbiterOutput,
)


class SafeImputer:
    """Safe, auditable value corrector preserving raw atmospheric integrity."""

    def __init__(self, min_confidence: float = 0.85):
        self.min_confidence = min_confidence

    def impute(
        self,
        raw_temp: Optional[float],
        raw_pres: Optional[float],
        raw_humi: Optional[float],
        arbiter: Optional[Stage3ArbiterOutput],
        stage1_forecast: Optional[Stage1ForecastOutput],
        spatial_consensus: Optional[SpatialConsensusOutput],
    ) -> CorrectedTelemetry:
        """Determines if a reading requires correction and computes an auditable imputed replacement."""
        # 1. Check if reading is an instrument fault (not genuine extreme weather)
        if not arbiter or arbiter.is_weather_event or arbiter.confidence < self.min_confidence:
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
        method = "NONE"

        # Prioritize spatial neighbor median if multiple agreeing neighbors exist
        if spatial_consensus and spatial_consensus.neighbor_count >= 2 and spatial_consensus.median_temp is not None:
            corr_t = spatial_consensus.median_temp
            corr_p = spatial_consensus.median_pres if spatial_consensus.median_pres is not None else raw_pres
            corr_h = spatial_consensus.median_humi if spatial_consensus.median_humi is not None else raw_humi
            method = "SPATIAL_NEIGHBOR_MEDIAN"
        # Otherwise use state-space Kalman prediction
        elif stage1_forecast is not None:
            corr_t = stage1_forecast.predicted_temp
            corr_p = stage1_forecast.predicted_pres
            corr_h = stage1_forecast.predicted_humi
            method = "KALMAN_STATE_SPACE_FORECAST"

        return CorrectedTelemetry(
            temperature=round(float(corr_t), 2) if corr_t is not None else None,
            pressure=round(float(corr_p), 2) if corr_p is not None else None,
            humidity=round(float(corr_h), 2) if corr_h is not None else None,
            applied=True,
            method=method,
            confidence=float(arbiter.confidence),
        )
