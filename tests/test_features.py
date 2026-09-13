"""
Tests for Phase 1: Feature Engineering Pipeline
Validates:
- Magnus dew point thermodynamic consistency
- Vapor pressure calculation
- Heat index Rothfusz regression
- Exactly 29 canonical features
- Persistence reset behavior
- Equivalence between batch and streaming extractors
"""

import numpy as np
import pandas as pd
import pytest

from skyguard.features import (
    compute_dew_point,
    compute_vapor_pressure,
    compute_heat_index,
    StreamingFeatureExtractor,
    extract_batch_features,
    CANONICAL_FEATURES,
)


def test_dew_point_physical_properties():
    # T = 30°C, RH = 100% -> Dew point must equal air temperature (within 0.05°C)
    dp_sat = compute_dew_point(30.0, 100.0)
    assert abs(dp_sat - 30.0) < 0.05

    # T = 30°C, RH = 50% -> Dew point must be strictly less than air temperature
    dp_sub = compute_dew_point(30.0, 50.0)
    assert dp_sub < 30.0
    assert 17.0 < dp_sub < 20.0  # Physical meteorology reference: ~18.4°C

    # Low humidity edge case (RH = 0.0% clamped safely without NaN)
    dp_zero = compute_dew_point(25.0, 0.0)
    assert not np.isnan(dp_zero)


def test_vapor_pressure():
    # Vapor pressure at 20°C, 50% RH
    vp = compute_vapor_pressure(20.0, 50.0)
    assert not np.isnan(vp)
    assert 10.0 < vp < 13.0  # Saturation vapor pressure at 20°C is ~23.4 hPa, 50% is ~11.7 hPa


def test_heat_index():
    # Cold temperatures (< 20°C) must default to air temperature
    assert compute_heat_index(15.0, 80.0) == 15.0
    # Hot and humid (e.g. 35°C and 70% RH) must produce high apparent temperature > 45°C
    hi_hot = compute_heat_index(35.0, 70.0)
    assert hi_hot > 45.0


def test_canonical_feature_count():
    assert len(CANONICAL_FEATURES) == 29


def test_streaming_extractor_step():
    extractor = StreamingFeatureExtractor(buffer_size=48)
    feats1 = extractor.process("2026-06-01T10:00:00", 32.0, 1005.0, 65.0)
    assert len(feats1) == 29
    assert feats1["temp"] == 32.0
    assert feats1["temp_persist_len"] == 0.0

    # Second reading identical -> persistence should increment to 1
    feats2 = extractor.process("2026-06-01T11:00:00", 32.0, 1005.0, 65.0)
    assert feats2["temp_persist_len"] == 1.0

    # Third reading changed -> persistence resets to 0
    feats3 = extractor.process("2026-06-01T12:00:00", 34.0, 1004.0, 60.0)
    assert feats3["temp_persist_len"] == 0.0


def test_batch_and_streaming_consistency():
    dates = pd.date_range("2026-01-01", periods=10, freq="h")
    temps = [25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5]
    press = [1013.0, 1012.8, 1012.5, 1012.0, 1011.5, 1011.0, 1010.5, 1010.0, 1009.5, 1009.0]
    humis = [60.0, 58.0, 55.0, 53.0, 50.0, 48.0, 45.0, 43.0, 40.0, 38.0]

    df = pd.DataFrame({
        "timestamp": dates,
        "temperature": temps,
        "pressure": press,
        "humidity": humis,
    })

    batch_res = extract_batch_features(df)
    assert len(batch_res) == 10
    for feat in CANONICAL_FEATURES:
        assert feat in batch_res.columns

    # Compare 5th row between batch and streaming
    extractor = StreamingFeatureExtractor()
    stream_rows = []
    for _, row in df.iterrows():
        s_feat = extractor.process(row["timestamp"], row["temperature"], row["pressure"], row["humidity"])
        stream_rows.append(s_feat)

    row5_batch = batch_res.iloc[4]
    row5_stream = stream_rows[4]
    assert abs(row5_batch["dew_point"] - row5_stream["dew_point"]) < 1e-4
    assert abs(row5_batch["vap_pres"] - row5_stream["vap_pres"]) < 1e-4
    assert abs(row5_batch["temp_rmean_6h"] - row5_stream["temp_rmean_6h"]) < 1e-4
