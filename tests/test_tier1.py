"""
Tests for Phase 3: Tier 1 Deterministic QC Engine
Validates:
- Range checks (temperature, pressure, humidity bounds)
- Step rate-of-change checks
- Persistence stuck-sensor detection
- Dew-point physical invariant checks
- Missing data handling
- Aggregate status (PASS, SUSPECT, FAIL)
"""

import pytest
from skyguard.tier1 import Tier1Engine
from skyguard.config.contracts import QCStatus, Severity


@pytest.fixture
def tier1_engine():
    return Tier1Engine()


def test_tier1_normal_reading(tier1_engine):
    features = {
        "temp": 28.0,
        "pres": 1012.0,
        "humi": 55.0,
        "dew_point": 18.0,
        "dp_depress": 10.0,
        "temp_delta_1": 0.5,
        "pres_delta_1": 0.2,
        "humi_delta_1": 1.0,
        "temp_persist_len": 0,
        "pres_persist_len": 0,
        "humi_persist_len": 0,
    }
    res = tier1_engine.evaluate(28.0, 1012.0, 55.0, features)
    assert res.status == QCStatus.PASS
    assert len(res.rules_fired) == 0
    assert res.latency_ms < 5.0  # sub-millisecond expected


def test_tier1_range_violation(tier1_engine):
    features = {
        "temp": 62.0,  # Impossible in India (>55°C)
        "pres": 1012.0,
        "humi": 30.0,
        "dew_point": 15.0,
        "dp_depress": 47.0,
    }
    res = tier1_engine.evaluate(62.0, 1012.0, 30.0, features)
    assert res.status == QCStatus.FAIL
    assert "RANGE_CHECK" in res.rules_fired


def test_tier1_step_jump(tier1_engine):
    features = {
        "temp": 35.0,
        "pres": 1012.0,
        "humi": 50.0,
        "dew_point": 23.0,
        "dp_depress": 12.0,
        "temp_delta_1": 12.0,  # Jump 12°C in one hour!
        "pres_delta_1": 0.0,
        "humi_delta_1": 0.0,
        "temp_rstd_6h": 1.0,
    }
    res = tier1_engine.evaluate(35.0, 1012.0, 50.0, features)
    assert res.status in (QCStatus.SUSPECT, QCStatus.FAIL)
    assert "STEP_CHECK" in res.rules_fired


def test_tier1_stuck_sensor(tier1_engine):
    features = {
        "temp": 28.0,
        "pres": 1012.0,
        "humi": 75.0,
        "dew_point": 23.0,
        "dp_depress": 5.0,
        "humi_persist_len": 8,  # Stuck for 8 hours
    }
    res = tier1_engine.evaluate(28.0, 1012.0, 75.0, features)
    assert res.status == QCStatus.FAIL
    assert "PERSISTENCE_CHECK" in res.rules_fired


def test_tier1_dew_point_invariant(tier1_engine):
    # Impossible: Dew point higher than air temp by 3°C
    features = {
        "temp": 20.0,
        "pres": 1012.0,
        "humi": 99.0,
        "dew_point": 23.0,
        "dp_depress": -3.0,
    }
    res = tier1_engine.evaluate(20.0, 1012.0, 99.0, features)
    assert res.status == QCStatus.FAIL
    assert "DEW_POINT_INVARIANT" in res.rules_fired


def test_tier1_missing_telemetry(tier1_engine):
    res = tier1_engine.evaluate(None, 1012.0, None, {})
    assert "MISSING_DATA_CHECK" in res.rules_fired
