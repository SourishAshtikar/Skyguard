"""
Tests for Phase 2: Anomaly Injector and Dataset Builder
Validates all 10 anomaly types and metadata integrity.
"""

import pandas as pd
import pytest
from skyguard.data import AnomalyInjector, DatasetBuilder


@pytest.fixture
def clean_baseline_df():
    dates = pd.date_range("2026-05-01", periods=200, freq="h")
    return pd.DataFrame({
        "timestamp": dates,
        "temperature": [28.0 + 5.0 * (i % 24) / 24.0 for i in range(200)],
        "pressure": [1010.0 + (i % 12) * 0.2 for i in range(200)],
        "humidity": [60.0 - (i % 24) * 0.8 for i in range(200)],
    })


def test_all_10_anomaly_injections(clean_baseline_df):
    injector = AnomalyInjector(random_seed=123)

    # 1. Spike
    df1, m1 = injector.inject_spike(clean_baseline_df, start_idx=20)
    assert df1.loc[20, "is_anomaly"] == 1
    assert m1.anomaly_type == "SENSOR_SPIKE"

    # 2. Frozen
    df2, m2 = injector.inject_frozen(clean_baseline_df, start_idx=40, duration=10)
    assert (df2.loc[40:50, "is_anomaly"] == 1).all()
    assert (df2.loc[40:50, "humidity"].diff().iloc[1:] == 0.0).all()

    # 3. Calibration Drift
    df3, m3 = injector.inject_calibration_drift(clean_baseline_df, start_idx=60, duration=20)
    assert df3.loc[60, "is_anomaly"] == 1
    assert df3.loc[79, "pressure"] > clean_baseline_df.loc[79, "pressure"]

    # 4. Dropout
    df4, m4 = injector.inject_communication_dropout(clean_baseline_df, start_idx=80, duration=5)
    assert pd.isna(df4.loc[80, "temperature"])
    assert df4.loc[80, "is_anomaly"] == 1

    # 5. Packet Corruption
    df5, m5 = injector.inject_packet_corruption(clean_baseline_df, start_idx=100)
    assert df5.loc[100, "temperature"] > 200.0

    # 6. Physical Inconsistency
    df6, m6 = injector.inject_physical_inconsistency(clean_baseline_df, start_idx=110, duration=4)
    assert df6.loc[110, "temperature"] == 2.0
    assert df6.loc[110, "humidity"] == 99.0

    # 7. Noise Jitter
    df7, m7 = injector.inject_noise_jitter(clean_baseline_df, start_idx=120, duration=10)
    assert df7.loc[120, "is_anomaly"] == 1

    # 8. Range Violation
    df8, m8 = injector.inject_range_violation(clean_baseline_df, start_idx=140)
    assert df8.loc[140, "temperature"] > 55.0

    # 9. Spatial Inconsistency
    df9, m9 = injector.inject_spatial_inconsistency(clean_baseline_df, start_idx=150, duration=6)
    assert df9.loc[150, "temperature"] > clean_baseline_df.loc[150, "temperature"] + 10.0

    # 10. Temporal Pattern Break
    df10, m10 = injector.inject_temporal_pattern_break(clean_baseline_df, start_idx=170, duration=12)
    assert df10.loc[170, "is_anomaly"] == 1


def test_dataset_builder_pipeline(clean_baseline_df):
    builder = DatasetBuilder(random_seed=42)
    df, metas = builder.generate_benchmark_dataset(clean_baseline_df, num_episodes=8)
    assert len(metas) >= 5
    assert df["is_anomaly"].sum() > 0

    train, val, test = builder.split_chronological(df)
    assert len(train) + len(val) + len(test) == len(df)
    assert len(train) > len(val)
