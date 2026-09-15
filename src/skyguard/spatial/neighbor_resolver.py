"""
SkyGuard AI — Robust Mesonet Peer Consensus & Spatial Neighbor Resolver
Computes Haversine distances across India's AWS stations and evaluates peer spatial consensus:
- Quality-aware & health-aware peer candidate selection
- Bounded distance-weighting with zero-distance safeguards
- Robust weighted-median consensus & MAD (Median Absolute Deviation) scale estimation
- Temporal change agreement (station_delta vs peer_consensus_delta)
- Multi-state spatial classification (CONSISTENT_WITH_PEERS, LOCALIZED_SENSOR_FAULT,
  REGIONAL_WEATHER_EVENT, UNCERTAIN_SPATIAL_EVIDENCE, NO_VALID_PEERS)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from skyguard.config.contracts import SpatialConsensusOutput
from skyguard.config.settings import SETTINGS


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(r * c)


def compute_weighted_median(values: List[float], weights: List[float]) -> float:
    """Computes robust weighted median of values given non-negative weights."""
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])

    val_arr = np.array(values, dtype=float)
    w_arr = np.array(weights, dtype=float)

    if np.sum(w_arr) <= 0:
        return float(np.median(val_arr))

    sort_idx = np.argsort(val_arr)
    sorted_vals = val_arr[sort_idx]
    sorted_weights = w_arr[sort_idx]

    cumsum = np.cumsum(sorted_weights)
    cutoff = np.sum(sorted_weights) / 2.0

    idx = np.searchsorted(cumsum, cutoff)
    if idx >= len(sorted_vals):
        idx = len(sorted_vals) - 1
    return float(sorted_vals[idx])


class SpatialNeighborResolver:
    """Resolves nearest neighbor AWS stations and evaluates robust spatial consistency metrics."""

    def __init__(
        self,
        metadata_csv_path: Optional[Union[str, Path]] = None,
        search_radius_km: float = 350.0,
        min_neighbors: int = 2,
        max_neighbors: int = 5,
    ):
        self.search_radius_km = search_radius_km
        self.min_neighbors = min_neighbors
        self.max_neighbors = max_neighbors
        self.stations_df: Optional[pd.DataFrame] = None
        self._neighbor_cache: Dict[Tuple[str, Optional[float]], List[Dict[str, Any]]] = {}
        self._prev_readings: Dict[str, Dict[str, float]] = {}

        if metadata_csv_path:
            self.load_metadata(metadata_csv_path)

    def load_metadata(self, csv_path: Union[str, Path]):
        """Loads Indian AWS station coordinates and elevations."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"AWS metadata file not found at {csv_path}")

        df = pd.read_csv(csv_path)
        df.columns = [c.upper().strip() for c in df.columns]
        df["STATION_ID"] = df["STATION_ID"].astype(str).str.split('.').str[0]
        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
        df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).reset_index(drop=True)
        self.stations_df = df
        self._neighbor_cache.clear()

    def find_nearest_neighbors(
        self, station_id: str, max_radius_km: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Finds closest stations within search radius with instant caching."""
        sid_str = str(station_id).split('.')[0]
        cache_key = (sid_str, max_radius_km)
        if cache_key in self._neighbor_cache:
            return self._neighbor_cache[cache_key]

        if self.stations_df is None or len(self.stations_df) == 0:
            return []

        radius = max_radius_km or self.search_radius_km
        target_rows = self.stations_df[self.stations_df["STATION_ID"] == sid_str]

        if not target_rows.empty:
            t_lat = float(target_rows.iloc[0]["LATITUDE"])
            t_lon = float(target_rows.iloc[0]["LONGITUDE"])
        else:
            t_lat = float(self.stations_df.iloc[0]["LATITUDE"])
            t_lon = float(self.stations_df.iloc[0]["LONGITUDE"])

        neighbors = []
        for _, row in self.stations_df.iterrows():
            s_id = str(row["STATION_ID"])
            if s_id == sid_str:
                continue
            dist = haversine_distance(t_lat, t_lon, row["LATITUDE"], row["LONGITUDE"])
            if dist <= radius:
                neighbors.append({
                    "station_id": s_id,
                    "station_name": str(row.get("STATION_NAME", s_id)),
                    "latitude": float(row["LATITUDE"]),
                    "longitude": float(row["LONGITUDE"]),
                    "distance_km": float(dist),
                    "elevation_m": float(row["ELEVATION_M"]) if pd.notna(row.get("ELEVATION_M")) else None,
                })

        neighbors.sort(key=lambda x: x["distance_km"])
        res = neighbors[: self.max_neighbors]
        self._neighbor_cache[cache_key] = res
        return res

    def evaluate_consensus(
        self,
        target_station_id: str,
        target_temp: Optional[float],
        target_pres: Optional[float],
        target_humi: Optional[float],
        neighbor_telemetry: Optional[Dict[str, Dict[str, Any]]] = None,
        prev_target_temp: Optional[float] = None,
    ) -> SpatialConsensusOutput:
        """
        Evaluates spatial consistency using quality-filtered, health-weighted,
        distance-bounded robust consensus (weighted median + MAD + temporal change agreement).
        """
        neighbors = self.find_nearest_neighbors(target_station_id)
        n_count = len(neighbors)
        n_ids = [n["station_id"] for n in neighbors]
        distances = [n["distance_km"] for n in neighbors]

        if n_count == 0 or not neighbor_telemetry:
            return SpatialConsensusOutput(
                neighbor_count=0,
                neighbor_ids=[],
                distances_km=[],
                median_temp=None,
                median_pres=None,
                median_humi=None,
                target_deviation_temp=0.0,
                spatial_consensus_score=1.0,
                is_spatially_inconsistent=False,
                valid_peer_count=0,
                healthy_peer_count=0,
                effective_peer_count=0.0,
                spatial_confidence=0.0,
                spatial_status="NO_VALID_PEERS",
                evidence={"reason": "No spatial peers found within search radius."}
            )

        valid_peers = []
        for n in neighbors:
            nid = n["station_id"]
            if nid not in neighbor_telemetry:
                continue

            tel = neighbor_telemetry[nid]
            q_state = str(tel.get("quality_state", "GOOD")).upper()
            h_status = str(tel.get("health_status", tel.get("status", "HEALTHY"))).upper()

            if q_state in ["BAD", "MISSING"] or h_status in ["FAILED", "CRITICAL"]:
                continue

            health_weight = 1.0
            if h_status in ["WATCH", "WARNING"]:
                health_weight = 0.8
            elif h_status in ["SUSPECT", "WEATHER"]:
                health_weight = 0.5
            elif h_status == "DEGRADED":
                health_weight = 0.1

            dist_km = n["distance_km"]
            epsilon = 5.0
            dist_weight = 1.0 / (dist_km + epsilon)

            combined_weight = health_weight * dist_weight

            valid_peers.append({
                "station_id": nid,
                "distance_km": dist_km,
                "temperature": tel.get("temperature"),
                "pressure": tel.get("pressure"),
                "humidity": tel.get("humidity"),
                "prev_temp": tel.get("prev_temperature"),
                "health_status": h_status,
                "weight": combined_weight,
                "is_healthy": h_status in ["HEALTHY", "NORMAL"]
            })

        v_count = len(valid_peers)
        healthy_count = sum(1 for p in valid_peers if p["is_healthy"])

        if v_count == 0 or target_temp is None:
            return SpatialConsensusOutput(
                neighbor_count=n_count,
                neighbor_ids=n_ids,
                distances_km=distances,
                median_temp=None,
                median_pres=None,
                median_humi=None,
                target_deviation_temp=0.0,
                spatial_consensus_score=1.0,
                is_spatially_inconsistent=False,
                valid_peer_count=0,
                healthy_peer_count=0,
                effective_peer_count=0.0,
                spatial_confidence=0.0,
                spatial_status="NO_VALID_PEERS" if v_count == 0 else "CONSISTENT_WITH_PEERS",
                evidence={"reason": "No valid healthy peer telemetry available."}
            )

        # 1. Temperature Robust Weighted Consensus & MAD
        temp_peers = [p for p in valid_peers if p["temperature"] is not None and pd.notna(p["temperature"])]
        t_vals = [p["temperature"] for p in temp_peers]
        t_weights = [p["weight"] for p in temp_peers]

        if not t_vals:
            med_t = None
            mad_t = 1.0
            dev_t = 0.0
            z_dev_t = 0.0
        else:
            med_t = compute_weighted_median(t_vals, t_weights)
            abs_diffs = [abs(v - med_t) for v in t_vals]
            mad_t = compute_weighted_median(abs_diffs, t_weights) if len(abs_diffs) > 1 else 1.0
            mad_t = max(1.0, mad_t)
            dev_t = abs(target_temp - med_t)
            z_dev_t = dev_t / (1.4826 * mad_t)

        # 2. Pressure Robust Consensus & MAD
        pres_peers = [p for p in valid_peers if p["pressure"] is not None and pd.notna(p["pressure"])]
        p_vals = [p["pressure"] for p in pres_peers]
        p_weights = [p["weight"] for p in pres_peers]
        med_p = compute_weighted_median(p_vals, p_weights) if p_vals else None
        dev_p = abs(target_pres - med_p) if (target_pres is not None and med_p is not None) else 0.0
        mad_p = compute_weighted_median([abs(v - med_p) for v in p_vals], p_weights) if len(p_vals) > 1 else 1.0
        mad_p = max(0.8, mad_p)
        z_dev_p = dev_p / (1.4826 * mad_p) if med_p is not None else 0.0

        # 3. Humidity Robust Consensus & MAD
        humi_peers = [p for p in valid_peers if p["humidity"] is not None and pd.notna(p["humidity"])]
        h_vals = [p["humidity"] for p in humi_peers]
        h_weights = [p["weight"] for p in humi_peers]
        med_h = compute_weighted_median(h_vals, h_weights) if h_vals else None
        dev_h = abs(target_humi - med_h) if (target_humi is not None and med_h is not None) else 0.0
        mad_h = compute_weighted_median([abs(v - med_h) for v in h_vals], h_weights) if len(h_vals) > 1 else 4.0
        mad_h = max(2.5, mad_h)
        z_dev_h = dev_h / (1.4826 * mad_h) if med_h is not None else 0.0

        # 4. Temporal Change Agreement
        station_delta = 0.0
        peer_consensus_delta = 0.0
        change_residual = 0.0

        if prev_target_temp is not None and target_temp is not None:
            station_delta = target_temp - prev_target_temp

            peer_deltas = []
            peer_delta_weights = []
            for p in temp_peers:
                if p.get("prev_temp") is not None and pd.notna(p["prev_temp"]):
                    peer_deltas.append(p["temperature"] - p["prev_temp"])
                    peer_delta_weights.append(p["weight"])

            if peer_deltas:
                peer_consensus_delta = compute_weighted_median(peer_deltas, peer_delta_weights)
                change_residual = station_delta - peer_consensus_delta

        if target_temp is not None:
            self._prev_readings[target_station_id] = {"temperature": target_temp}

        # 5. Spatial Confidence
        peer_count_confidence = min(1.0, len(temp_peers) / 3.0)
        dispersion_penalty = max(0.0, (mad_t - 2.5) / 5.0)
        spatial_confidence = max(0.1, round(peer_count_confidence * (1.0 - dispersion_penalty), 2))

        # 6. Spatial Consensus Score
        max_z = max(z_dev_t, z_dev_p, z_dev_h)
        consensus_score = float(np.exp(-0.5 * (max_z / 2.0) ** 2))

        # 7. Spatial Status Classification
        if len(temp_peers) < 2 or (len(t_vals) > 2 and mad_t > 5.0):
            spatial_status = "UNCERTAIN_SPATIAL_EVIDENCE"
            is_inconsistent = False
        elif abs(change_residual) < 3.0 and abs(station_delta) >= 3.0:
            spatial_status = "REGIONAL_WEATHER_EVENT"
            is_inconsistent = False
        elif dev_t >= 6.5 and z_dev_t > 3.5:
            spatial_status = "LOCALIZED_SENSOR_FAULT"
            is_inconsistent = True
        elif dev_t <= 2.5 and mad_t <= 3.5:
            spatial_status = "CONSISTENT_WITH_PEERS"
            is_inconsistent = False
        elif consensus_score < 0.45:
            spatial_status = "UNCERTAIN_SPATIAL_EVIDENCE"
            is_inconsistent = bool(dev_t >= 6.5 and z_dev_t > 3.5)
        else:
            spatial_status = "CONSISTENT_WITH_PEERS"
            is_inconsistent = False


        evidence = {
            "valid_peer_count": len(temp_peers),
            "healthy_peer_count": healthy_count,
            "peer_consensus_temp": med_t,
            "peer_mad_temp": mad_t,
            "absolute_residual": float(dev_t),
            "change_residual": float(change_residual),
            "station_delta": float(station_delta),
            "peer_consensus_delta": float(peer_consensus_delta),
            "spatial_confidence": spatial_confidence,
            "spatial_status": spatial_status
        }

        return SpatialConsensusOutput(
            neighbor_count=len(temp_peers),
            neighbor_ids=n_ids,
            distances_km=distances,
            median_temp=med_t,
            median_pres=med_p,
            median_humi=med_h,
            target_deviation_temp=float(dev_t),
            target_deviation_pres=float(dev_p),
            target_deviation_humi=float(dev_h),
            spatial_consensus_score=round(consensus_score, 4),
            is_spatially_inconsistent=is_inconsistent,
            valid_peer_count=len(temp_peers),
            healthy_peer_count=healthy_count,
            effective_peer_count=round(sum(p["weight"] for p in temp_peers), 2),
            peer_mad_temp=float(mad_t),
            peer_mad_pres=float(mad_p),
            peer_mad_humi=float(mad_h),
            temp_absolute_residual=float(dev_t),
            temp_change_residual=float(change_residual),
            spatial_confidence=spatial_confidence,
            spatial_status=spatial_status,
            evidence=evidence
        )
