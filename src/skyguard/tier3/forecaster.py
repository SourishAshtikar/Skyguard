"""
SkyGuard AI — Tier 3 Stage 1 State-Space Forecaster
Jointly models [Temperature, Pressure, Humidity] using a recursive Kalman filter
with diurnal cyclical exogenous regressors (hour_sin/cos, doy_sin/cos).
Evaluates innovation Mahalanobis distance:
    d^2 = (y_t - y_hat)^T Sigma^{-1} (y_t - y_hat) ~ Chi^2_3
Provides dynamic +/- 3-sigma confidence bounds and handles communication dropouts natively.
"""

import time
from typing import Dict, Optional, Tuple, Union
import numpy as np

from skyguard.config.contracts import Stage1ForecastOutput


class StateSpaceForecaster:
    """Multivariate 3-state Kalman Filter for [T, P, H] with diurnal cyclical forcing."""

    def __init__(self, chi2_p99_threshold: float = 11.345):
        self.chi2_p99_threshold = chi2_p99_threshold
        # State vector x = [T, P, H]^T
        self.x = np.array([25.0, 1013.25, 60.0], dtype=float)
        # State covariance P
        self.P = np.diag([4.0, 2.0, 10.0]).astype(float)
        # Process noise covariance Q
        self.Q = np.diag([0.25, 0.1, 1.0]).astype(float)
        # Measurement noise covariance R
        self.R = np.diag([0.15, 0.05, 0.5]).astype(float)
        # Transition matrix A (diurnal drift persistence)
        self.A = np.eye(3)
        self.initialized = False

    def reset(self, initial_t: float = 25.0, initial_p: float = 1013.25, initial_h: float = 60.0):
        """Resets the state vector and covariance matrix."""
        self.x = np.array([initial_t, initial_p, initial_h], dtype=float)
        self.P = np.diag([4.0, 2.0, 10.0]).astype(float)
        self.initialized = True

    def update(
        self,
        temp: Optional[float],
        pres: Optional[float],
        humi: Optional[float],
        features: Optional[Dict[str, float]] = None,
    ) -> Stage1ForecastOutput:
        """Runs 1-step recursive Kalman filter update and returns innovation diagnostics."""
        t0 = time.perf_counter()

        if not self.initialized:
            init_t = temp if temp is not None and not np.isnan(temp) else 25.0
            init_p = pres if pres is not None and not np.isnan(pres) else 1013.25
            init_h = humi if humi is not None and not np.isnan(humi) else 60.0
            self.reset(init_t, init_p, init_h)

        # 1. State Prediction (A * x + B * u)
        # Exogenous cyclical adjustment
        h_sin = features.get("hour_sin", 0.0) if features else 0.0
        h_cos = features.get("hour_cos", 1.0) if features else 1.0
        diurnal_t_delta = 0.8 * h_sin - 0.3 * h_cos  # Warmer in afternoon, cooler at dawn
        diurnal_h_delta = -1.2 * h_sin + 0.5 * h_cos  # Inverse of temperature

        x_pred = self.A @ self.x + np.array([diurnal_t_delta, 0.0, diurnal_h_delta])
        P_pred = self.A @ self.P @ self.A.T + self.Q

        # Innovation covariance S = P_pred + R
        S = P_pred + self.R
        S_inv = np.linalg.inv(S)

        # Dynamic 3-sigma confidence bounds
        sigma_3 = {
            "temp": float(3.0 * np.sqrt(max(1e-4, S[0, 0]))),
            "pres": float(3.0 * np.sqrt(max(1e-4, S[1, 1]))),
            "humi": float(3.0 * np.sqrt(max(1e-4, S[2, 2]))),
        }

        # Measurement reading vector
        is_missing = (
            temp is None or pres is None or humi is None or
            np.isnan(temp) or np.isnan(pres) or np.isnan(humi)
        )

        if is_missing:
            # Dropout handling: state covariance propagation without update
            self.x = x_pred
            self.P = P_pred
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return Stage1ForecastOutput(
                predicted_temp=float(x_pred[0]),
                predicted_pres=float(x_pred[1]),
                predicted_humi=float(x_pred[2]),
                residual_temp=0.0,
                residual_pres=0.0,
                residual_humi=0.0,
                mahalanobis_distance=0.0,
                is_suspicious=False,
                confidence_bound_3sigma=sigma_3,
                latency_ms=latency_ms,
            )

        y = np.array([temp, pres, humi], dtype=float)
        # Innovation residual y - x_pred
        residual = y - x_pred

        # Innovation Mahalanobis distance: d^2 = res^T * S^-1 * res
        mahal_d2 = float(residual.T @ S_inv @ residual)
        is_suspicious = bool(mahal_d2 > self.chi2_p99_threshold)

        # Kalman gain K = P_pred * S^-1
        K = P_pred @ S_inv

        # Update state and covariance (dampen update if suspicious to avoid contamination)
        effective_gain = K if not is_suspicious else 0.1 * K
        self.x = x_pred + effective_gain @ residual
        self.P = (np.eye(3) - effective_gain) @ P_pred

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return Stage1ForecastOutput(
            predicted_temp=float(x_pred[0]),
            predicted_pres=float(x_pred[1]),
            predicted_humi=float(x_pred[2]),
            residual_temp=float(residual[0]),
            residual_pres=float(residual[1]),
            residual_humi=float(residual[2]),
            mahalanobis_distance=float(mahal_d2),
            is_suspicious=is_suspicious,
            confidence_bound_3sigma=sigma_3,
            latency_ms=latency_ms,
        )
