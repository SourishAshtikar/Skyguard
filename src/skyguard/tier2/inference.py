"""
SkyGuard AI — Tier 2 Edge Inference Engine
Performs ultra-fast (< 0.5 ms) forward pass of the compact autoencoder using numpy.
Computes scaled reconstruction error and normalized anomaly score (0.0 to 1.0).
"""

from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from skyguard.config.contracts import Tier2Output
from .autoencoder import TIER2_FEATURE_NAMES, Tier2AutoencoderTrainer


class Tier2InferenceEngine:
    """Evaluates Tier 2 autoencoder scores on single readings or matrices."""

    def __init__(
        self,
        mean: Optional[np.ndarray] = None,
        std: Optional[np.ndarray] = None,
        weights: Optional[Dict[str, np.ndarray]] = None,
        threshold: float = 0.045,
    ):
        self.mean = mean if mean is not None else np.zeros(10)
        self.std = std if std is not None else np.ones(10)
        self.threshold = threshold
        self.weights = weights or {}

        # Default fallback weights if not trained yet
        if not self.weights:
            self._init_default_weights()

    def _init_default_weights(self):
        # Identity-like projection for 10 -> 8 -> 4 -> 8 -> 10
        rng = np.random.default_rng(42)
        self.weights = {
            "W_enc1": rng.normal(0.0, 0.1, (8, 10)),
            "b_enc1": np.zeros(8),
            "W_enc2": rng.normal(0.0, 0.1, (4, 8)),
            "b_enc2": np.zeros(4),
            "W_dec1": rng.normal(0.0, 0.1, (8, 4)),
            "b_dec1": np.zeros(8),
            "W_dec2": rng.normal(0.0, 0.1, (10, 8)),
            "b_dec2": np.zeros(10),
        }

    def load_from_trainer(self, trainer: Tier2AutoencoderTrainer):
        """Loads weights and scalers directly from trained PyTorch model."""
        self.mean = trainer.mean
        self.std = trainer.std
        self.threshold = trainer.threshold

        params = {k: v.detach().cpu().numpy() for k, v in trainer.model.named_parameters()}
        self.weights = {
            "W_enc1": params["enc1.weight"],
            "b_enc1": params["enc1.bias"],
            "W_enc2": params["enc2.weight"],
            "b_enc2": params["enc2.bias"],
            "W_dec1": params["dec1.weight"],
            "b_dec1": params["dec1.bias"],
            "W_dec2": params["dec2.weight"],
            "b_dec2": params["dec2.bias"],
        }

    def load_from_directory(self, model_dir: Union[str, Path]):
        """Loads weights and scalers directly from saved model directory."""
        import json
        import torch
        from pathlib import Path
        model_dir = Path(model_dir)
        cfg_file = model_dir / "tier2_config.json"
        pth_file = model_dir / "tier2_autoencoder.pth"
        if not cfg_file.exists() or not pth_file.exists():
            raise FileNotFoundError(f"Tier 2 model files not found in {model_dir}")

        config = json.loads(cfg_file.read_text(encoding="utf-8"))
        self.mean = np.array(config["mean"], dtype=float)
        self.std = np.array(config["std"], dtype=float)
        self.threshold = float(config["threshold"])

        state_dict = torch.load(pth_file, map_location="cpu")
        self.weights = {
            "W_enc1": state_dict["enc1.weight"].numpy(),
            "b_enc1": state_dict["enc1.bias"].numpy(),
            "W_enc2": state_dict["enc2.weight"].numpy(),
            "b_enc2": state_dict["enc2.bias"].numpy(),
            "W_dec1": state_dict["dec1.weight"].numpy(),
            "b_dec1": state_dict["dec1.bias"].numpy(),
            "W_dec2": state_dict["dec2.weight"].numpy(),
            "b_dec2": state_dict["dec2.bias"].numpy(),
        }

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Runs forward pass on scaled input vector x (10,). Returns (reconstruction, error_vector)."""
        # Encoder 1
        h1 = np.maximum(0.0, self.weights["W_enc1"] @ x + self.weights["b_enc1"])
        # Encoder 2
        code = np.maximum(0.0, self.weights["W_enc2"] @ h1 + self.weights["b_enc2"])
        # Decoder 1
        h2 = np.maximum(0.0, self.weights["W_dec1"] @ code + self.weights["b_dec1"])
        # Decoder 2
        rec = self.weights["W_dec2"] @ h2 + self.weights["b_dec2"]

        error = (rec - x) ** 2
        return rec, error

    def evaluate(self, features: Dict[str, float]) -> Tier2Output:
        """Evaluates single reading features dictionary. Returns Tier2Output."""
        t0 = time.perf_counter()

        vec = np.array([features.get(k, 0.0) for k in TIER2_FEATURE_NAMES], dtype=float)
        # Normalize
        x_scaled = (vec - self.mean) / self.std

        _, error = self.forward(x_scaled)
        mse = float(np.mean(error))

        # Normalized anomaly score (sigmoid-like scaling around threshold)
        score = 1.0 / (1.0 + np.exp(-4.0 * (mse - self.threshold) / max(1e-4, self.threshold)))
        is_anomaly = mse > self.threshold

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return Tier2Output(
            reconstruction_error=mse,
            anomaly_score=float(np.clip(score, 0.0, 1.0)),
            is_anomaly=bool(is_anomaly),
            threshold=self.threshold,
            latency_ms=latency_ms,
        )
