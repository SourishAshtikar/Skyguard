"""
Tests for Master Orchestration Pipeline
Validates:
- End-to-end execution of all 3 tiers in a single call
- Correct diagnostic result object format and properties
- Detection of synthetic spikes and persistence failures
- Safe imputation behavior
"""

import pytest
from skyguard.pipeline import SkyGuardPipeline
from skyguard.config.contracts import QCStatus, SensorReading


def test_pipeline_normal_reading():
    pipeline = SkyGuardPipeline(station_id="42182099999", station_name="SAFDARJUNG")
    reading = SensorReading(
        timestamp="2026-06-15T12:00:00",
        station_id="42182099999",
        station_name="SAFDARJUNG",
        latitude=28.58,
        longitude=77.20,
        temperature=34.0,
        pressure=1004.0,
        humidity=55.0,
    )

    result = pipeline.process(reading)
    assert result.final_status == QCStatus.PASS
    assert not result.final_anomaly
    assert result.total_latency_ms < 50.0  # < 50ms latency budget
    assert "NOMINAL" in result.plain_english_rca
    assert result.sensor_health.status == "HEALTHY"


def test_pipeline_spike_anomaly():
    pipeline = SkyGuardPipeline(station_id="42182099999", station_name="SAFDARJUNG")
    # Feed 3 normal readings first
    for h in [10, 11, 12]:
        pipeline.process(SensorReading(
            timestamp=f"2026-06-15T{h}:00:00",
            station_id="42182099999",
            station_name="SAFDARJUNG",
            latitude=28.58,
            longitude=77.20,
            temperature=30.0,
            pressure=1005.0,
            humidity=60.0,
        ))

    # Injected spike: +18°C temperature jump
    spike_reading = SensorReading(
        timestamp="2026-06-15T13:00:00",
        station_id="42182099999",
        station_name="SAFDARJUNG",
        latitude=28.58,
        longitude=77.20,
        temperature=48.0,
        pressure=1005.0,
        humidity=60.0,
    )
    result = pipeline.process(spike_reading)
    assert result.final_anomaly
    assert result.tier1.status in (QCStatus.SUSPECT, QCStatus.FAIL)
    # Check that safe imputation suggested a corrected value close to normal
    assert result.corrected_telemetry.applied
    assert abs(result.corrected_telemetry.temperature - 30.0) < 5.0
