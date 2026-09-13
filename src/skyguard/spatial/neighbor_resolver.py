"""
SkyGuard AI — Spatial Neighbor Resolver
Computes Haversine distances across India's 545 AWS stations and performs spatial consensus checks:
- Multi-station nearest neighbor lookup
- Cluster median and MAD (Median Absolute Deviation)
- Target deviation scoring
- Isolated station graceful fallback
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from skyguard.config.contracts import SpatialConsensusOutput


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(r * c)


class SpatialNeighborResolver:
    """Resolves nearest neighbor AWS stations and computes spatial consistency metrics."""

    def __init__(
        self,
        metadata_csv_path: Optional[Union[str, Path]] = None,
        search_radius_km: float = 150.0,
        min_neighbors: int = 2,
        max_neighbors: int = 5,
    ):
        self.search_radius_km = search_radius_km
        self.min_neighbors = min_neighbors
        self.max_neighbors = max_neighbors
        self.stations_df: Optional[pd.DataFrame] = None
        self._neighbor_cache: Dict[Tuple[str, Optional[float]], List[Dict[str, Any]]] = {}

        if metadata_csv_path:
            self.load_metadata(metadata_csv_path)

    def load_metadata(self, csv_path: Union[str, Path]):
        """Loads Indian AWS station coordinates and elevations."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"AWS metadata file not found at {csv_path}")

        df = pd.read_csv(csv_path)
        # Normalize column names
        df.columns = [c.upper().strip() for c in df.columns]
        # Required columns: STATION_ID, LATITUDE, LONGITUDE
        df["STATION_ID"] = df["STATION_ID"].astype(str)
        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
        df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).reset_index(drop=True)
        self.stations_df = df
        self._neighbor_cache.clear()

    def find_nearest_neighbors(
        self, station_id: str, max_radius_km: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Finds closest stations within search radius with instant caching."""
        cache_key = (str(station_id), max_radius_km)
        if cache_key in self._neighbor_cache:
            return self._neighbor_cache[cache_key]

        if self.stations_df is None or len(self.stations_df) == 0:
            return []

        radius = max_radius_km or self.search_radius_km
        target_rows = self.stations_df[self.stations_df["STATION_ID"] == str(station_id)]
        if target_rows.empty:
            return []

        t_lat = float(target_rows.iloc[0]["LATITUDE"])
        t_lon = float(target_rows.iloc[0]["LONGITUDE"])

        neighbors = []
        for _, row in self.stations_df.iterrows():
            s_id = str(row["STATION_ID"])
            if s_id == str(station_id):
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
        neighbor_telemetry: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> SpatialConsensusOutput:
        """Evaluates whether target station reading agrees with neighboring mesonet stations."""
        neighbors = self.find_nearest_neighbors(target_station_id)
        n_count = len(neighbors)
        n_ids = [n["station_id"] for n in neighbors]
        distances = [n["distance_km"] for n in neighbors]

        # If isolated station or no neighbor telemetry available
        if n_count < self.min_neighbors or not neighbor_telemetry:
            return SpatialConsensusOutput(
                neighbor_count=n_count,
                neighbor_ids=n_ids,
                distances_km=distances,
                median_temp=None,
                median_pres=None,
                median_humi=None,
                target_deviation_temp=0.0,
                spatial_consensus_score=1.0,  # Neutral pass when no spatial peers
                is_spatially_inconsistent=False,
            )

        # Collect available neighbor readings
        n_temps = []
        n_pres = []
        n_humis = []

        for nid in n_ids:
            if nid in neighbor_telemetry:
                t_dat = neighbor_telemetry[nid]
                if "temperature" in t_dat and pd.notna(t_dat["temperature"]):
                    n_temps.append(float(t_dat["temperature"]))
                if "pressure" in t_dat and pd.notna(t_dat["pressure"]):
                    n_pres.append(float(t_dat["pressure"]))
                if "humidity" in t_dat and pd.notna(t_dat["humidity"]):
                    n_humis.append(float(t_dat["humidity"]))

        if len(n_temps) < self.min_neighbors or target_temp is None:
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
            )

        med_t = float(np.median(n_temps))
        med_p = float(np.median(n_pres)) if n_pres else None
        med_h = float(np.median(n_humis)) if n_humis else None

        # 1. Temperature Median Absolute Deviation (MAD)
        mad_t = float(np.median(np.abs(np.array(n_temps) - med_t)))
        mad_t = max(1.0, mad_t)  # Minimum 1.0°C expected ambient dispersion
        dev_t = abs(target_temp - med_t) if target_temp is not None else 0.0
        z_dev_t = dev_t / (1.4826 * mad_t)

        # 2. Pressure Median Absolute Deviation (MAD)
        dev_p = 0.0
        z_dev_p = 0.0
        if target_pres is not None and med_p is not None:
            dev_p = abs(target_pres - med_p)
            mad_p = float(np.median(np.abs(np.array(n_pres) - med_p))) if len(n_pres) > 1 else 1.0
            mad_p = max(0.8, mad_p)
            z_dev_p = dev_p / (1.4826 * mad_p)

        # 3. Humidity Median Absolute Deviation (MAD)
        dev_h = 0.0
        z_dev_h = 0.0
        if target_humi is not None and med_h is not None:
            dev_h = abs(target_humi - med_h)
            mad_h = float(np.median(np.abs(np.array(n_humis) - med_h))) if len(n_humis) > 1 else 4.0
            mad_h = max(2.5, mad_h)
            z_dev_h = dev_h / (1.4826 * mad_h)

        # Consensus score from 0.0 (extreme divergence) to 1.0 (perfect match)
        max_z = max(z_dev_t, z_dev_p, z_dev_h)
        consensus_score = float(np.exp(-0.5 * (max_z / 2.0) ** 2))

        # Flag inconsistency if:
        # - Temperature deviates > 8.0°C or z > 3.5
        # - Pressure deviates > 5.5 hPa or z > 3.5 (calibration drift / barometric leak)
        # - Humidity deviates > 30.0% or z > 3.5
        is_temp_inconsistent = bool(dev_t > 8.0 or z_dev_t > 3.5)
        is_pres_inconsistent = bool((dev_p > 5.5 or z_dev_p > 3.5) if (target_pres is not None and med_p is not None) else False)
        is_humi_inconsistent = bool((dev_h > 30.0 or z_dev_h > 3.5) if (target_humi is not None and med_h is not None) else False)

        is_inconsistent = bool(is_temp_inconsistent or is_pres_inconsistent or is_humi_inconsistent)

        return SpatialConsensusOutput(
            neighbor_count=len(n_temps),
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
        )
