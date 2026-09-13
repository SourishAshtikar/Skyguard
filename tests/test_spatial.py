"""
Tests for Spatial Consensus and Neighbor Resolver
Validates:
- Haversine distance accuracy between known coordinates
- Nearest neighbor lookup from indian_aws_locations.csv
- Spatial consensus calculation (MAD, deviation, score)
"""

from pathlib import Path
import pytest
from skyguard.spatial import SpatialNeighborResolver, haversine_distance


def test_haversine_known_distances():
    # Delhi (28.61, 77.20) to Mumbai (19.07, 72.87) is approx 1150 km
    d = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1100.0 < d < 1200.0

    # Zero distance for identical points
    assert haversine_distance(28.0, 77.0, 28.0, 77.0) == 0.0


def test_spatial_neighbor_resolver():
    meta_path = Path("Datasets/indian_aws_locations.csv")
    assert meta_path.exists()

    resolver = SpatialNeighborResolver(metadata_csv_path=meta_path, search_radius_km=250.0)
    # Safdarjung Delhi station: 42182099999
    neighbors = resolver.find_nearest_neighbors("42182099999")
    assert len(neighbors) > 0
    # Closest neighbors should be within 250 km
    assert neighbors[0]["distance_km"] < 250.0

    # Test consensus with agreeing peers
    peer_telemetry = {
        n["station_id"]: {"temperature": 32.5, "pressure": 1005.0, "humidity": 60.0}
        for n in neighbors
    }
    consensus_normal = resolver.evaluate_consensus("42182099999", 32.0, 1005.2, 59.0, peer_telemetry)
    assert consensus_normal.spatial_consensus_score > 0.8
    assert not consensus_normal.is_spatially_inconsistent

    # Test consensus with strong spatial anomaly (target reads 46°C while neighbors read 32°C)
    consensus_anomaly = resolver.evaluate_consensus("42182099999", 46.0, 1005.2, 59.0, peer_telemetry)
    assert consensus_anomaly.spatial_consensus_score < 0.5
    assert consensus_anomaly.is_spatially_inconsistent
