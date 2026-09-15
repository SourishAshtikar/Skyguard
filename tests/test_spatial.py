"""
SkyGuard AI — Test Suite for Robust Mesonet Peer Consensus & Spatial Resolver
Validates:
- Haversine distance calculations & edge cases (zero distance, identical coordinates)
- Nearest neighbor lookup with caching
- Quality-aware & health-aware peer candidate set filtering
- Robust weighted median consensus (outlier resistance against 1 bad peer)
- Spatial dispersion scale & zero MAD safeguards
- Temporal change agreement (station_delta vs peer_consensus_delta)
- Multi-state spatial classification (CONSISTENT_WITH_PEERS, LOCALIZED_SENSOR_FAULT,
  REGIONAL_WEATHER_EVENT, UNCERTAIN_SPATIAL_EVIDENCE, NO_VALID_PEERS)
"""

from pathlib import Path
import pytest
import pandas as pd
from skyguard.spatial.neighbor_resolver import (
    SpatialNeighborResolver,
    haversine_distance,
    compute_weighted_median,
)


@pytest.fixture
def sample_station_id():
    meta_path = Path("Datasets/indian_aws_locations.csv")
    if meta_path.exists():
        df = pd.read_csv(meta_path)
        return str(df.iloc[0]["STATION_ID"])
    return "43025099999"


def test_haversine_known_distances():
    # Delhi (28.61, 77.20) to Mumbai (19.07, 72.87) is approx 1150 km
    d = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1100.0 < d < 1200.0

    # Zero distance for identical points
    assert haversine_distance(28.0, 77.0, 28.0, 77.0) == 0.0


def test_weighted_median():
    # Ordinary median case
    vals = [10.0, 20.0, 30.0]
    weights = [1.0, 1.0, 1.0]
    assert compute_weighted_median(vals, weights) == 20.0

    # Outlier resistance test: 4 healthy peers around 32°C, 1 corrupted peer at 60°C
    vals_outlier = [31.8, 32.0, 32.1, 32.2, 60.0]
    weights_outlier = [1.0, 1.0, 1.0, 1.0, 1.0]
    med = compute_weighted_median(vals_outlier, weights_outlier)
    assert 31.5 <= med <= 32.5  # Consensus resists the 60°C outlier peer


def test_basic_agreeing_peers(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)

    neighbors = resolver.find_nearest_neighbors(sample_station_id)
    assert len(neighbors) > 0

    peer_telemetry = {
        n["station_id"]: {
            "temperature": 32.0,
            "pressure": 1005.0,
            "humidity": 60.0,
            "health_status": "HEALTHY",
            "quality_state": "GOOD"
        }
        for n in neighbors
    }

    res = resolver.evaluate_consensus(sample_station_id, 32.2, 1005.1, 59.5, peer_telemetry)
    assert res.spatial_status == "CONSISTENT_WITH_PEERS"
    assert res.spatial_consensus_score > 0.8
    assert not res.is_spatially_inconsistent


def test_one_bad_peer_outlier_immunity(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)
    neighbors = resolver.find_nearest_neighbors(sample_station_id)

    # 4 peers read 32°C, 1 peer reads 65°C
    peer_telemetry = {}
    for idx, n in enumerate(neighbors):
        val = 65.0 if idx == 0 else 32.0
        peer_telemetry[n["station_id"]] = {
            "temperature": val,
            "pressure": 1005.0,
            "humidity": 60.0,
            "health_status": "HEALTHY",
            "quality_state": "GOOD"
        }

    res = resolver.evaluate_consensus(sample_station_id, 32.1, 1005.0, 60.0, peer_telemetry)
    assert 31.5 <= res.median_temp <= 32.5
    assert res.spatial_status == "CONSISTENT_WITH_PEERS"


def test_regional_weather_event(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)
    neighbors = resolver.find_nearest_neighbors(sample_station_id)

    # All stations experience a simultaneous +5°C temperature shift
    peer_telemetry = {
        n["station_id"]: {
            "temperature": 35.0,
            "prev_temperature": 30.0,
            "pressure": 1000.0,
            "humidity": 85.0,
            "health_status": "HEALTHY"
        }
        for n in neighbors
    }

    res = resolver.evaluate_consensus(sample_station_id, 35.0, 1000.0, 85.0, peer_telemetry, prev_target_temp=30.0)
    assert res.spatial_status == "REGIONAL_WEATHER_EVENT"
    assert not res.is_spatially_inconsistent


def test_localized_sensor_fault(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)
    neighbors = resolver.find_nearest_neighbors(sample_station_id)

    peer_telemetry = {
        n["station_id"]: {
            "temperature": 30.0,
            "prev_temperature": 30.0,
            "pressure": 1010.0,
            "humidity": 60.0,
            "health_status": "HEALTHY"
        }
        for n in neighbors
    }

    res = resolver.evaluate_consensus(sample_station_id, 48.0, 1010.0, 60.0, peer_telemetry, prev_target_temp=30.0)
    assert res.spatial_status == "LOCALIZED_SENSOR_FAULT"
    assert res.is_spatially_inconsistent


def test_peer_disagreement_uncertain_evidence(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)
    neighbors = resolver.find_nearest_neighbors(sample_station_id)

    peer_telemetry = {}
    for idx, n in enumerate(neighbors):
        peer_telemetry[n["station_id"]] = {
            "temperature": 20.0 + (idx * 12.0),
            "health_status": "HEALTHY"
        }

    res = resolver.evaluate_consensus(sample_station_id, 30.0, 1000.0, 60.0, peer_telemetry)
    assert res.spatial_status == "UNCERTAIN_SPATIAL_EVIDENCE"


def test_no_valid_peers_fallback(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)

    res = resolver.evaluate_consensus(sample_station_id, 30.0, 1000.0, 60.0, {})
    assert res.spatial_status == "NO_VALID_PEERS"
    assert res.spatial_confidence == 0.0
    assert not res.is_spatially_inconsistent


def test_unhealthy_peer_exclusion(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)
    neighbors = resolver.find_nearest_neighbors(sample_station_id)

    peer_telemetry = {}
    for idx, n in enumerate(neighbors):
        if idx == 0:
            peer_telemetry[n["station_id"]] = {
                "temperature": 75.0,
                "health_status": "FAILED",
                "quality_state": "BAD"
            }
        else:
            peer_telemetry[n["station_id"]] = {
                "temperature": 30.0,
                "health_status": "HEALTHY",
                "quality_state": "GOOD"
            }

    res = resolver.evaluate_consensus(sample_station_id, 30.0, 1000.0, 60.0, peer_telemetry)
    assert res.valid_peer_count == len(neighbors) - 1
    assert res.median_temp == 30.0


def test_zero_mad_safeguard(sample_station_id):
    meta_path = Path("Datasets/indian_aws_locations.csv")
    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=350.0)
    neighbors = resolver.find_nearest_neighbors(sample_station_id)

    peer_telemetry = {
        n["station_id"]: {"temperature": 30.0, "health_status": "HEALTHY"}
        for n in neighbors
    }

    res = resolver.evaluate_consensus(sample_station_id, 30.5, 1000.0, 60.0, peer_telemetry)
    assert res.peer_mad_temp >= 1.0
    assert res.spatial_status == "CONSISTENT_WITH_PEERS"
