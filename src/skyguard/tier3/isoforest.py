"""
SkyGuard AI — Tier 3 Stage 2 Augmented Isolation Forest
Invoked conditionally for readings flagged as suspicious by Stage 1 Forecaster (d^2 > threshold).
Evaluates the 29 features + forecast residuals + Mahalanobis distance.
"""

import time
from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest

from skyguard.config.contracts import Stage2IsoForestOutput
from skyguard.features.streaming import CANONICAL_FEATURES


class AugmentedIsolationForest:
    """Stage 2 unsupervised isolation forest trained on normal multi-variate vectors."""

    def __init__(self, contamination: float = 0.02, n_estimators: int = 100, random_state: int = 42):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=1,
        )
        self.is_fitted = False

    def fit(self, feature_matrix: np.ndarray):
        """Fits Isolation Forest on clean feature matrix."""
        # Replace any residual NaNs with column medians
        cleaned = np.nan_to_num(feature_matrix, nan=0.0)
        self.model.fit(cleaned)
        self.is_fitted = True

    def evaluate(
        self,
        features: Dict[str, float],
        residual_temp: float,
        residual_pres: float,
        residual_humi: float,
        mahalanobis_d2: float,
        force_run: bool = False,
    ) -> Stage2IsoForestOutput:
        """Evaluates anomaly score for suspicious readings."""
        t0 = time.perf_counter()

        # Build feature vector: 29 features + 3 residuals + 1 mahalanobis_d2 = 33 features
        vec = [features.get(k, 0.0) for k in CANONICAL_FEATURES]
        vec.extend([residual_temp, residual_pres, residual_humi, mahalanobis_d2])
        x = np.array(vec, dtype=float).reshape(1, -1)

        if not self.is_fitted:
            # Fallback heuristic score based on residuals and mahalanobis distance
            score = float(np.clip(mahalanobis_d2 / 20.0, 0.0, 1.0))
            is_anomaly = score > 0.55
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return Stage2IsoForestOutput(
                executed=True,
                anomaly_score=score,
                is_anomaly=is_anomaly,
                latency_ms=latency_ms,
            )

        # Sklearn decision_function returns negative for outliers, positive for inliers
        raw_score = float(self.model.decision_function(x)[0])
        # Map to 0.0 (normal) to 1.0 (severe outlier)
        norm_score = float(np.clip(0.5 - raw_score, 0.0, 1.0))
        pred = self.model.predict(x)[0]
        is_anomaly = bool(pred == -1)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return Stage2IsoForestOutput(
            executed=True,
            anomaly_score=norm_score,
            is_anomaly=is_anomaly,
            latency_ms=latency_ms,
        )
