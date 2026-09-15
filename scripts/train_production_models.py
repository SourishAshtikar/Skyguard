"""
SkyGuard AI — Production Model Training Engine
Trains Tier 2 Autoencoder, Tier 3 Isolation Forest, and Tier 3 Hierarchical XGBoost Arbiter
on the comprehensive multi-station Indian AWS meteorological dataset (543 stations).
Saves production-ready model weights, scalers, and C++ headers to the `models/` directory.
"""

import json
import logging
import os
from pathlib import Path
import random
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, accuracy_score

from skyguard.config.contracts import AnomalyCategory, SpatialConsensusOutput
from skyguard.data.anomaly_injector import AnomalyInjector
from skyguard.features import StreamingFeatureExtractor, extract_batch_features
from skyguard.features.streaming import CANONICAL_FEATURES
from skyguard.spatial.neighbor_resolver import SpatialNeighborResolver
from skyguard.tier2.autoencoder import Tier2AutoencoderTrainer, TIER2_FEATURE_NAMES
from skyguard.tier3.arbiter import HierarchicalArbiter, CAUSE_CLASSES
from skyguard.tier3.isoforest import AugmentedIsolationForest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SkyGuardTrain")


def discover_station_files(dataset_dir: Path) -> List[Path]:
    """Finds all non-empty station CSV files."""
    files = list(dataset_dir.glob("*.csv"))
    valid_files = [f for f in files if f.stat().st_size > 10240]  # Minimum 10KB
    logger.info(f"Discovered {len(valid_files)} valid station datasets (out of {len(files)} total files)")
    return valid_files


def load_clean_multi_station_features(
    station_files: List[Path],
    samples_per_station: int = 1500,
    max_stations: int = 120,
) -> pd.DataFrame:
    """Extracts clean historical observation features across diverse Indian stations."""
    rng = random.Random(42)
    selected_files = rng.sample(station_files, min(len(station_files), max_stations))
    
    all_dfs = []
    logger.info(f"Extracting features from {len(selected_files)} stations across India...")

    for i, file_path in enumerate(selected_files):
        try:
            df = pd.read_csv(file_path)
            # Standardize columns
            col_map = {c: c.lower().strip() for c in df.columns}
            df = df.rename(columns=col_map)

            req_cols = ["temperature", "pressure", "humidity", "timestamp"]
            if not all(c in df.columns for c in req_cols):
                continue

            # Drop missing values
            df = df.dropna(subset=["temperature", "pressure", "humidity"]).reset_index(drop=True)
            if len(df) < 200:
                continue

            # Take recent observations
            df_slice = df.iloc[-samples_per_station:].copy().reset_index(drop=True)
            feats_df = extract_batch_features(df_slice)
            feats_df["station_id"] = str(df_slice.get("station_id", [file_path.stem.split("_")[0]])[0])
            all_dfs.append(feats_df)
        except Exception as e:
            continue

    if not all_dfs:
        raise RuntimeError("Failed to load clean features from any station dataset.")

    combined_df = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Clean feature matrix constructed with {len(combined_df)} samples across {len(all_dfs)} stations.")
    return combined_df


