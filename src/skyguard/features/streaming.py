"""
SkyGuard AI — Streaming Feature Extractor
Stateful ring-buffer feature extractor for low-latency (< 0.5 ms) edge & gateway inference.
Extracts all 29 canonical engineered features without data leakage.
"""

from collections import deque
from datetime import datetime
import math
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd

from .thermodynamics import (
    compute_dew_point,
    compute_vapor_pressure,
    compute_heat_index,
)

CANONICAL_FEATURES: List[str] = [
    # A. Raw sensor (3)
    "temp", "pres", "humi",
    # B. Derived thermodynamic (4)
    "dew_point", "dp_depress", "vap_pres", "heat_idx",
    # C. Temporal / rate-of-change (12)
    "temp_delta_1", "pres_delta_1", "humi_delta_1",
    "temp_roc_3h", "pres_roc_3h", "humi_roc_3h",
    "temp_rmean_6h", "temp_rstd_6h",
    "pres_rmean_6h", "pres_rstd_6h",
    "humi_rmean_6h", "humi_rstd_6h",
    # D. Persistence / frozen sensor (3)
    "temp_persist_len", "pres_persist_len", "humi_persist_len",
    # E. Cyclical temporal context (4)
    "hour_sin", "hour_cos", "doy_sin", "doy_cos",
    # F. Z-score normalized (3)
    "temp_z", "pres_z", "humi_z",
]


class StreamingFeatureExtractor:
    """Stateful ring-buffer extractor maintaining historical context up to 48 readings."""

    def __init__(self, buffer_size: int = 48):
        self.buffer_size = buffer_size
        self.history: deque = deque(maxlen=buffer_size)
        self.prev_reading: Optional[Dict[str, float]] = None
        self.persist_counts: Dict[str, int] = {"temp": 0, "pres": 0, "humi": 0}

    def reset(self):
        """Clears buffer and resets persistence state."""
        self.history.clear()
        self.prev_reading = None
        self.persist_counts = {"temp": 0, "pres": 0, "humi": 0}

    def process(
        self,
        timestamp: Union[str, datetime, pd.Timestamp],
        temp: Optional[float],
        pres: Optional[float],
        humi: Optional[float],
    ) -> Dict[str, float]:
        """Ingests one reading (t) and returns dictionary with all 29 features."""
        # Convert timestamp
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp)
            except Exception:
                dt = pd.to_datetime(timestamp)
        elif isinstance(timestamp, (datetime, pd.Timestamp)):
            dt = timestamp
        else:
            dt = pd.to_datetime(timestamp)

        # Fallback values for NaN readings (e.g. communication drops)
        t_val = float(temp) if temp is not None and not np.isnan(temp) else 25.0
        p_val = float(pres) if pres is not None and not np.isnan(pres) else 1013.25
        h_val = float(humi) if humi is not None and not np.isnan(humi) else 50.0

        features: Dict[str, float] = {
            "temp": t_val,
            "pres": p_val,
            "humi": h_val,
        }

        # 2. Derived thermodynamic features
        dp = float(compute_dew_point(t_val, h_val))
        features["dew_point"] = dp
        features["dp_depress"] = t_val - dp
        features["vap_pres"] = float(compute_vapor_pressure(t_val, h_val))
        features["heat_idx"] = float(compute_heat_index(t_val, h_val))

        # 3. Persistence and 1-step deltas
        if self.prev_reading is not None:
            for p, val in [("temp", t_val), ("pres", p_val), ("humi", h_val)]:
                prev_val = self.prev_reading[p]
                if abs(val - prev_val) < 0.05:
                    self.persist_counts[p] += 1
                else:
                    self.persist_counts[p] = 0
            features["temp_delta_1"] = t_val - self.prev_reading["temp"]
            features["pres_delta_1"] = p_val - self.prev_reading["pres"]
            features["humi_delta_1"] = h_val - self.prev_reading["humi"]
        else:
            features["temp_delta_1"] = 0.0
            features["pres_delta_1"] = 0.0
            features["humi_delta_1"] = 0.0

        features["temp_persist_len"] = float(self.persist_counts["temp"])
        features["pres_persist_len"] = float(self.persist_counts["pres"])
        features["humi_persist_len"] = float(self.persist_counts["humi"])

        # 3-hour rates of change
        if len(self.history) >= 3:
            h_3 = self.history[-3]
            features["temp_roc_3h"] = (t_val - h_3["temp"]) / 3.0
            features["pres_roc_3h"] = (p_val - h_3["pres"]) / 3.0
            features["humi_roc_3h"] = (h_val - h_3["humi"]) / 3.0
        else:
            features["temp_roc_3h"] = 0.0
            features["pres_roc_3h"] = 0.0
            features["humi_roc_3h"] = 0.0

        # Push to history ring buffer
        self.history.append({
            "temp": t_val,
            "pres": p_val,
            "humi": h_val,
            "dt": dt,
        })
        self.prev_reading = {"temp": t_val, "pres": p_val, "humi": h_val}

        # 6-hour rolling statistics
        n_6 = min(len(self.history), 6)
        recent_6 = list(self.history)[-n_6:]
        for p in ["temp", "pres", "humi"]:
            vals_6 = [item[p] for item in recent_6]
            m6 = sum(vals_6) / len(vals_6)
            features[f"{p}_rmean_6h"] = float(m6)
            if len(vals_6) > 1:
                var6 = sum((x - m6) ** 2 for x in vals_6) / len(vals_6)
                features[f"{p}_rstd_6h"] = float(math.sqrt(var6))
            else:
                features[f"{p}_rstd_6h"] = 0.0

        # Cyclical temporal context
        hour = dt.hour
        doy = dt.dayofyear if hasattr(dt, "dayofyear") else dt.timetuple().tm_yday
        features["hour_sin"] = float(math.sin(2.0 * math.pi * hour / 24.0))
        features["hour_cos"] = float(math.cos(2.0 * math.pi * hour / 24.0))
        features["doy_sin"] = float(math.sin(2.0 * math.pi * doy / 365.25))
        features["doy_cos"] = float(math.cos(2.0 * math.pi * doy / 365.25))

        # 24-hour rolling z-scores
        n_24 = min(len(self.history), 24)
        recent_24 = list(self.history)[-n_24:]
        eps = 1e-6
        for p in ["temp", "pres", "humi"]:
            vals_24 = [item[p] for item in recent_24]
            mu = sum(vals_24) / len(vals_24)
            if len(vals_24) > 1:
                var24 = sum((x - mu) ** 2 for x in vals_24) / len(vals_24)
                sigma = math.sqrt(var24)
            else:
                sigma = 0.0
            features[f"{p}_z"] = float((features[p] - mu) / (sigma + eps))

        return features
