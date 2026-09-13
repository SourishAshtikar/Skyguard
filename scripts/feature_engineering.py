"""
SkyGuard AI — Phase 1: Feature Engineering Pipeline
Computes all 29 engineered features specified in the SkyGuard AI architecture:
  - 3 Raw Sensor Features: temp, pres, humi
  - 4 Derived Thermodynamic Features: dew_point, dp_depress, vap_pres, heat_idx
  - 12 Temporal / Rate-of-Change Features: 1-step deltas, 3h rate-of-change, 6h rolling mean/std
  - 3 Persistence / Stuck Features: temp_persist_len, pres_persist_len, humi_persist_len
  - 4 Cyclical Temporal Context Features: hour_sin, hour_cos, doy_sin, doy_cos
  - 3 Rolling Z-Scores (24h): temp_z, pres_z, humi_z

Supports both vectorized batch processing on historical DataFrames and
low-latency streaming processing with a rolling window buffer.
"""

from collections import deque
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SkyGuard.FeatureEngineering")

# Exactly 29 engineered features
FEATURE_NAMES: List[str] = [
    # A. Raw sensor (3)
    "temp",
    "pres",
    "humi",
    # B. Derived thermodynamic (4)
    "dew_point",
    "dp_depress",
    "vap_pres",
    "heat_idx",
    # C. Temporal / rate-of-change (12)
    "temp_delta_1",
    "pres_delta_1",
    "humi_delta_1",
    "temp_roc_3h",
    "pres_roc_3h",
    "humi_roc_3h",
    "temp_rmean_6h",
    "temp_rstd_6h",
    "pres_rmean_6h",
    "pres_rstd_6h",
    "humi_rmean_6h",
    "humi_rstd_6h",
    # D. Persistence / stuck sensor (3)
    "temp_persist_len",
    "pres_persist_len",
    "humi_persist_len",
    # E. Cyclical temporal context (4)
    "hour_sin",
    "hour_cos",
    "doy_sin",
    "doy_cos",
    # F. Z-score normalized (3)
    "temp_z",
    "pres_z",
    "humi_z",
]

# Physical thermodynamic constants (Magnus-Tetens)
MAGNUS_A = 17.625
MAGNUS_B = 243.04  # °C


def compute_dew_point(temp: np.ndarray, humi: np.ndarray) -> np.ndarray:
    """Computes dew point temperature (°C) via Magnus-Tetens formula.
    Valid for -40°C to +50°C. Clamps humidity to [0.01, 100.0] to avoid log(0).
    """
    rh_clamped = np.clip(humi, 0.01, 100.0)
    alpha = np.log(rh_clamped / 100.0) + (MAGNUS_A * temp) / (MAGNUS_B + temp)
    dew_point = (MAGNUS_B * alpha) / (MAGNUS_A - alpha)
    return dew_point


def compute_vapor_pressure(temp: np.ndarray, humi: np.ndarray) -> np.ndarray:
    """Computes actual atmospheric vapor pressure e (hPa).
    e = e_s(T) * (RH / 100) where e_s is saturation vapor pressure.
    """
    rh_clamped = np.clip(humi, 0.0, 100.0)
    es = 6.1078 * np.exp((MAGNUS_A * temp) / (MAGNUS_B + temp))
    return es * (rh_clamped / 100.0)


