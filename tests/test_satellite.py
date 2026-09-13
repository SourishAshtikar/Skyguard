"""
Unit Tests for SkyGuard AI Satellite Imagery & Thermal IR Cross-Checking Engine
"""

from datetime import datetime
import pytest

from skyguard.config.contracts import (
    AnomalyCategory,
    QCStatus,
    SensorReading,
    Severity,
)
from skyguard.pipeline.orchestrator import SkyGuardPipeline
from skyguard.satellite.cross_checker import (
    INSATSatelliteValidator,
    OfflineRadiativeModel,
)


def test_offline_radiative_model_solar_zenith():
    """Verifies that the deterministic radiative energy balance model calculates daytime solar heating."""
    model = OfflineRadiativeModel()

    # Noon in New Delhi (peak solar heating)
    res_noon = model.fetch_pixel_data(28.58, 77.20, "2026-05-15T12:00:00")
    assert res_noon["cos_zenith"] > 0.80
    assert res_noon["expected_skin_delta_c"] > 4.0  # Sun warms ground above air temp

    # Midnight in New Delhi (radiative cooling)
    res_night = model.fetch_pixel_data(28.58, 77.20, "2026-05-15T00:00:00")
    assert res_night["cos_zenith"] == 0.0
    assert res_night["expected_skin_delta_c"] <= 0.0


def test_satellite_thermal_consistency_nominal():
    """Verifies nominal thermal agreement between AWS air temp and satellite LST."""
    validator = INSATSatelliteValidator()

    sat_obs = {
        "satellite_id": "INSAT-3DR",
        "land_surface_temp_c": 32.5,
        "expected_skin_delta_c": 4.5,
        "cloud_fraction_pct": 15.0,
        "cloud_top_temp_c": 12.0,
    }

    out = validator.evaluate_satellite_consistency(
        station_id="42182099999",
        latitude=28.58,
        longitude=77.20,
        timestamp="2026-05-15T12:00:00",
        target_temp=28.0,  # 32.5 - 4.5 = 28.0 (exact match)
        target_pres=1005.0,
        target_humi=45.0,
        satellite_obs=sat_obs,
    )

    assert out.is_satellite_inconsistent is False
    assert out.temp_consistency_score > 0.95
    assert out.satellite_consensus_score > 0.90
    assert "Verified by INSAT-3DR" in out.satellite_note


def test_satellite_thermal_divergence_alert():
    """Verifies that severe temperature divergence under clear skies triggers thermal alert."""
    validator = INSATSatelliteValidator()

    sat_obs = {
        "satellite_id": "INSAT-3DR",
        "land_surface_temp_c": 26.0,
        "expected_skin_delta_c": 3.0,
        "cloud_fraction_pct": 5.0,  # Clear sky
    }

    out = validator.evaluate_satellite_consistency(
        station_id="42182099999",
        latitude=28.58,
        longitude=77.20,
        timestamp="2026-05-15T12:00:00",
        target_temp=46.0,  # Thermocouple reading 46°C vs adjusted LST 23°C (23°C gap!)
        target_pres=1005.0,
        target_humi=30.0,
        satellite_obs=sat_obs,
    )

    assert out.is_satellite_inconsistent is True
    assert out.temp_consistency_score < 0.20
    assert "Thermal divergence alert" in out.satellite_note


def test_convective_storm_corroboration():
    """Verifies that cold cloud top (CTT < -40°C) corroborates sudden temperature drop as genuine severe weather."""
    validator = INSATSatelliteValidator()

    sat_obs = {
        "satellite_id": "INSAT-3DR",
        "land_surface_temp_c": 18.0,
        "cloud_top_temp_c": -52.0,  # Deep convective anvil cloud
        "cloud_fraction_pct": 95.0,
    }

    out = validator.evaluate_satellite_consistency(
        station_id="42182099999",
        latitude=28.58,
        longitude=77.20,
        timestamp="2026-07-15T16:00:00",
        target_temp=20.0,
        target_pres=992.0,
        target_humi=92.0,
        satellite_obs=sat_obs,
    )

    assert out.is_convective_storm_confirmed is True
    assert out.is_satellite_inconsistent is False
    assert "Deep convective cloud top" in out.satellite_note


def test_moisture_sensor_false_saturation():
    """Verifies that reporting 100% RH under 0% satellite cloud cover is flagged as sensor fault."""
    validator = INSATSatelliteValidator()

    sat_obs = {
        "satellite_id": "INSAT-3D",
        "land_surface_temp_c": 35.0,
        "cloud_fraction_pct": 0.0,  # Clear sky desert
        "cloud_top_temp_c": None,
    }

    out = validator.evaluate_satellite_consistency(
        station_id="42182099999",
        latitude=28.58,
        longitude=77.20,
        timestamp="2026-05-15T14:00:00",
        target_temp=33.0,
        target_pres=1002.0,
        target_humi=99.5,  # Saturated humidity impossible with 0% cloud cover
        satellite_obs=sat_obs,
    )

    assert out.is_satellite_inconsistent is True
    assert out.cloud_consistency_score < 0.30
    assert "Moisture invariant violation" in out.satellite_note


def test_pipeline_satellite_integration():
    """Verifies end-to-end SkyGuard pipeline execution with satellite cross-checking active."""
    pipeline = SkyGuardPipeline(station_id="42182099999", station_name="SAFDARJUNG")

    # Nominal reading
    reading = SensorReading(
        timestamp="2026-05-15T12:00:00",
        station_id="42182099999",
        station_name="SAFDARJUNG",
        latitude=28.58,
        longitude=77.20,
        temperature=32.0,
        pressure=1004.0,
        humidity=40.0,
    )

    res = pipeline.process(reading)

    assert res.satellite_cross_check is not None
    assert res.satellite_cross_check.satellite_id.startswith("INSAT")
    assert res.satellite_cross_check.satellite_consensus_score > 0.0
    assert "satellite_cross_check" in res.to_dict()
    assert res.to_dict()["satellite_cross_check"]["satellite_id"] is not None

    # Test severe weather confirmation via satellite
    storm_reading = SensorReading(
        timestamp="2026-07-15T16:00:00",
        station_id="42182099999",
        station_name="SAFDARJUNG",
        latitude=28.58,
        longitude=77.20,
        temperature=22.0,
        pressure=990.0,
        humidity=95.0,
    )

    sat_storm = {
        "satellite_id": "INSAT-3DR",
        "land_surface_temp_c": 21.0,
        "cloud_top_temp_c": -55.0,
        "cloud_fraction_pct": 100.0,
    }

    storm_res = pipeline.process(storm_reading, satellite_observation=sat_storm)
    assert storm_res.satellite_cross_check.is_convective_storm_confirmed is True
    assert storm_res.final_status == QCStatus.PASS
    assert storm_res.final_anomaly is False  # Genuine severe weather is not a sensor fault!
