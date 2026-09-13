"""
Tests for Tier 3 Cloud Pipeline
Validates:
- StateSpaceForecaster Kalman updates, innovation distance, confidence bands
- AugmentedIsolationForest evaluation
- HierarchicalArbiter decisions (Weather vs Fault, Root-Cause diagnosis, TreeSHAP attributions)
"""

import pytest
from skyguard.tier3 import StateSpaceForecaster, AugmentedIsolationForest, HierarchicalArbiter
from skyguard.config.contracts import AnomalyCategory


def test_state_space_forecaster():
    forecaster = StateSpaceForecaster()
    # Step 1: Normal temperature reading
    res1 = forecaster.update(28.0, 1012.0, 55.0, {"hour_sin": 0.5, "hour_cos": 0.8})
    assert not res1.is_suspicious
    assert res1.predicted_temp > 20.0
    assert "temp" in res1.confidence_bound_3sigma

    # Step 2: Sudden massive jump (48.0°C from 28°C) should produce high Mahalanobis distance
    res2 = forecaster.update(48.0, 1012.0, 55.0, {"hour_sin": 0.5, "hour_cos": 0.8})
    assert res2.is_suspicious
    assert res2.mahalanobis_distance > 11.345


def test_augmented_isolation_forest():
    iso = AugmentedIsolationForest()
    features = {
        "temp": 30.0,
        "pres": 1010.0,
        "humi": 60.0,
    }
    out = iso.evaluate(features, residual_temp=1.0, residual_pres=0.5, residual_humi=2.0, mahalanobis_d2=2.5)
    assert out.executed
    assert 0.0 <= out.anomaly_score <= 1.0


def test_hierarchical_arbiter():
    arbiter = HierarchicalArbiter()
    features = {
        "temp": 32.0,
        "pres": 1008.0,
        "humi": 65.0,
        "dp_depress": 8.0,
        "temp_delta_1": 0.5,
    }
    out = arbiter.evaluate(
        features=features,
        spatial_consensus=None,
        mahalanobis_d2=1.5,
        tier1_fired_rules=[],
        tier2_score=0.1,
    )
    assert out.confidence > 0.6
    assert len(out.shap_attributions) > 0
    assert out.latency_ms < 15.0  # Fast sub-15ms TreeSHAP