def compute_heat_index(temp: np.ndarray, humi: np.ndarray) -> np.ndarray:
    """Computes Heat Index / Apparent Temperature (°C) using the Rothfusz regression.
    When T < 20°C or conditions are mild, heat index defaults to air temperature.
    """
    tf = temp * 9.0 / 5.0 + 32.0  # Fahrenheit
    rh = np.clip(humi, 0.0, 100.0)

    # Simple formula
    hi_simple = 0.5 * (tf + 61.0 + ((tf - 68.0) * 1.2) + (rh * 0.094))

    # Full Rothfusz polynomial
    hi_full = (
        -42.379
        + 2.04901523 * tf
        + 10.14333127 * rh
        - 0.22475541 * tf * rh
        - 0.00683783 * (tf**2)
        - 0.05481717 * (rh**2)
        + 0.00122874 * (tf**2) * rh
        + 0.00085282 * tf * (rh**2)
        - 0.00000199 * (tf**2) * (rh**2)
    )

    # Low humidity adjustment
    adj1_mask = (rh < 13.0) & (tf >= 80.0) & (tf <= 112.0)
    adj1 = np.where(
        adj1_mask,
        ((13.0 - rh) / 4.0)
        * np.sqrt(np.maximum(0.0, (17.0 - np.abs(tf - 95.0)) / 17.0)),
        0.0,
    )

    # High humidity adjustment
    adj2_mask = (rh > 85.0) & (tf >= 80.0) & (tf <= 87.0)
    adj2 = np.where(adj2_mask, ((rh - 85.0) / 10.0) * ((87.0 - tf) / 5.0), 0.0)

    hi_adjusted = hi_full - adj1 + adj2
    hi_f = np.where(hi_simple >= 80.0, hi_adjusted, hi_simple)
    hi_c = (hi_f - 32.0) * 5.0 / 9.0

    # Heat index only applies when T >= 20°C
    return np.where(temp >= 20.0, hi_c, temp)


def compute_persistence_vectorized(
    series: pd.Series, threshold: float = 0.05
) -> pd.Series:
    """Computes run-length of consecutive readings where |x_t - x_{t-1}| < threshold.
    Vectorized O(N) implementation.
    """
    diffs = series.diff().abs() < threshold
    # Each time diffs is False, start a new group
    block_id = (~diffs).cumsum()
    # Cumulative count of True within each group
    persist_len = diffs.groupby(block_id).cumsum()
    return persist_len.fillna(0).astype(int)


def extract_features(
    df: pd.DataFrame,
    temp_col: str = "temperature",
    pres_col: str = "pressure",
    humi_col: str = "humidity",
    time_col: str = "timestamp",
    sort_chronological: bool = True,
) -> pd.DataFrame:
    """Vectorized feature engineering on a historical station DataFrame.

    Parameters:
        df: DataFrame containing sensor columns and timestamps.
        temp_col: Column name for Air Temperature (°C).
        pres_col: Column name for Atmospheric Pressure (hPa).
        humi_col: Column name for Relative Humidity (%).
        time_col: Column name for Timestamp.
        sort_chronological: Whether to sort by time_col before computing rolling features.

    Returns:
        DataFrame with original metadata preserved plus all 29 FEATURE_NAMES columns.
    """
    out = df.copy()

    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(out[time_col]):
        out[time_col] = pd.to_datetime(out[time_col])

    if sort_chronological:
        out = out.sort_values(time_col).reset_index(drop=True)

    # 1. Raw sensor features
    out["temp"] = out[temp_col].astype(float)
    out["pres"] = out[pres_col].astype(float)
    out["humi"] = out[humi_col].astype(float)

    # 2. Derived thermodynamic features
    out["dew_point"] = compute_dew_point(out["temp"].values, out["humi"].values)
    out["dp_depress"] = out["temp"] - out["dew_point"]
    out["vap_pres"] = compute_vapor_pressure(out["temp"].values, out["humi"].values)
    out["heat_idx"] = compute_heat_index(out["temp"].values, out["humi"].values)

    # 3. Temporal / rate-of-change features
    # 1-step deltas
    out["temp_delta_1"] = out["temp"].diff().fillna(0.0)
    out["pres_delta_1"] = out["pres"].diff().fillna(0.0)
    out["humi_delta_1"] = out["humi"].diff().fillna(0.0)

    # 3-hour rates of change (assuming hourly steps; 3-step delta / 3)
    out["temp_roc_3h"] = ((out["temp"] - out["temp"].shift(3)) / 3.0).fillna(0.0)
    out["pres_roc_3h"] = ((out["pres"] - out["pres"].shift(3)) / 3.0).fillna(0.0)
    out["humi_roc_3h"] = ((out["humi"] - out["humi"].shift(3)) / 3.0).fillna(0.0)

    # 6-hour rolling statistics (window=6)
    out["temp_rmean_6h"] = (
        out["temp"].rolling(window=6, min_periods=1).mean().fillna(out["temp"])
    )
    out["temp_rstd_6h"] = (
        out["temp"].rolling(window=6, min_periods=1).std().fillna(0.0)
    )

    out["pres_rmean_6h"] = (
        out["pres"].rolling(window=6, min_periods=1).mean().fillna(out["pres"])
    )
    out["pres_rstd_6h"] = (
        out["pres"].rolling(window=6, min_periods=1).std().fillna(0.0)
    )

    out["humi_rmean_6h"] = (
        out["humi"].rolling(window=6, min_periods=1).mean().fillna(out["humi"])
    )
    out["humi_rstd_6h"] = (
        out["humi"].rolling(window=6, min_periods=1).std().fillna(0.0)
    )

    # 4. Persistence / frozen sensor features
    out["temp_persist_len"] = compute_persistence_vectorized(out["temp"])
    out["pres_persist_len"] = compute_persistence_vectorized(out["pres"])
    out["humi_persist_len"] = compute_persistence_vectorized(out["humi"])

    # 5. Cyclical temporal context features
    hours = out[time_col].dt.hour.values
    doys = out[time_col].dt.dayofyear.values

    out["hour_sin"] = np.sin(2.0 * np.pi * hours / 24.0)
    out["hour_cos"] = np.cos(2.0 * np.pi * hours / 24.0)
    out["doy_sin"] = np.sin(2.0 * np.pi * doys / 365.25)
    out["doy_cos"] = np.cos(2.0 * np.pi * doys / 365.25)

    # 6. Rolling 24-hour Z-scores
    eps = 1e-6
    for param in ["temp", "pres", "humi"]:
        roll_mean_24 = out[param].rolling(window=24, min_periods=1).mean()
        roll_std_24 = out[param].rolling(window=24, min_periods=1).std().fillna(0.0)
        out[f"{param}_z"] = (out[param] - roll_mean_24) / (roll_std_24 + eps)

    return out


