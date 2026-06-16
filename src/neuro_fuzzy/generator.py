"""
Traffic Generator using ANFIS (Adaptive Neuro-Fuzzy Inference System).

Generates realistic packet sizes and inter-arrival times (IAT) by predicting
the next packet parameters from a sliding window of historical traffic.

On first run: trains on synthetic traffic profiles and saves weights.
Subsequent runs: loads saved weights instantly.
"""
import os
import logging
import numpy as np
from pathlib import Path

from .anfis import ANFIS, TORCH_AVAILABLE

logger = logging.getLogger(__name__)

# Directory to store trained model weights
_MODELS_DIR = Path(__file__).parent / "models"
_SIZE_MODEL_PATH = _MODELS_DIR / "anfis_size.pt"
_IAT_MODEL_PATH = _MODELS_DIR / "anfis_iat.pt"


class TrafficGenerator:
    """
    Generates synthetic traffic patterns using trained ANFIS models.

    Input features: (normalized_size, iat) for the last n_history packets → 2*n_history inputs
    Outputs: predicted next (size, iat)
    """

    def __init__(self, n_history: int = 5):
        self.n_history = n_history
        self.input_dim = 2 * n_history
        self.n_rules = 12

        self.model_size = ANFIS(self.input_dim, self.n_rules)
        self.model_iat = ANFIS(self.input_dim, self.n_rules)

        # Sliding window: [size_t-n, iat_t-n, ..., size_t-1, iat_t-1]
        self.history_buffer = np.zeros(self.input_dim)

        # Load or train
        self._ensure_trained()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_next_packet(self) -> tuple:
        """
        Predict the next packet's (size_bytes, iat_seconds).

        Returns:
            (size: int, iat: float)
        """
        inputs = self._normalize_inputs()

        if TORCH_AVAILABLE:
            import torch
            t = torch.tensor(inputs, dtype=torch.float32)
            pred_size_norm = self.model_size.infer(t)
            pred_iat = self.model_iat.infer(t)
        else:
            pred_size_norm = self.model_size.infer(inputs)
            pred_iat = self.model_iat.infer(inputs)

        # Denormalize & clamp to valid ranges
        pred_size = int(pred_size_norm * 1500.0)
        pred_size = max(64, min(1500, abs(pred_size)))
        pred_iat = max(0.001, min(2.0, abs(pred_iat)))

        self._update_history(pred_size, pred_iat)
        return pred_size, pred_iat

    def generate_sequence(self, length: int = 100) -> list:
        """Generate a sequence of (size, iat) tuples."""
        return [self.generate_next_packet() for _ in range(length)]

    # ------------------------------------------------------------------
    # Training & persistence
    # ------------------------------------------------------------------

    def _ensure_trained(self):
        """Load pretrained weights or train from scratch."""
        _MODELS_DIR.mkdir(exist_ok=True)

        if _SIZE_MODEL_PATH.exists() and _IAT_MODEL_PATH.exists():
            try:
                self.model_size.load(str(_SIZE_MODEL_PATH))
                self.model_iat.load(str(_IAT_MODEL_PATH))
                logger.info("ANFIS weights loaded from disk ✓")
                return
            except Exception as e:
                logger.warning(f"Could not load ANFIS weights ({e}), retraining...")

        logger.info("Training ANFIS on synthetic traffic data...")
        self.train_on_synthetic_data(save=True, verbose=False)
        logger.info("ANFIS training complete ✓")

    def train_on_synthetic_data(
        self,
        n_samples: int = 2000,
        epochs: int = 300,
        lr: float = 0.005,
        save: bool = True,
        verbose: bool = True,
    ):
        """
        Generate synthetic traffic and train both ANFIS models.

        Traffic profiles simulated:
          - HTTP browsing: medium packets (200-1400 bytes), variable IAT (50-500ms)
          - Video streaming: large packets (1000-1500 bytes), steady IAT (10-30ms)
          - Idle / heartbeat: small packets (64-128 bytes), long IAT (500ms-2s)
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available — skipping ANFIS training")
            return

        import torch

        X_list, y_size_list, y_iat_list = [], [], []
        rng = np.random.default_rng(42)

        # --- Generate synthetic sequences ---
        profiles = {
            "http":    {"size_range": (200, 1400), "iat_range": (0.05, 0.5),  "n": n_samples // 3},
            "video":   {"size_range": (1000, 1500), "iat_range": (0.01, 0.03), "n": n_samples // 3},
            "idle":    {"size_range": (64, 128),   "iat_range": (0.5, 2.0),   "n": n_samples // 3},
        }

        # Accumulate a rolling history buffer for dataset construction
        buf = np.zeros(self.input_dim)
        for profile_name, cfg in profiles.items():
            lo_s, hi_s = cfg["size_range"]
            lo_i, hi_i = cfg["iat_range"]
            for _ in range(cfg["n"]):
                size = rng.integers(lo_s, hi_s)
                iat = rng.uniform(lo_i, hi_i)

                # Current buffer is features; (size, iat) is targets
                X_list.append(buf.copy())
                y_size_list.append(size / 1500.0)  # normalize
                y_iat_list.append(iat)

                # Update buffer
                buf[:-2] = buf[2:]
                buf[-2] = size / 1500.0
                buf[-1] = iat

        X = torch.tensor(np.array(X_list), dtype=torch.float32)
        y_size = torch.tensor(np.array(y_size_list), dtype=torch.float32)
        y_iat = torch.tensor(np.array(y_iat_list), dtype=torch.float32)

        if verbose:
            logger.info(f"Training on {len(X)} samples | epochs={epochs} | lr={lr}")

        self.model_size.train_model(X, y_size, epochs=epochs, lr=lr, verbose=verbose)
        self.model_iat.train_model(X, y_iat, epochs=epochs, lr=lr, verbose=verbose)

        if save:
            self.model_size.save(str(_SIZE_MODEL_PATH))
            self.model_iat.save(str(_IAT_MODEL_PATH))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_inputs(self) -> np.ndarray:
        """Return normalized copy of history buffer."""
        inp = self.history_buffer.copy()
        inp[0::2] /= 1500.0  # normalize sizes (every even index)
        return inp

    def _update_history(self, size: int, iat: float):
        """Slide the history window forward."""
        self.history_buffer[:-2] = self.history_buffer[2:]
        self.history_buffer[-2] = size
        self.history_buffer[-1] = iat
