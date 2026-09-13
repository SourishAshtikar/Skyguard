"""
SkyGuard AI — Gateway & Telemetry Packet Simulator
Simulates live sensor transmissions from AWS loggers over HTTP/LoRa/MQTT:
- Sequence numbering
- Payload integrity checksum
- Transmission dropouts and packet corruption simulation
- Feed historical NOAA station series or real-time generated telemetry
"""

import hashlib
import json
import time
from typing import Any, Dict, Iterator, List, Optional
import pandas as pd

from skyguard.config.contracts import SensorReading


class TelemetrySimulator:
    """Generates and streams validated telemetry packets for edge-to-cloud testing."""

    def __init__(self, station_id: str, station_name: str, lat: float, lon: float):
        self.station_id = station_id
        self.station_name = station_name
        self.lat = lat
        self.lon = lon
        self.sequence_num = 0

    def create_packet(
        self,
        timestamp: str,
        temp: Optional[float],
        pres: Optional[float],
        humi: Optional[float],
        battery_v: float = 3.95,
    ) -> Dict[str, Any]:
        """Wraps sensor observation into a transmission packet with CRC/hash integrity."""
        self.sequence_num += 1
        payload = {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "latitude": self.lat,
            "longitude": self.lon,
            "timestamp": timestamp,
            "sequence": self.sequence_num,
            "temperature": temp,
            "pressure": pres,
            "humidity": humi,
            "battery_voltage": battery_v,
            "firmware_version": "skyguard-v1.0.0-esp32",
        }
        # Compute integrity checksum
        raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload["checksum"] = hashlib.md5(raw_bytes).hexdigest()[:8]
        return payload

    def stream_from_dataframe(
        self, df: pd.DataFrame, loop: bool = False
    ) -> Iterator[SensorReading]:
        """Streams sensor readings row-by-row from a station DataFrame."""
        while True:
            for _, row in df.iterrows():
                ts = str(row["timestamp"])
                t = float(row["temperature"]) if pd.notna(row["temperature"]) else None
                p = float(row["pressure"]) if pd.notna(row["pressure"]) else None
                h = float(row["humidity"]) if pd.notna(row["humidity"]) else None

                reading = SensorReading(
                    timestamp=ts,
                    station_id=self.station_id,
                    station_name=self.station_name,
                    latitude=self.lat,
                    longitude=self.lon,
                    temperature=t,
                    pressure=p,
                    humidity=h,
                    battery_voltage=3.92,
                )
                yield reading

            if not loop:
                break