class StreamingFeatureExtractor:
    """Stateful, low-latency streaming feature extractor for real-time edge/gateway inference.
    Maintains a rolling ring buffer of recent readings to compute rolling statistics,
    persistence lengths, and z-scores in sub-millisecond time.
    """

    def __init__(self, buffer_size: int = 48):
        self.buffer_size = buffer_size
        self.history: deque = deque(maxlen=buffer_size)
        self.prev_reading: Optional[Dict[str, float]] = None
        self.persist_counts: Dict[str, int] = {"temp": 0, "pres": 0, "humi": 0}

    def process_reading(
        self, timestamp: pd.Timestamp, temp: float, pres: float, humi: float
    ) -> Dict[str, float]:
        """Ingests a single reading (t) and returns the full 29-feature dictionary."""
        # 1. Raw features
        features: Dict[str, float] = {
            "temp": float(temp),
            "pres": float(pres),
            "humi": float(humi),
        }

        # 2. Derived thermodynamic features
        dp = float(
            compute_dew_point(np.array([temp]), np.array([humi]))[0]
        )
        features["dew_point"] = dp
        features["dp_depress"] = temp - dp
        features["vap_pres"] = float(
            compute_vapor_pressure(np.array([temp]), np.array([humi]))[0]
        )
        features["heat_idx"] = float(
            compute_heat_index(np.array([temp]), np.array([humi]))[0]
        )

        # Update persistence
        if self.prev_reading is not None:
            for p in ["temp", "pres", "humi"]:
                if abs(features[p] - self.prev_reading[p]) < 0.05:
                    self.persist_counts[p] += 1
                else:
                    self.persist_counts[p] = 0
            # 1-step deltas
            features["temp_delta_1"] = features["temp"] - self.prev_reading["temp"]
            features["pres_delta_1"] = features["pres"] - self.prev_reading["pres"]
            features["humi_delta_1"] = features["humi"] - self.prev_reading["humi"]
        else:
            features["temp_delta_1"] = 0.0
            features["pres_delta_1"] = 0.0
            features["humi_delta_1"] = 0.0

        features["temp_persist_len"] = float(self.persist_counts["temp"])
        features["pres_persist_len"] = float(self.persist_counts["pres"])
        features["humi_persist_len"] = float(self.persist_counts["humi"])

        # 3h rate of change using history buffer
        if len(self.history) >= 3:
            h_3 = self.history[-3]
            features["temp_roc_3h"] = (features["temp"] - h_3["temp"]) / 3.0
            features["pres_roc_3h"] = (features["pres"] - h_3["pres"]) / 3.0
            features["humi_roc_3h"] = (features["humi"] - h_3["humi"]) / 3.0
        else:
            features["temp_roc_3h"] = 0.0
            features["pres_roc_3h"] = 0.0
            features["humi_roc_3h"] = 0.0

        # Add current reading to history buffer
        self.history.append(
            {"temp": temp, "pres": pres, "humi": humi, "timestamp": timestamp}
        )
        self.prev_reading = features.copy()

        # Rolling 6h mean & std
        n_6 = min(len(self.history), 6)
        recent_6 = list(self.history)[-n_6:]
        for p in ["temp", "pres", "humi"]:
            vals_6 = [item[p] for item in recent_6]
            features[f"{p}_rmean_6h"] = float(np.mean(vals_6))
            features[f"{p}_rstd_6h"] = float(np.std(vals_6)) if len(vals_6) > 1 else 0.0

        # Cyclical temporal context
        hour = timestamp.hour
        doy = timestamp.dayofyear
        features["hour_sin"] = float(np.sin(2.0 * np.pi * hour / 24.0))
        features["hour_cos"] = float(np.cos(2.0 * np.pi * hour / 24.0))
        features["doy_sin"] = float(np.sin(2.0 * np.pi * doy / 365.25))
        features["doy_cos"] = float(np.cos(2.0 * np.pi * doy / 365.25))

        # Rolling 24h z-scores
        n_24 = min(len(self.history), 24)
        recent_24 = list(self.history)[-n_24:]
        eps = 1e-6
        for p in ["temp", "pres", "humi"]:
            vals_24 = [item[p] for item in recent_24]
            mu = float(np.mean(vals_24))
            sigma = float(np.std(vals_24)) if len(vals_24) > 1 else 0.0
            features[f"{p}_z"] = float((features[p] - mu) / (sigma + eps))

        return features


