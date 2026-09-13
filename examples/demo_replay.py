"""
SkyGuard AI — End-to-End Demonstration Replay Script
Replays historical NOAA ISD observations from an Indian AWS station (Safdarjung, New Delhi),
injects a sequence of synthetic anomalies, and streams them through the 3-tier SkyGuard pipeline.
"""

import sys
from pathlib import Path
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from skyguard.config.contracts import SensorReading
from skyguard.data import AnomalyInjector
from skyguard.pipeline import SkyGuardPipeline


def run_demo():
    print("===========================================================================")
    print("[*] SKYGUARD AI: NATIONAL AUTOMATIC WEATHER STATION INTELLIGENCE PIPELINE")
    print("===========================================================================")

    station_csv = Path("Datasets/noaa_india_by_station/42182099999_SAFDARJUNG.csv")
    if not station_csv.exists():
        print(f"Error: Station data file not found at {station_csv}")
        return

    print(f"Loading NOAA baseline observations from {station_csv.name}...")
    df = pd.read_csv(station_csv).tail(50).reset_index(drop=True)
    print(f"Loaded {len(df)} historical readings.\n")

    # Inject anomaly into reading #25: +18°C temperature spike
    injector = AnomalyInjector(random_seed=42)
    df_injected, meta = injector.inject_spike(df, sensor="temperature", start_idx=25, jump_val=18.0)
    print(f"Synthetically Injected: {meta.root_cause} at index {meta.start_idx}\n")

    # Initialize Master Pipeline for Safdarjung
    pipeline = SkyGuardPipeline(
        station_id="42182099999",
        station_name="SAFDARJUNG NEW DELHI",
    )

    print("Replaying telemetry stream through all 3 intelligence tiers:")
    print("-" * 75)
    print(f"{'STEP':<5} | {'TIMESTAMP':<19} | {'RAW TEMP':<9} | {'T1 STATUS':<10} | {'T2 SCORE':<9} | {'STAGE3 DIAGNOSIS':<22} | {'CORRECTED'}")
    print("-" * 75)

    for i, row in df_injected.iterrows():
        reading = SensorReading(
            timestamp=str(row["timestamp"]),
            station_id="42182099999",
            station_name="SAFDARJUNG NEW DELHI",
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            temperature=float(row["temperature"]) if pd.notna(row["temperature"]) else None,
            pressure=float(row["pressure"]) if pd.notna(row["pressure"]) else None,
            humidity=float(row["humidity"]) if pd.notna(row["humidity"]) else None,
        )

        result = pipeline.process(reading)

        t_raw = f"{reading.temperature:.1f}C" if reading.temperature is not None else "NULL"
        t1_stat = result.tier1.status.value
        t2_sc = f"{result.tier2.anomaly_score:.2f}" if result.tier2 else "0.00"
        cause = result.anomaly_category.value[:20] if result.final_anomaly else "Nominal"
        corr = f"{result.corrected_telemetry.temperature:.1f}C" if result.corrected_telemetry.applied else "--"

        # Highlight anomaly row
        flag = "[!]" if result.final_anomaly else "   "
        print(f"{flag}{i:<3} | {reading.timestamp[:19]} | {t_raw:<9} | {t1_stat:<10} | {t2_sc:<9} | {cause:<22} | {corr}")

        if result.final_anomaly and i == 25:
            print("\n" + "=" * 75)
            print("OPERATOR EXPLAINABILITY & ROOT CAUSE ANALYSIS REPORT (RCA):")
            print("=" * 75)
            print(result.plain_english_rca)
            print("=" * 75)
            print("Top TreeSHAP Feature Attributions:")
            if result.stage3_arbiter and result.stage3_arbiter.shap_attributions:
                top_shap = sorted(result.stage3_arbiter.shap_attributions.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                for k, v in top_shap:
                    print(f"  • {k:<25}: {v:+.4f}")
            print("=" * 75 + "\n")

    print("\nDemonstration Replay Completed Successfully!")


if __name__ == "__main__":
    run_demo()
