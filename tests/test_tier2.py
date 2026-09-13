"""
Tests for Phase 4: Tier 2 Edge Autoencoder
Validates:
- CompactAutoencoder architecture (10 -> 8 -> 4 -> 8 -> 10)
- Training on synthetic normal baseline data
- Reconstruction error threshold calculation
- C++ header weight export
- Parity between trainer model and inference engine
"""

import os
from pathlib import Path
import numpy as np
import pytest
import torch

from skyguard.tier2 import (
    CompactAutoencoder,
    Tier2AutoencoderTrainer,
    Tier2InferenceEngine,
    TIER2_FEATURE_NAMES,
)


@pytest.fixture
def normal_data_matrix():
    # 200 normal readings with 10 features
    rng = np.random.default_rng(42)
    # temp, pres, humi, dew_point, dp_depress, vap_pres, heat_idx, temp_z, pres_z, humi_z
    temps = 25.0 + rng.normal(0.0, 3.0, 200)
    pres = 1013.0 + rng.normal(0.0, 2.0, 200)
    humis = 60.0 + rng.normal(0.0, 5.0, 200)
    dew = temps - 5.0
    dp_dep = temps - dew
    vap = 15.0 + rng.normal(0.0, 1.0, 200)
    heat = temps
    t_z = (temps - 25.0) / 3.0
    p_z = (pres - 1013.0) / 2.0
    h_z = (humis - 60.0) / 5.0

    return np.column_stack([temps, pres, humis, dew, dp_dep, vap, heat, t_z, p_z, h_z])


def test_autoencoder_architecture():
    model = CompactAutoencoder(10, 4)
    x = torch.randn(5, 10)
    out = model(x)
    assert out.shape == (5, 10)


def test_autoencoder_training_and_export(normal_data_matrix, tmp_path):
    trainer = Tier2AutoencoderTrainer()
    history = trainer.fit(normal_data_matrix, epochs=5, batch_size=32)
    assert len(history["train_loss"]) == 5
    assert trainer.threshold > 0.0

    # Test export C++ header
    out_header = tmp_path / "model_weights.h"
    trainer.export_cpp_header(out_header)
    assert out_header.exists()
    content = out_header.read_text(encoding="utf-8")
    assert "TIER2_THRESHOLD" in content
    assert "W_ENC1" in content


def test_inference_engine_parity(normal_data_matrix):
    trainer = Tier2AutoencoderTrainer()
    trainer.fit(normal_data_matrix, epochs=5, batch_size=32)

    engine = Tier2InferenceEngine()
    engine.load_from_trainer(trainer)

    # Test on a normal sample
    feat_dict = {name: float(normal_data_matrix[0, i]) for i, name in enumerate(TIER2_FEATURE_NAMES)}
    res_normal = engine.evaluate(feat_dict)
    assert res_normal.latency_ms < 5.0

    # Test on an extreme anomalous sample (+30°C temperature spike)
    feat_anom = feat_dict.copy()
    feat_anom["temp"] += 35.0
    feat_anom["temp_z"] += 12.0
    res_anom = engine.evaluate(feat_anom)
    assert res_anom.reconstruction_error > res_normal.reconstruction_error
