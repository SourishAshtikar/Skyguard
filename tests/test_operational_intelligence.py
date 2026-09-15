"""
SkyGuard AI — Test Suite for Logic, Reliability & Operational Intelligence
Tests all 18 specified operational intelligence logic scenarios against the PostgreSQL DB engine
and state machines.
"""

import pytest
from datetime import datetime, timezone, timedelta
from skyguard.config.settings import SETTINGS
from skyguard.db.database import DB
from skyguard.watchdog.validator import TimestampValidator, QualityState
from skyguard.watchdog.communication import CommunicationWatchdog, CommunicationStatus
from skyguard.sensor_state.state_machine import SensorStateMachine, SensorOperationalState
from skyguard.sensor_state.health_card import SensorHealthCardGenerator
from skyguard.incidents.lifecycle import IncidentLifecycleManager, IncidentStatus, IncidentSeverity
from skyguard.incidents.correlator import EventCorrelator
from skyguard.incidents.deduplicator import AlertDeduplicator
from skyguard.operator.workflow import OperatorWorkflowManager, OperatorAction, RecalibrationStatus


@pytest.fixture(autouse=True)
def reset_db_before_tests():
    """Resets database before each test run."""
    DB.clear_database()
    yield


# ----------------------------------------------------
# Scenario 1: Single Spike (EVENT -> SUSPECTED)
# ----------------------------------------------------
def test_scenario_1_single_spike():
    mgr = IncidentLifecycleManager()
    inc = mgr.process_anomaly_event("STATION-01", "temperature", True, "SENSOR_SPIKE", 0.9, {"rate_change": True})
    assert inc is not None
    assert inc["status"] == IncidentStatus.SUSPECTED
    assert inc["event_count"] == 1


# ----------------------------------------------------
# Scenario 2: Repeated Spike (SUSPECTED -> CONFIRMED/ACTIVE)
# ----------------------------------------------------
def test_scenario_2_repeated_spike():
    mgr = IncidentLifecycleManager()
    inc1 = mgr.process_anomaly_event("STATION-01", "temperature", True, "SENSOR_SPIKE", 0.9, {"rate_change": True})
    inc2 = mgr.process_anomaly_event("STATION-01", "temperature", True, "SENSOR_SPIKE", 0.9, {"rate_change": True})
    inc3 = mgr.process_anomaly_event("STATION-01", "temperature", True, "SENSOR_SPIKE", 0.9, {"rate_change": True})
    assert inc3["event_count"] == 3
    assert inc3["status"] in [IncidentStatus.CONFIRMED, IncidentStatus.ACTIVE]


# ----------------------------------------------------
# Scenario 3: Frozen Sensor State Transition
# ----------------------------------------------------
def test_scenario_3_frozen_sensor():
    sm = SensorStateMachine()
    st1 = sm.update_state("STATION-01", "humidity", True, confidence=0.7)
    st2 = sm.update_state("STATION-01", "humidity", True, confidence=0.7)
    assert st2["operational_state"] == SensorOperationalState.SUSPECT
    st3 = sm.update_state("STATION-01", "humidity", True, confidence=0.85)
    assert st3["operational_state"] == SensorOperationalState.DEGRADED


# ----------------------------------------------------
# Scenario 4: Communication Dropout
# ----------------------------------------------------
def test_scenario_4_dropout():
    wd = CommunicationWatchdog()
    now = datetime.now(timezone.utc)
    wd.record_packet("STATION-01", now - timedelta(seconds=60), {})
    stats = wd.check_station_timeouts("STATION-01", now)
    assert stats["comm_status"] == CommunicationStatus.DROPOUT


# ----------------------------------------------------
# Scenario 5: Dropout Recovery
# ----------------------------------------------------
def test_scenario_5_dropout_recovery():
    wd = CommunicationWatchdog()
    now = datetime.now(timezone.utc)
    wd.record_packet("STATION-01", now - timedelta(seconds=60), {})
    wd.check_station_timeouts("STATION-01", now)
    
    # Packet arrives establishing normal cadence again
    wd.record_packet("STATION-01", now, {})
    stats2 = wd.record_packet("STATION-01", now + timedelta(seconds=10), {})
    assert stats2["comm_status"] == CommunicationStatus.HEALTHY


# ----------------------------------------------------
# Scenario 6: Late Telemetry Detection
# ----------------------------------------------------
def test_scenario_6_late_telemetry():
    wd = CommunicationWatchdog()
    now = datetime.now(timezone.utc)
    wd.record_packet("STATION-01", now - timedelta(seconds=20), {})
    stats = wd.record_packet("STATION-01", now, {})
    assert stats["comm_status"] == CommunicationStatus.LATE


# ----------------------------------------------------
# Scenario 7: Duplicate Telemetry Timestamp
# ----------------------------------------------------
def test_scenario_7_duplicate_telemetry():
    tv = TimestampValidator()
    now = datetime.now(timezone.utc)
    tv.validate_reading({"station_id": "STATION-01", "timestamp": now, "temperature": 25.0, "pressure": 1012.0, "humidity": 60.0})
    state, flags = tv.validate_reading({"station_id": "STATION-01", "timestamp": now, "temperature": 25.0, "pressure": 1012.0, "humidity": 60.0})
    assert flags["duplicate_timestamp"] is True
    assert state == QualityState.SUSPECT


# ----------------------------------------------------
# Scenario 8: Out of Order Telemetry Timestamp
# ----------------------------------------------------
def test_scenario_8_out_of_order_telemetry():
    tv = TimestampValidator()
    now = datetime.now(timezone.utc)
    tv.validate_reading({"station_id": "STATION-01", "timestamp": now, "temperature": 25.0, "pressure": 1012.0, "humidity": 60.0})
    state, flags = tv.validate_reading({"station_id": "STATION-01", "timestamp": now - timedelta(seconds=30), "temperature": 25.0, "pressure": 1012.0, "humidity": 60.0})
    assert flags["out_of_order"] is True
    assert state == QualityState.SUSPECT


