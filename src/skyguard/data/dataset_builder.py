"""
SkyGuard AI — Dataset Builder
Constructs benchmark evaluation datasets by applying deterministic anomaly injections
onto clean baseline NOAA station data with chronological train/validation/test splits.
"""

from typing import Dict, List, Tuple
import pandas as pd

from .anomaly_injector import AnomalyInjector, AnomalyInjectionMeta


class DatasetBuilder:
    """Builds synthetic anomaly datasets for training Tier 2 and Tier 3 models and evaluation."""

    def __init__(self, random_seed: int = 42):
        self.injector = AnomalyInjector(random_seed=random_seed)

    def generate_benchmark_dataset(
        self, baseline_df: pd.DataFrame, num_episodes: int = 10
    ) -> Tuple[pd.DataFrame, List[AnomalyInjectionMeta]]:
        """Injects a rich balanced mixture of all 10 anomaly classes onto clean baseline series."""
        df = baseline_df.copy()
        df["is_anomaly"] = 0
        df["anomaly_type"] = "NONE"
        df["affected_sensor"] = "none"
        df["ground_truth_root_cause"] = "Normal Atmospheric Behavior"

        meta_list: List[AnomalyInjectionMeta] = []
        n = len(df)
        step = max(30, n // (num_episodes + 2))

        methods = [
            ("inject_spike", {"sensor": "temperature"}),
            ("inject_frozen", {"sensor": "humidity", "duration": 10}),
            ("inject_calibration_drift", {"sensor": "pressure", "duration": 24}),
            ("inject_communication_dropout", {"sensor": "all", "duration": 6}),
            ("inject_packet_corruption", {"sensor": "temperature"}),
            ("inject_physical_inconsistency", {"duration": 4}),
            ("inject_noise_jitter", {"sensor": "temperature", "duration": 12}),
            ("inject_range_violation", {"sensor": "temperature"}),
            ("inject_spatial_inconsistency", {"sensor": "temperature", "duration": 8}),
            ("inject_temporal_pattern_break", {"sensor": "temperature", "duration": 18}),
        ]

        for i, (m_name, kwargs) in enumerate(methods[:num_episodes]):
            idx = 10 + i * step
            if idx >= n - 25:
                break
            method = getattr(self.injector, m_name)
            df, meta = method(df, start_idx=idx, **kwargs)
            meta_list.append(meta)

        return df, meta_list

    def split_chronological(
        self, df: pd.DataFrame, train_ratio: float = 0.7, val_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Splits chronologically into train, validation, and test subsets."""
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end].copy().reset_index(drop=True)
        val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = df.iloc[val_end:].copy().reset_index(drop=True)

        return train_df, val_df, test_df