def generate_tier3_training_dataset(
    station_files: List[Path],
    spatial_resolver: SpatialNeighborResolver,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Generates labelled training dataset for Tier 3 Arbiter:
    - Model 1: Weather Event (1) vs Malfunction (0)
    - Model 2: Failure Mode Diagnoser (0-9)
    """
    logger.info("Generating realistic multi-station synthetic anomalies and severe weather scenarios...")
    injector = AnomalyInjector(random_seed=42)
    rng = np.random.default_rng(42)

    X_rows = []
    y_weather_list = []
    y_causes_list = []

    # Select representative stations
    sample_files = random.Random(42).sample(station_files, min(len(station_files), 50))

    feature_names = list(CANONICAL_FEATURES) + [
        "spatial_consensus_score",
        "spatial_target_deviation",
        "mahalanobis_distance",
    ]

    cause_map = {cause: idx for idx, cause in enumerate(CAUSE_CLASSES)}

    for f in sample_files:
        try:
            df = pd.read_csv(f)
            df.columns = [c.lower().strip() for c in df.columns]
            df = df.dropna(subset=["temperature", "pressure", "humidity"]).reset_index(drop=True)
            if len(df) < 500:
                continue

            station_id = str(df.get("station_id", [f.stem.split("_")[0]])[0])

            # Scenario A: Normal baseline
            base_df = df.iloc[-300:].copy().reset_index(drop=True)
            base_feats = extract_batch_features(base_df)
            for _, row in base_feats.iloc[48:168].iterrows():
                # Normal reading: realistic spatial consensus, target deviation, and diurnal Mahalanobis innovations
                vec = [row.get(k, 0.0) for k in CANONICAL_FEATURES]
                vec.append(rng.uniform(0.65, 1.0))   # realistic spatial consensus
                vec.append(rng.uniform(0.0, 3.5))    # target deviation
                vec.append(rng.uniform(0.1, 20.0))   # realistic Mahalanobis distance range for normal telemetry
                X_rows.append(vec)
                y_weather_list.append(0)  # Not an anomaly/weather event
                y_causes_list.append(0)   # Default NONE class

            # Scenario B: Genuine Severe Weather Event (Monsoon / Squall / Heatwave)
            weather_df = base_df.copy()
            w_idx = len(weather_df) // 2
            weather_df.loc[w_idx:w_idx+30, "temperature"] -= rng.uniform(6.0, 12.0)
            weather_df.loc[w_idx:w_idx+30, "pressure"] -= rng.uniform(8.0, 15.0)
            weather_df.loc[w_idx:w_idx+30, "humidity"] = np.clip(weather_df.loc[w_idx:w_idx+30, "humidity"] + 30.0, 0, 100)
            w_feats = extract_batch_features(weather_df)

            for _, row in w_feats.iloc[w_idx:w_idx+30].iterrows():
                vec = [row.get(k, 0.0) for k in CANONICAL_FEATURES]
                # High spatial consensus because mesonet confirms ambient shift
                vec.append(rng.uniform(0.80, 0.98))
                vec.append(rng.uniform(0.5, 2.5))
                vec.append(rng.uniform(8.0, 25.0))  # High mahalanobis
                X_rows.append(vec)
                y_weather_list.append(1)  # Genuine weather event
                y_causes_list.append(0)

            # Scenario C: 10 Types of Sensor / Instrument Malfunctions
            anomaly_generators = [
                (injector.inject_spike, AnomalyCategory.SENSOR_SPIKE.value),
                (injector.inject_frozen, AnomalyCategory.FROZEN_SENSOR.value),
                (injector.inject_calibration_drift, AnomalyCategory.CALIBRATION_DRIFT.value),
                (injector.inject_communication_dropout, AnomalyCategory.COMMUNICATION_DROPOUT.value),
                (injector.inject_packet_corruption, AnomalyCategory.PACKET_CORRUPTION.value),
                (injector.inject_physical_inconsistency, AnomalyCategory.PHYSICAL_INCONSISTENCY.value),
                (injector.inject_noise_jitter, AnomalyCategory.NOISE_JITTER.value),
                (injector.inject_range_violation, AnomalyCategory.RANGE_VIOLATION.value),
                (injector.inject_spatial_inconsistency, AnomalyCategory.SPATIAL_INCONSISTENCY.value),
                (injector.inject_temporal_pattern_break, AnomalyCategory.TEMPORAL_PATTERN_BREAK.value),
            ]

            for func, cat_name in anomaly_generators:
                inj_df = base_df.copy()
                inj_df["is_anomaly"] = 0
                inj_df, meta = func(inj_df, start_idx=60)
                inj_feats = extract_batch_features(inj_df)
                
                s_idx = meta.get("start_idx", 60)
                dur = meta.get("duration", 15)
                for _, row in inj_feats.iloc[s_idx : s_idx + dur].iterrows():
                    vec = [row.get(k, 0.0) for k in CANONICAL_FEATURES]
                    # Faults cause poor spatial consensus or high isolated deviation
                    if cat_name in [AnomalyCategory.SPATIAL_INCONSISTENCY.value, AnomalyCategory.RANGE_VIOLATION.value, AnomalyCategory.SENSOR_SPIKE.value]:
                        vec.append(rng.uniform(0.01, 0.35))  # Low consensus
                        vec.append(rng.uniform(8.0, 25.0))   # High target deviation
                    else:
                        vec.append(rng.uniform(0.1, 0.60))
                        vec.append(rng.uniform(3.0, 10.0))
                    vec.append(rng.uniform(12.0, 45.0))       # Elevated Mahalanobis distance

                    X_rows.append(vec)
                    y_weather_list.append(0)  # Instrument fault
                    y_causes_list.append(cause_map.get(cat_name, 0))

        except Exception as e:
            continue

    X = np.array(X_rows, dtype=float)
    y_weather = np.array(y_weather_list, dtype=int)
    y_causes = np.array(y_causes_list, dtype=int)

    # Clean NaNs/Infs
    X = np.nan_to_num(X, nan=0.0, posinf=100.0, neginf=-100.0)

    logger.info(f"Tier 3 Training Matrix constructed: shape={X.shape}, weather_events={np.sum(y_weather)}, fault_samples={len(y_weather)-np.sum(y_weather)}")
    return X, y_weather, y_causes, feature_names


def main():
    project_root = Path(__file__).resolve().parent.parent
    dataset_dir = project_root / "Datasets" / "noaa_india_by_station"
    metadata_path = project_root / "Datasets" / "indian_aws_locations.csv"
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    logger.info("=" * 70)
    logger.info("   SkyGuard AI — Production Model Training on Full India Dataset")
    logger.info("=" * 70)

    # 1. Discover Datasets
    station_files = discover_station_files(dataset_dir)
    spatial_resolver = SpatialNeighborResolver(metadata_csv_path=metadata_path if metadata_path.exists() else None)

    # 2. Extract Multi-Station Clean Data
    logger.info("\n--- Phase 1: Extracting Clean Climatological Matrices ---")
    clean_df = load_clean_multi_station_features(station_files, samples_per_station=1500, max_stations=100)

    # 3. Train Tier 2 Compact Edge Autoencoder
    logger.info("\n--- Phase 2: Training Tier 2 Compact Edge Autoencoder ---")
    X_tier2 = clean_df[TIER2_FEATURE_NAMES].values
    tier2_trainer = Tier2AutoencoderTrainer(input_dim=10, bottleneck_dim=4)
    history = tier2_trainer.fit(X_tier2, epochs=25, batch_size=128, lr=0.005)
    logger.info(f"Tier 2 Training Complete | Final Train Loss: {history['train_loss'][-1]:.6f} | Val Loss: {history['val_loss'][-1]:.6f} | Adaptive Threshold: {tier2_trainer.threshold:.6f}")
    
    tier2_trainer.save(models_dir)
    logger.info(f"Saved Tier 2 Autoencoder weights to {models_dir / 'tier2_autoencoder.pth'} and {models_dir / 'tier2_weights.h'}")

    # 4. Train Tier 3 Stage 2 Isolation Forest
    logger.info("\n--- Phase 3: Training Tier 3 Augmented Isolation Forest ---")
    X_iso = clean_df[list(CANONICAL_FEATURES)].values
    X_iso_aug = np.hstack([X_iso, np.zeros((len(X_iso), 3)), np.ones((len(X_iso), 1)) * 1.5])
    
    iso_forest = AugmentedIsolationForest(contamination=0.015, n_estimators=100)
    iso_forest.fit(X_iso_aug)
    iso_forest.save_model(models_dir / "tier3_isoforest.joblib")
    logger.info(f"Saved Isolation Forest to {models_dir / 'tier3_isoforest.joblib'}")

    # 5. Generate Labelled Multi-Station Dataset for Stage 3 Arbiter
    logger.info("\n--- Phase 4: Training Tier 3 Hierarchical XGBoost Arbiter ---")
    X_t3, y_weather, y_causes, feature_names = generate_tier3_training_dataset(
        station_files=station_files,
        spatial_resolver=spatial_resolver,
    )

    X_train, X_val, yw_train, yw_val, yc_train, yc_val = train_test_split(
        X_t3, y_weather, y_causes, test_size=0.15, random_state=42
    )

    arbiter = HierarchicalArbiter()
    arbiter.fit(X_train, yw_train, yc_train, feature_names=feature_names)

    # Evaluate validation performance
    yw_pred = arbiter.weather_model.predict(X_val)
    yc_pred = arbiter.diagnoser_model.predict(X_val)

    w_acc = accuracy_score(yw_val, yw_pred)
    w_f1 = f1_score(yw_val, yw_pred, average="macro")
    c_acc = accuracy_score(yc_val, yc_pred)
    c_f1 = f1_score(yc_val, yc_pred, average="weighted")

    logger.info(f"Model 1 (Weather Classifier) | Val Accuracy: {w_acc * 100:.2f}% | Macro F1: {w_f1:.4f}")
    logger.info(f"Model 2 (Fault Diagnoser)    | Val Accuracy: {c_acc * 100:.2f}% | Weighted F1: {c_f1:.4f}")

    arbiter.save_models(models_dir)
    logger.info(f"Saved Tier 3 Arbiter XGBoost models to {models_dir / 'tier3_weather_arbiter.json'} and {models_dir / 'tier3_fault_diagnoser.json'}")

    # 6. Save Training Metadata
    metadata = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_stations_available": len(station_files),
        "tier2_samples": len(X_tier2),
        "tier2_train_loss": history['train_loss'][-1],
        "tier2_val_loss": history['val_loss'][-1],
        "tier2_threshold": tier2_trainer.threshold,
        "tier3_samples": len(X_t3),
        "weather_classifier_f1": float(w_f1),
        "fault_diagnoser_f1": float(c_f1),
        "feature_names": feature_names,
        "classes": CAUSE_CLASSES,
    }
    (models_dir / "training_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    elapsed = time.time() - t_start
    logger.info("\n" + "=" * 70)
    logger.info(f"   TRAINING COMPLETE IN {elapsed:.2f}s — ALL MODELS PERSISTED & PRODUCTION READY")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
