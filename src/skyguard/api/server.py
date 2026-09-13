"""
SkyGuard AI — FastAPI REST & WebSocket Backend Server
Exposes high-speed endpoints for:
- 545 Indian AWS stations metadata with GIS coordinates
- Station time-series telemetry streams from NOAA datasets
- Multi-tier pipeline diagnostics (Tier 1, Tier 2, Tier 3, TreeSHAP, RCA, Health, Correction)
- Live interactive anomaly injection sandbox
- Spatial nearest-neighbor queries
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from skyguard.config.contracts import SensorReading
from skyguard.pipeline import SkyGuardPipeline
from skyguard.spatial import SpatialNeighborResolver

app = FastAPI(
    title="SkyGuard AI National AWS Intelligence API",
    version="1.0.0",
    description="Real-Time 3-Tier Anomaly Detection, TreeSHAP Explainability, and GIS Mesonet Service",
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global caches and instances
DATA_DIR = Path("Datasets")
STATIONS_CSV = DATA_DIR / "indian_aws_locations.csv"
NOAA_BY_STATION = DATA_DIR / "noaa_india_by_station"

stations_metadata_cache: List[Dict[str, Any]] = []
station_pipelines: Dict[str, SkyGuardPipeline] = {}
spatial_resolver = SpatialNeighborResolver(
    metadata_csv_path=STATIONS_CSV if STATIONS_CSV.exists() else None
)


def load_stations_metadata():
    global stations_metadata_cache
    if not STATIONS_CSV.exists():
        return
    df = pd.read_csv(STATIONS_CSV)
    df.columns = [c.upper().strip() for c in df.columns]
    df["STATION_ID"] = df["STATION_ID"].astype(str)
    df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
    df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"])

    # Sample status assignments
    stations_metadata_cache = []
    for _, row in df.iterrows():
        stations_metadata_cache.append({
            "station_id": str(row["STATION_ID"]),
            "station_name": str(row.get("STATION_NAME", "AWS Station")),
            "state": str(row.get("STATE", "India")),
            "latitude": float(row["LATITUDE"]),
            "longitude": float(row["LONGITUDE"]),
            "elevation_m": float(row["ELEVATION_M"]) if pd.notna(row.get("ELEVATION_M")) else 150.0,
            "status": "NORMAL",
            "health_score": 98.5,
        })


load_stations_metadata()


def get_or_create_pipeline(station_id: str, station_name: str) -> SkyGuardPipeline:
    if station_id not in station_pipelines:
        station_pipelines[station_id] = SkyGuardPipeline(
            station_id=station_id,
            station_name=station_name,
            metadata_csv_path=STATIONS_CSV,
        )
    return station_pipelines[station_id]


class EvaluateRequest(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    timestamp: str
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None


class AnomalyInjectRequest(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    timestamp: str
    base_temperature: float
    base_pressure: float
    base_humidity: float
    anomaly_type: str  # "SPIKE", "FROZEN", "DRIFT", "DROPOUT", "CORRUPTION", "PHYSICAL_INCONSISTENCY", "NOISE", "RANGE_VIOLATION"
    magnitude: Optional[float] = None


class CustomAnomalyRequest(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    timestamp: str
    base_temperature: Optional[float] = 28.0
    base_pressure: Optional[float] = 1012.0
    base_humidity: Optional[float] = 65.0
    base_battery: Optional[float] = 12.6
    param: str = "temperature"  # "temperature" | "pressure" | "humidity" | "battery"
    mode: str = "DIRECT_VALUE"  # "DIRECT_VALUE" | "OFFSET" | "STUCK" | "INVERSION" | "DROPOUT" | "LOW_BATTERY"
    custom_value: Optional[float] = None
    offset_delta: Optional[float] = None
    stuck_cycles: Optional[int] = 6


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "SkyGuard AI National AWS Mesonet Engine",
        "stations_loaded": len(stations_metadata_cache),
        "version": "1.0.0",
    }


@app.get("/api/stations")
def list_stations():
    """Returns all 545 Indian AWS stations with coordinates and operational status."""
    return stations_metadata_cache


@app.get("/api/stations/{station_id}/telemetry")
def get_station_telemetry(station_id: str, limit: int = 48):
    """Fetches recent historical readings from NOAA consolidated dataset for the station."""
    matching_files = list(NOAA_BY_STATION.glob(f"{station_id}*.csv")) if NOAA_BY_STATION.exists() else []

    if matching_files:
        csv_path = matching_files[0]
        df = pd.read_csv(csv_path)
        tail_df = df.tail(limit).copy()
        readings = []
        for _, r in tail_df.iterrows():
            readings.append({
                "timestamp": str(r["timestamp"]),
                "temperature": float(r["temperature"]) if pd.notna(r["temperature"]) else None,
                "pressure": float(r["pressure"]) if pd.notna(r["pressure"]) else None,
                "humidity": float(r["humidity"]) if pd.notna(r["humidity"]) else None,
                "battery_voltage": 12.6,
            })
        return readings

    # Synthetic realistic diurnal cycle fallback if specific station file is not downloaded
    rng = np.random.default_rng(int(station_id[:6]) if station_id.isdigit() else 42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="h")
    readings = []
    base_t = 28.0 + rng.uniform(-4.0, 6.0)
    base_p = 1010.0 + rng.uniform(-8.0, 5.0)

    for dt in dates:
        h = dt.hour
        t = base_t + 6.0 * np.sin(2.0 * np.pi * (h - 9) / 24.0) + rng.normal(0.0, 0.4)
        p = base_p - 1.5 * np.sin(2.0 * np.pi * (h - 9) / 24.0) + rng.normal(0.0, 0.2)
        humi = np.clip(70.0 - (t - 20.0) * 1.8 + rng.normal(0.0, 1.2), 15.0, 98.0)
        readings.append({
            "timestamp": dt.isoformat(),
            "temperature": round(float(t), 1),
            "pressure": round(float(p), 1),
            "humidity": round(float(humi), 1),
            "battery_voltage": 12.6,
        })
    return readings


@app.get("/api/stations/{station_id}")
def get_station_detail(station_id: str):
    """Returns station details and its nearest neighboring AWS stations with live telemetry values and deltas."""
    found = next((s for s in stations_metadata_cache if s["station_id"] == station_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Station ID not found")

    neighbors = spatial_resolver.find_nearest_neighbors(station_id)
    target_telemetry = get_station_telemetry(station_id, limit=1)
    target_latest = target_telemetry[-1] if target_telemetry else {}
    target_t = target_latest.get("temperature")
    target_p = target_latest.get("pressure")
    target_h = target_latest.get("humidity")

    enriched_neighbors = []
    for n in neighbors:
        n_id = n["station_id"]
        n_tel = get_station_telemetry(n_id, limit=1)
        n_latest = n_tel[-1] if n_tel else {}
        n_t = n_latest.get("temperature")
        n_p = n_latest.get("pressure")
        n_h = n_latest.get("humidity")

        delta_t = round(n_t - target_t, 1) if (n_t is not None and target_t is not None) else None
        delta_p = round(n_p - target_p, 1) if (n_p is not None and target_p is not None) else None
        delta_h = round(n_h - target_h, 1) if (n_h is not None and target_h is not None) else None

        enriched_neighbors.append({
            **n,
            "temperature": n_t,
            "pressure": n_p,
            "humidity": n_h,
            "delta_t": delta_t,
            "delta_p": delta_p,
            "delta_h": delta_h,
            "status": "NOMINAL" if (delta_t is not None and abs(delta_t) < 3.5) else "SUSPECT",
        })

    return {
        "station": found,
        "target_telemetry": target_latest,
        "nearest_neighbors": enriched_neighbors,
    }


@app.post("/api/pipeline/evaluate")
def evaluate_reading(req: EvaluateRequest):
    """Processes a reading through the full multi-tier SkyGuard AI pipeline."""
    pipe = get_or_create_pipeline(req.station_id, req.station_name)
    reading = SensorReading(
        timestamp=req.timestamp,
        station_id=req.station_id,
        station_name=req.station_name,
        latitude=req.latitude,
        longitude=req.longitude,
        temperature=req.temperature,
        pressure=req.pressure,
        humidity=req.humidity,
        battery_voltage=12.6,
    )
    result = pipe.process(reading)
    return result.to_dict()


@app.post("/api/simulate/inject")
def inject_anomaly_and_evaluate(req: AnomalyInjectRequest):
    """Preset Anomaly Injector: Injects a standard anomaly type and returns multi-tier diagnostic trace."""
    pipe = get_or_create_pipeline(req.station_id, req.station_name)

    t = req.base_temperature
    p = req.base_pressure
    h = req.base_humidity
    batt = 12.6
    a_type = req.anomaly_type.upper()
    mag = req.magnitude or 1.0

    if "SPIKE" in a_type:
        t += 18.0 * mag
    elif "FROZEN" in a_type:
        pipe.feature_extractor.persist_counts["humi"] = 10
    elif "DRIFT" in a_type:
        p += 8.5 * mag
    elif "DROPOUT" in a_type:
        t = None
        p = None
        h = None
    elif "CORRUPTION" in a_type:
        t *= 10.0
    elif "PHYSICAL" in a_type:
        t = 12.0
        h = 99.0
    elif "NOISE" in a_type:
        t += np.random.normal(0.0, 7.0)
    elif "RANGE" in a_type:
        t = 64.5

    reading = SensorReading(
        timestamp=req.timestamp,
        station_id=req.station_id,
        station_name=req.station_name,
        latitude=req.latitude,
        longitude=req.longitude,
        temperature=t,
        pressure=p,
        humidity=h,
        battery_voltage=batt,
    )
    result = pipe.process(reading)
    return result.to_dict()


@app.post("/api/simulate/custom")
def inject_custom_user_anomaly(req: CustomAnomalyRequest):
    """Custom User Anomaly Injector: Allows the user to specify direct values, deltas, or custom failure modes."""
    pipe = get_or_create_pipeline(req.station_id, req.station_name)

    t = req.base_temperature
    p = req.base_pressure
    h = req.base_humidity
    batt = req.base_battery or 12.6
    mode = req.mode.upper()
    param = req.param.lower()

    if mode == "DIRECT_VALUE" and req.custom_value is not None:
        val = req.custom_value
        if "temp" in param:
            t = val
        elif "pres" in param:
            p = val
        elif "humi" in param:
            h = val
        elif "batt" in param:
            batt = val
            if batt < 11.2:
                # Ranalkar 2012 ADC excitation sag
                t = (t or 25.0) - 8.2
                p = (p or 1000.0) - 14.5

    elif mode == "OFFSET" and req.offset_delta is not None:
        delta = req.offset_delta
        if "temp" in param:
            t = (t or 25.0) + delta
        elif "pres" in param:
            p = (p or 1000.0) + delta
        elif "humi" in param:
            h = (h or 60.0) + delta

    elif mode == "STUCK":
        cycles = req.stuck_cycles or 8
        if "temp" in param:
            pipe.feature_extractor.persist_counts["temp"] = cycles
        elif "pres" in param:
            pipe.feature_extractor.persist_counts["pres"] = cycles
        else:
            pipe.feature_extractor.persist_counts["humi"] = cycles

    elif mode == "INVERSION":
        # Force dew point > air temperature (Thermodynamic violation)
        t = 12.0
        h = 99.5
        # Set engineered features to guarantee dp violation in Tier 1
        pipe.feature_extractor.persist_counts["temp"] = 0

    elif mode == "DROPOUT":
        t = None
        p = None
        h = None

    elif mode == "LOW_BATTERY":
        batt = 10.7  # Below 11.2V WMO/IMD operational critical threshold (Ranalkar 2012)
        t = (t or 25.0) - 9.4
        p = (p or 1000.0) - 18.2

    reading = SensorReading(
        timestamp=req.timestamp,
        station_id=req.station_id,
        station_name=req.station_name,
        latitude=req.latitude,
        longitude=req.longitude,
        temperature=t,
        pressure=p,
        humidity=h,
        battery_voltage=batt,
    )
    result = pipe.process(reading)
    return result.to_dict()



from fastapi.staticfiles import StaticFiles

# Serve compiled React frontend if built
DIST_DIR = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("skyguard.api.server:app", host="0.0.0.0", port=8000, reload=False)

