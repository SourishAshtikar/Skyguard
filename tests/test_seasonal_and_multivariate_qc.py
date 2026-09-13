"""
Tests for Seasonal Climatology, Precipitation-Conditioned Physics,
and Multivariate Imputation/Detection (Temperature, Pressure, Humidity).
"""

import pytest
from skyguard.tier1 import Tier1Engine, Tier1Rules
from skyguard.config.contracts import QCStatus, Severity, SensorReading
from skyguard.correction import SafeImputer
from skyguard.spatial import SpatialNeighborResolver
from skyguard.health import SensorHealthTracker
from skyguard.pipeline import SkyGuardPipeline


def test_mumbai_monsoon_spike_44c():
    """
    User scenario:
    In Mumbai (lat ~19.07°N), currently raining during Southwest Monsoon (month 9).
    Sensor spikes +18°C to 44.0°C with 85% relative humidity.
    Must trigger SEASONAL_RANGE_CHECK and RAIN_THERMAL_INCONSISTENCY with CRITICAL severity.
    """
    rules = Tier1Rules()
    
    # 1. Seasonal Range Check: 44.0°C in Mumbai (lat 19.07) in Sept (month 9)
    res_seasonal = rules.check_seasonal_range(
        temp=44.0, pres=1008.0, humi=85.0, latitude=19.07, month=9
    )
    assert not res_seasonal.passed
    assert res_seasonal.rule_name == "SEASONAL_RANGE_CHECK"
    assert res_seasonal.severity == Severity.CRITICAL
    assert "Southwest Monsoon ceiling" in res_seasonal.message

    # 2. Rain Thermal Consistency: 44.0°C during active rain or 85% RH
    res_rain = rules.check_rain_thermal_consistency(
        temp=44.0, humi=85.0, is_precipitating=True
    )
    assert not res_rain.passed
    assert res_rain.rule_name == "RAIN_THERMAL_INCONSISTENCY"
    assert res_rain.severity == Severity.CRITICAL
    assert "evaporative" in res_rain.message.lower() or "vapor pressure" in res_rain.message.lower()

    # 3. Aggregate Tier 1 evaluation
    engine = Tier1Engine(rules)
    features = {
        "temp": 44.0,
        "pres": 1008.0,
        "humi": 85.0,
        "dew_point": 41.2,
        "dp_depress": 2.8,
        "month": 9.0,
        "temp_delta_1": 18.0,
        "pres_delta_1": 0.0,
        "humi_delta_1": 0.0,
    }
    out = engine.evaluate(
        temp=44.0, pres=1008.0, humi=85.0,
        features=features, latitude=19.07, timestamp="2026-09-13T14:00:00",
        is_precipitating=True
    )
    assert out.status == QCStatus.FAIL
    assert "SEASONAL_RANGE_CHECK" in out.rules_fired
    assert "RAIN_THERMAL_INCONSISTENCY" in out.rules_fired


def test_normal_mumbai_monsoon_reading_passes():
    """A realistic monsoon reading in Mumbai (27.5°C, 88% RH, active rain) must PASS without false alarms."""
    rules = Tier1Rules()
    engine = Tier1Engine(rules)
    features = {
        "temp": 27.5,
        "pres": 1008.0,
        "humi": 88.0,
        "dew_point": 25.3,
        "dp_depress": 2.2,
        "month": 9.0,
        "temp_delta_1": 0.2,
        "pres_delta_1": 0.1,
        "humi_delta_1": 0.5,
        "temp_persist_len": 0,
        "pres_persist_len": 0,
        "humi_persist_len": 0,
    }
    out = engine.evaluate(
        temp=27.5, pres=1008.0, humi=88.0,
        features=features, latitude=19.07, timestamp="2026-09-13T14:00:00",
        is_precipitating=True
    )
    assert out.status == QCStatus.PASS
    assert "SEASONAL_RANGE_CHECK" not in out.rules_fired
    assert "RAIN_THERMAL_INCONSISTENCY" not in out.rules_fired


def test_winter_north_india_climatology():
    """In Delhi (lat 28.6°N) in January (month 1), 36°C is impossible and must fail."""
    rules = Tier1Rules()
    res = rules.check_seasonal_range(temp=36.0, pres=1018.0, humi=45.0, latitude=28.6, month=1)
    assert not res.passed
    assert res.severity == Severity.CRITICAL or res.severity == Severity.HIGH
    assert "Winter ceiling" in res.message


def test_pressure_and_humidity_spatial_consensus_deviation():
    """
    Validates that a pressure calibration drift (e.g. +8.5 hPa) or humidity divergence
    is detected by the spatial mesonet consensus check.
    """
    from pathlib import Path
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=250.0)
    # Mock neighboring telemetry around a target station (Delhi 42182099999)
    neighbors = resolver.find_nearest_neighbors("42182099999")
    assert len(neighbors) > 0

    neighbor_tel = {}
    for n in neighbors:
        neighbor_tel[n["station_id"]] = {
            "temperature": 27.5,
            "pressure": 1010.0,
            "humidity": 82.0,
        }

    # Station reporting 1018.5 hPa (+8.5 hPa calibration drift)
    consensus = resolver.evaluate_consensus(
        target_station_id="42182099999",
        target_temp=27.5,
        target_pres=1018.5,
        target_humi=82.0,
        neighbor_telemetry=neighbor_tel,
    )

    assert consensus.target_deviation_pres == pytest.approx(8.5, abs=0.1)
    assert consensus.is_spatially_inconsistent is True
    assert consensus.spatial_consensus_score < 0.20


def test_multivariate_safe_imputation_predicts_all_parameters():
    """
    Validates that when telemetry is missing (e.g. transmission dropout where T, P, H are None),
    SafeImputer accurately predicts and reconstructs Temperature, Pressure, AND Humidity.
    """
    imputer = SafeImputer()
    corrected = imputer.impute(
        raw_temp=None,
        raw_pres=None,
        raw_humi=None,
        is_anomaly=True,
    )

    assert corrected.applied is True
    assert corrected.temperature is not None
    assert corrected.pressure is not None
    assert corrected.humidity is not None
    assert 20.0 <= corrected.temperature <= 40.0
    assert 950.0 <= corrected.pressure <= 1040.0
    assert 10.0 <= corrected.humidity <= 100.0


def test_active_anomaly_health_tracker_action_not_nominal():
    """
    Validates that when an anomaly occurs, the health tracker produces an active
    fault status and mitigation action, and does NOT claim 'Nominal: No action required'.
    """
    tracker = SensorHealthTracker(station_id="43887099999")
    # First cycle has an anomaly
    metric = tracker.update(
        timestamp="2026-09-13T14:00:00",
        is_anomaly=True,
        is_missing=False,
        drift_delta=18.0,
    )

    assert metric.status in ("FAULT_DETECTED", "CRITICAL")
    assert "Nominal" not in metric.recommended_action
    assert "Malfunction" in metric.recommended_action or "inspection" in metric.recommended_action