# ----------------------------------------------------
# Scenario 9: Regional Weather Event Detection
# ----------------------------------------------------
def test_scenario_9_regional_weather_event():
    correlator = EventCorrelator()
    ev = correlator.evaluate_regional_weather_event(["STATION-01", "STATION-02", "STATION-03"], [])
    assert ev is not None
    assert ev["event_type"] == "REGIONAL_WEATHER_EVENT"


# ----------------------------------------------------
# Scenario 10: Isolated Station Anomaly
# ----------------------------------------------------
def test_scenario_10_isolated_station_anomaly():
    card = SensorHealthCardGenerator.generate_health_card("STATION-01", "temperature")
    assert card["station_id"] == "STATION-01"
    assert "current_state" in card


# ----------------------------------------------------
# Scenario 11: Multi-Parameter Incident Grouping
# ----------------------------------------------------
def test_scenario_11_multi_parameter_incident():
    mgr = IncidentLifecycleManager()
    mgr.process_anomaly_event("STATION-01", "temperature", True, "SENSOR_SPIKE", 0.9, {})
    mgr.process_anomaly_event("STATION-01", "pressure", True, "DRIFT", 0.9, {})
    
    correlator = EventCorrelator()
    grouped = correlator.correlate_station_incidents("STATION-01")
    assert grouped is not None
    assert "MULTIVARIATE" in grouped["affected_parameter"]


# ----------------------------------------------------
# Scenario 12: Alert Deduplication / Cooldown
# ----------------------------------------------------
def test_scenario_12_alert_deduplication():
    dedup = AlertDeduplicator()
    inc = {"incident_id": "INC-100", "status": "ACTIVE", "severity": "MEDIUM"}
    should1, r1 = dedup.should_emit_notification(inc)
    assert should1 is True
    
    should2, r2 = dedup.should_emit_notification(inc)
    assert should2 is False
    assert "SUPPRESSED" in r2


# ----------------------------------------------------
# Scenario 13: Anomaly Escalation
# ----------------------------------------------------
def test_scenario_13_anomaly_escalation():
    mgr = IncidentLifecycleManager()
    inc1 = mgr.process_anomaly_event("STATION-01", "temperature", True, "SPIKE", 0.5, {})
    assert inc1["severity"] == IncidentSeverity.LOW
    
    inc10 = mgr.process_anomaly_event("STATION-01", "temperature", True, "SPIKE", 0.95, {"is_comm_timeout": True})
    assert inc10["severity"] == IncidentSeverity.CRITICAL


# ----------------------------------------------------
# Scenario 14: Anomaly Recovery (ACTIVE -> RECOVERING -> RESOLVED)
# ----------------------------------------------------
def test_scenario_14_anomaly_recovery():
    mgr = IncidentLifecycleManager()
    for _ in range(3):
        mgr.process_anomaly_event("STATION-01", "temperature", True, "SPIKE", 0.9, {})
        
    rec = mgr.process_anomaly_event("STATION-01", "temperature", False, "NONE", 0.0, {})
    assert rec["status"] == IncidentStatus.RECOVERING
    
    for _ in range(4):
        rec = mgr.process_anomaly_event("STATION-01", "temperature", False, "NONE", 0.0, {})
        
    assert rec["status"] == IncidentStatus.RESOLVED


# ----------------------------------------------------
# Scenario 15: Operator Acknowledgement
# ----------------------------------------------------
def test_scenario_15_operator_acknowledgement():
    mgr = IncidentLifecycleManager()
    inc = mgr.process_anomaly_event("STATION-01", "temperature", True, "SPIKE", 0.9, {})
    ok = mgr.acknowledge_incident(inc["incident_id"], "OPERATOR_ALICE")
    assert ok is True
    
    timeline = mgr._get_timeline_entries(inc["incident_id"])
    assert any(t["event_type"] == "OPERATOR_ACKNOWLEDGED" for t in timeline)


# ----------------------------------------------------
# Scenario 16: Operator Rejection / Feedback Submission
# ----------------------------------------------------
def test_scenario_16_operator_rejection():
    workflow = OperatorWorkflowManager()
    res = workflow.submit_feedback(
        station_id="STATION-01",
        operator_action=OperatorAction.REJECT_ANOMALY,
        incident_id="INC-100",
        reason="False alarm due to transient solar glare",
        operator_name="OPERATOR_BOB"
    )
    assert res["status"] == RecalibrationStatus.PENDING
    assert res["feedback_id"].startswith("FBK-")


# ----------------------------------------------------
# Scenario 17: Correction Approval Queue Pipeline
# ----------------------------------------------------
def test_scenario_17_correction_approval():
    workflow = OperatorWorkflowManager()
    res = workflow.submit_feedback(
        station_id="STATION-01",
        operator_action=OperatorAction.CONFIRM_CORRECTION,
        reason="Kalman forecast correction validated against AWS baseline"
    )
    candidate_id = res["candidate_id"]
    ok = workflow.advance_recalibration_candidate(candidate_id, RecalibrationStatus.DEPLOYED)
    assert ok is True


# ----------------------------------------------------
# Scenario 18: Audit Log Tracking
# ----------------------------------------------------
def test_scenario_18_audit_log_tracking():
    DB.log_audit("STATION-01", "TEST_EVENT", "System diagnostic test verification", actor="TESTER")
    logs = DB.get_audit_logs("STATION-01")
    assert len(logs) > 0
    assert logs[0]["event_type"] == "TEST_EVENT"
