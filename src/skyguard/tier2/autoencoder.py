"""
SkyGuard AI — Tier 2 Compact Edge Autoencoder
Architecture: 10 -> 8 -> 4 -> 8 -> 10 (Bottleneck = 4 features, ~200 total parameters)
Input: 10 core physical and thermodynamic features.
Lightweight enough to execute in < 3.5 ms on ESP32 microcontroller with < 40 KB SRAM.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

TIER2_FEATURE_NAMES: List[str] = [
    "temp",
    "pres",
    "humi",
    "dew_point",
    "dp_depress",
    "vap_pres",
    "heat_idx",
    "temp_z",
    "pres_z",
    "humi_z",
]


class CompactAutoencoder(nn.Module):
    """Symmetric 10 -> 8 -> 4 -> 8 -> 10 autoencoder with ReLU activations."""

    def __init__(self, input_dim: int = 10, bottleneck_dim: int = 4):
        super().__init__()
        # Encoder
        self.enc1 = nn.Linear(input_dim, 8)
        self.enc_act1 = nn.ReLU()
        self.enc2 = nn.Linear(8, bottleneck_dim)
        self.enc_act2 = nn.ReLU()

        # Decoder
        self.dec1 = nn.Linear(bottleneck_dim, 8)
        self.dec_act1 = nn.ReLU()
        self.dec2 = nn.Linear(8, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h1 = self.enc_act1(self.enc1(x))
        code = self.enc_act2(self.enc2(h1))
        h2 = self.dec_act1(self.dec1(code))
        reconstructed = self.dec2(h2)
        return reconstructed


class Tier2AutoencoderTrainer:
    """Trains the compact autoencoder on normal baseline observations and exports weights."""

    def __init__(self, input_dim: int = 10, bottleneck_dim: int = 4):
        self.model = CompactAutoencoder(input_dim=input_dim, bottleneck_dim=bottleneck_dim)
        self.mean: np.ndarray = np.zeros(input_dim)
        self.std: np.ndarray = np.ones(input_dim)
        self.threshold: float = 0.05

    def fit(
        self,
        X_train: np.ndarray,
        epochs: int = 25,
        batch_size: int = 64,
        lr: float = 0.005,
        val_split: float = 0.15,
    ) -> Dict[str, List[float]]:
        """Trains autoencoder on normal telemetry matrices (N, 10)."""
        # Fit standard scaler
        self.mean = np.mean(X_train, axis=0)
        self.std = np.std(X_train, axis=0)
        self.std = np.where(self.std < 1e-5, 1.0, self.std)

        X_scaled = (X_train - self.mean) / self.std

        # Validation split
        n_val = int(len(X_scaled) * val_split)
        if n_val > 0:
            X_tr, X_va = X_scaled[:-n_val], X_scaled[-n_val:]
        else:
            X_tr, X_va = X_scaled, X_scaled

        tensor_x = torch.tensor(X_tr, dtype=torch.float32)
        dataset = torch.utils.data.TensorDataset(tensor_x)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
        criterion = nn.MSELoss()

        history = {"train_loss": [], "val_loss": []}
        self.model.train()

        for epoch in range(epochs):
            epoch_loss = 0.0
            for (batch,) in loader:
                optimizer.zero_grad()
                pred = self.model(batch)
                loss = criterion(pred, batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * len(batch)
            epoch_loss /= len(X_tr)
            history["train_loss"].append(epoch_loss)

            # Validation loss
            self.model.eval()
            with torch.no_grad():
                va_tensor = torch.tensor(X_va, dtype=torch.float32)
                va_pred = self.model(va_tensor)
                va_loss = criterion(va_pred, va_tensor).item()
                history["val_loss"].append(va_loss)
            self.model.train()

        # Compute adaptive reconstruction error threshold (99th percentile of normal validation data)
        self.model.eval()
        with torch.no_grad():
            diff = (self.model(va_tensor) - va_tensor).numpy()
            mse_errors = np.mean(diff ** 2, axis=1)
            self.threshold = float(np.percentile(mse_errors, 99.0))
            if self.threshold < 1e-4:
                self.threshold = 0.005

        return history

    def save(self, model_dir: Union[str, Path]):
        """Saves PyTorch weights, config, and statistics to directory."""
        import json
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), model_dir / "tier2_autoencoder.pth")
        config = {
            "mean": self.mean.tolist(),
            "std": self.std.tolist(),
            "threshold": float(self.threshold),
            "input_dim": len(self.mean),
            "bottleneck_dim": 4,
            "feature_names": TIER2_FEATURE_NAMES,
        }
        (model_dir / "tier2_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        self.export_cpp_header(model_dir / "tier2_weights.h")

    def load(self, model_dir: Union[str, Path]):
        """Loads PyTorch weights, config, and statistics from directory."""
        import json
        model_dir = Path(model_dir)
        cfg_file = model_dir / "tier2_config.json"
        pth_file = model_dir / "tier2_autoencoder.pth"
        if not cfg_file.exists() or not pth_file.exists():
            raise FileNotFoundError(f"Tier 2 model files not found in {model_dir}")
        config = json.loads(cfg_file.read_text(encoding="utf-8"))
        self.mean = np.array(config["mean"], dtype=float)
        self.std = np.array(config["std"], dtype=float)
        self.threshold = float(config["threshold"])
        self.model = CompactAutoencoder(input_dim=config.get("input_dim", 10), bottleneck_dim=config.get("bottleneck_dim", 4))
        self.model.load_state_dict(torch.load(pth_file, map_location="cpu"))
        self.model.eval()

    def export_cpp_header(self, output_path: Union[str, Path]):
        """Exports weights, biases, mean, std, and threshold to an ESP32 C++ header file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        params = {k: v.detach().cpu().numpy() for k, v in self.model.named_parameters()}

        def format_1d(arr: np.ndarray) -> str:
            return ", ".join(f"{x:.6f}f" for x in arr)

        def format_2d(arr: np.ndarray) -> str:
            lines = []
            for row in arr:
                lines.append("    {" + ", ".join(f"{x:.6f}f" for x in row) + "}")
            return ",\n".join(lines)

        content = f"""#ifndef SKYGUARD_TIER2_WEIGHTS_H
#define SKYGUARD_TIER2_WEIGHTS_H

// Auto-generated SkyGuard AI Tier 2 Autoencoder Weights
// Architecture: 10 -> 8 -> 4 -> 8 -> 10

#define TIER2_INPUT_DIM 10
#define TIER2_HIDDEN1_DIM 8
#define TIER2_BOTTLENECK_DIM 4
#define TIER2_HIDDEN2_DIM 8

static const float TIER2_THRESHOLD = {self.threshold:.6f}f;

static const float TIER2_MEAN[TIER2_INPUT_DIM] = {{
    {format_1d(self.mean)}
}};

static const float TIER2_STD[TIER2_INPUT_DIM] = {{
    {format_1d(self.std)}
}};

// Encoder 1: [8][10]
static const float W_ENC1[8][10] = {{
{format_2d(params['enc1.weight'])}
}};
static const float B_ENC1[8] = {{
    {format_1d(params['enc1.bias'])}
}};

// Encoder 2: [4][8]
static const float W_ENC2[4][8] = {{
{format_2d(params['enc2.weight'])}
}};
static const float B_ENC2[4] = {{
    {format_1d(params['enc2.bias'])}
}};

// Decoder 1: [8][4]
static const float W_DEC1[8][4] = {{
{format_2d(params['dec1.weight'])}
}};
static const float B_DEC1[8] = {{
    {format_1d(params['dec1.bias'])}
}};

// Decoder 2: [10][8]
static const float W_DEC2[10][8] = {{
{format_2d(params['dec2.weight'])}
}};
static const float B_DEC2[10] = {{
    {format_1d(params['dec2.bias'])}
}};

#endif // SKYGUARD_TIER2_WEIGHTS_H
"""
        output_path.write_text(content, encoding="utf-8")