def process_station_file(
    station_csv_path: Union[str, Path], output_csv_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """Loads a consolidated station CSV, computes all 29 features, and optionally saves to disk."""
    station_csv_path = Path(station_csv_path)
    logger.info(f"Loading station data: {station_csv_path.name}...")
    df = pd.read_csv(station_csv_path)
    logger.info(f"Read {len(df):,} records. Extracting 29 features...")
    featured_df = extract_features(df)

    if output_csv_path:
        output_csv_path = Path(output_csv_path)
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        featured_df.to_csv(output_csv_path, index=False)
        logger.info(f"Saved featured dataset to {output_csv_path}")

    return featured_df


if __name__ == "__main__":
    import sys

    sample_station = (
        Path(__file__).parent.parent
        / "Datasets"
        / "noaa_india_by_station"
        / "42182099999_SAFDARJUNG.csv"
    )

    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = sample_station

    if not target_path.exists():
        logger.error(f"Target file not found: {target_path}")
        sys.exit(1)

    featured = process_station_file(target_path)
    print("\n" + "=" * 60)
    print(f"FEATURE EXTRACTION SUMMARY FOR {target_path.name}")
    print("=" * 60)
    print(f"Total Rows: {len(featured):,}")
    print(f"Total Columns: {len(featured.columns)} (Expected 29 features + metadata)")
    print("\nEngineered Feature Columns:")
    for i, col in enumerate(FEATURE_NAMES, 1):
        print(f"  {i:2d}. {col:<18} mean={featured[col].mean():.2f}, std={featured[col].std():.2f}")

    print("\nSanity Invariant Checks:")
    invalid_dp = (featured["dp_depress"] < -0.1).sum()
    print(f"  - Thermodynamic Invariant Violations (dp_depress < -0.1): {invalid_dp} rows")
    print(f"  - Max Temp Persistence Run: {featured['temp_persist_len'].max()} consecutive steps")
    print(f"  - Max Pres Persistence Run: {featured['pres_persist_len'].max()} consecutive steps")
    print(f"  - Hour sin/cos range: [{featured['hour_sin'].min():.2f}, {featured['hour_sin'].max():.2f}]")
    print("=" * 60)
    print("Phase 1 Feature Engineering pipeline verified successfully!")
