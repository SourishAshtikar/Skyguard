"""
SkyGuard AI — Vectorized Batch Feature Engineering
Computes all 29 canonical engineered features on historical pandas DataFrames.
"""

from typing import List
import numpy as np
import pandas as pd

from .streaming import CANONICAL_FEATURES
from .thermodynamics import (
    compute_dew_point,
    compute_vapor_pressure,
    compute_heat_index,
)


def extract_batch_features(
    df: pd.DataFrame,
    temp_col: str = "temperature",
    pres_col: str = "pressure",
    humi_col: str = "humidity",
    time_col: str = "timestamp",
    sort: bool = True,
) -> pd.DataFrame:
    """Extracts all 29 features from a DataFrame. Preserves existing metadata columns."""
    out = df.copy()

    if not pd.api.types.is_datetime64_any_dtype(out[time_col]):
        out[time_col] = pd.to_datetime(out[time_col])

    if sort:
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

    # 3. 1-step deltas
    out["temp_delta_1"] = out["temp"].diff().fillna(0.0)
    out["pres_delta_1"] = out["pres"].diff().fillna(0.0)
    out["humi_delta_1"] = out["humi"].diff().fillna(0.0)

    # 3-hour rates of change
    out["temp_roc_3h"] = ((out["temp"] - out["temp"].shift(3)) / 3.0).fillna(0.0)
    out["pres_roc_3h"] = ((out["pres"] - out["pres"].shift(3)) / 3.0).fillna(0.0)
    out["humi_roc_3h"] = ((out["humi"] - out["humi"].shift(3)) / 3.0).fillna(0.0)

    # 6-hour rolling statistics
    for p in ["temp", "pres", "humi"]:
        out[f"{p}_rmean_6h"] = out[p].rolling(window=6, min_periods=1).mean().fillna(out[p])
        out[f"{p}_rstd_6h"] = out[p].rolling(window=6, min_periods=1).std(ddof=0).fillna(0.0)

    # 4. Persistence run lengths (diff < 0.05)
    for p in ["temp", "pres", "humi"]:
        diffs = out[p].diff().abs() < 0.05
        block_id = (~diffs).cumsum()
        persist_len = diffs.groupby(block_id).cumsum()
        out[f"{p}_persist_len"] = persist_len.fillna(0).astype(float)

    # 5. Cyclical temporal context
    hours = out[time_col].dt.hour.values
    doys = out[time_col].dt.dayofyear.values
    out["hour_sin"] = np.sin(2.0 * np.pi * hours / 24.0)
    out["hour_cos"] = np.cos(2.0 * np.pi * hours / 24.0)
    out["doy_sin"] = np.sin(2.0 * np.pi * doys / 365.25)
    out["doy_cos"] = np.cos(2.0 * np.pi * doys / 365.25)

    # 6. Rolling 24-hour Z-scores
    eps = 1e-6
    for p in ["temp", "pres", "humi"]:
        r_mean = out[p].rolling(window=24, min_periods=1).mean()
        r_std = out[p].rolling(window=24, min_periods=1).std(ddof=0).fillna(0.0)
        out[f"{p}_z"] = (out[p] - r_mean) / (r_std + eps)

    return out
