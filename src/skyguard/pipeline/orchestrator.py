"""
SkyGuard AI — Master Orchestration Pipeline
Unifies Tier 1 (Edge Rules), Tier 2 (Autoencoder), Tier 3 (Kalman Forecaster,
Augmented Isolation Forest, Hierarchical XGBoost Arbiter), Spatial Consensus,
TreeSHAP Explainability, Sensor Health, and Safe Imputation into a single high-speed pipeline.
"""

from pathlib import Path
import time
from typing import Dict, List, Optional, Union

from skyguard.config.contracts import (
    AnomalyCategory,
    DiagnosticResult,
    QCStatus,
    SensorReading,
    Severity,
)
from skyguard.correction import SafeImputer
from skyguard.explainability import IncidentExplainer
from skyguard.features import StreamingFeatureExtractor
from skyguard.health import SensorHealthTracker
from skyguard.spatial import SpatialNeighborResolver
from skyguard.tier1 import Tier1Engine
from skyguard.tier2 import Tier2InferenceEngine
from skyguard.tier3 import (
    AugmentedIsolationForest,
    HierarchicalArbiter,
    StateSpaceForecaster,
)


class SkyGuardPipeline:
    """Master pipeline orchestrating all three intelligence tiers for an AWS station."""

    def __init__(
        self,
        station_id: str,
        station_name: str = "Unknown Station",
        metadata_csv_path: Optional[Union[str, Path]] = None,
    ):
        self.station_id = station_id
        self.station_name = station_name

        # 1. Feature Extractor
        self.feature_extractor = StreamingFeatureExtractor(buffer_size=48)
        # 2. Tier 1 Edge QC Engine
        self.tier1_engine = Tier1Engine()
        # 3. Tier 2 Edge Autoencoder
        self.tier2_engine = Tier2InferenceEngine()
        # 4. Tier 3 Stage 1 Forecaster
        self.forecaster = StateSpaceForecaster()
        # 5. Tier 3 Stage 2 Isolation Forest
        self.isoforest = AugmentedIsolationForest()
        # 6. Spatial Resolver
        meta_p = metadata_csv_path or Path("Datasets/indian_aws_locations.csv")
        self.spatial_resolver = SpatialNeighborResolver(
            metadata_csv_path=meta_p if Path(meta_p).exists() else None
        )
        # 7. Tier 3 Stage 3 Arbiter
        self.arbiter = HierarchicalArbiter()
        # 8. Explainer
        self.explainer = IncidentExplainer()
        # 9. Health Tracker
        self.health_tracker = SensorHealthTracker(station_id=station_id)
        # 10. Safe Imputer
        self.imputer = SafeImputer(min_confidence=0.80)

    def process(
        self,
        reading: SensorReading,
        neighbor_telemetry: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> DiagnosticResult:
        """Processes a single telemetry reading through all three tiers."""
        t_start = time.perf_counter()

        ts_str = reading.timestamp.isoformat() if hasattr(reading.timestamp, "isoformat") else str(reading.timestamp)
        t = reading.temperature
        p = reading.pressure
        h = reading.humidity

        # Step 1 & 2: Streaming feature extraction
        feats = self.feature_extractor.process(ts_str, t, p, h)

        # Step 3: Tier 1 Edge QC Rules
        t1_out = self.tier1_engine.evaluate(t, p, h, feats)

        # Step 4: Tier 2 Edge Autoencoder Inference
        t2_out = self.tier2_engine.evaluate(feats)

        # Step 5: Tier 3 Stage 1 State-Space Forecaster
        s1_out = self.forecaster.update(t, p, h, feats)

        # Step 6: Tier 3 Stage 2 Isolation Forest (conditional on suspicious forecast)
        if s1_out.is_suspicious or t1_out.status != QCStatus.PASS:
            s2_out = self.isoforest.evaluate(
                features=feats,
                residual_temp=s1_out.residual_temp,
                residual_pres=s1_out.residual_pres,
                residual_humi=s1_out.residual_humi,
                mahalanobis_d2=s1_out.mahalanobis_distance,
            )
        else:
            s2_out = None

        # Step 7: Spatial Consensus Verification
        spatial_out = self.spatial_resolver.evaluate_consensus(
            target_station_id=self.station_id,
            target_temp=t,
            target_pres=p,
            target_humi=h,
            neighbor_telemetry=neighbor_telemetry,
        )

        # Step 8: Tier 3 Stage 3 Hierarchical Arbiter
        arbiter_out = self.arbiter.evaluate(
            features=feats,
            spatial_consensus=spatial_out,
            mahalanobis_d2=s1_out.mahalanobis_distance,
            tier1_fired_rules=t1_out.rules_fired,
            tier2_score=t2_out.anomaly_score,
        )

        # Step 9: Final status, severity, and confidence aggregation
        is_anomaly = bool(
            t1_out.status == QCStatus.FAIL or
            (t2_out.is_anomaly and not arbiter_out.is_weather_event) or
            (s1_out.is_suspicious and s2_out is not None and s2_out.is_anomaly and not arbiter_out.is_weather_event) or
            spatial_out.is_spatially_inconsistent
        )

        if arbiter_out.is_weather_event:
            final_status = QCStatus.PASS
            severity = Severity.HIGH  # Severe weather alert
        elif is_anomaly:
            final_status = QCStatus.FAIL
            severity = Severity.CRITICAL if ("DEW_POINT_INVARIANT" in t1_out.rules_fired or "RANGE_CHECK" in t1_out.rules_fired) else Severity.HIGH
        elif t1_out.status == QCStatus.SUSPECT:
            final_status = QCStatus.SUSPECT
            severity = Severity.MEDIUM
        else:
            final_status = QCStatus.PASS
            severity = Severity.NORMAL

        confidence = arbiter_out.confidence if arbiter_out else (0.95 if not is_anomaly else 0.85)

        # Step 10: Explainability & Plain-English RCA
        rca_narrative = self.explainer.generate_narrative(
            station_name=self.station_name,
            station_id=self.station_id,
            timestamp=ts_str,
            raw_values={"temperature": t, "pressure": p, "humidity": h},
            tier1=t1_out,
            tier2=t2_out,
            stage1=s1_out,
            spatial=spatial_out,
            arbiter=arbiter_out,
            final_anomaly=is_anomaly,
        )

        # Step 11: Sensor Health Tracker Update
        is_missing = t is None or p is None or h is None
        health_metric = self.health_tracker.update(
            timestamp=ts_str,
            is_anomaly=is_anomaly,
            is_missing=is_missing,
            drift_delta=s1_out.residual_temp if is_anomaly else 0.0,
        )

        # Step 12: Safe Auditable Correction
        corrected = self.imputer.impute(
            raw_temp=t,
            raw_pres=p,
            raw_humi=h,
            arbiter=arbiter_out if is_anomaly else None,
            stage1_forecast=s1_out,
            spatial_consensus=spatial_out,
        )

        total_latency_ms = (time.perf_counter() - t_start) * 1000.0

        # WMO/IMD Standard QC Flag (Biju et al., 2012):
        # 0: Good, 1: Suspect / Extreme Weather, 2: Erroneous / Malfunction, 3: Missing, 4: Imputed
        if corrected.applied:
            qc_flag = 4
        elif is_missing:
            qc_flag = 3
        elif is_anomaly:
            qc_flag = 2
        elif final_status == QCStatus.SUSPECT or (arbiter_out and arbiter_out.is_weather_event):
            qc_flag = 1
        else:
            qc_flag = 0

        return DiagnosticResult(
            timestamp=ts_str,
            station_id=self.station_id,
            station_name=self.station_name,
            raw_reading=reading.to_dict(),
            engineered_features=feats,
            tier1=t1_out,
            tier2=t2_out,
            stage1_forecast=s1_out,
            stage2_isoforest=s2_out,
            spatial_consensus=spatial_out,
            stage3_arbiter=arbiter_out,
            final_status=final_status,
            final_anomaly=is_anomaly,
            anomaly_category=arbiter_out.anomaly_category if arbiter_out else AnomalyCategory.NONE,
            root_cause=arbiter_out.root_cause_label if arbiter_out else "Nominal",
            severity=severity,
            confidence=confidence,
            plain_english_rca=rca_narrative,
            sensor_health=health_metric,
            corrected_telemetry=corrected,
            total_latency_ms=round(total_latency_ms, 2),
            wmo_qc_flag=qc_flag,
        )
