import logging
import random

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    logging.warning("Torch not found. Using Mock ANFIS.")

if TORCH_AVAILABLE:
    class GaussianMF(nn.Module):
        """Gaussian Membership Function — learnable center (mu) and width (sigma)."""
        def __init__(self, mu, sigma):
            super().__init__()
            self.mu = nn.Parameter(torch.tensor(mu, dtype=torch.float32))
            self.sigma = nn.Parameter(torch.tensor(sigma, dtype=torch.float32))

        def forward(self, x):
            return torch.exp(-((x - self.mu) ** 2) / (2 * self.sigma ** 2 + 1e-8))

    class ANFIS(nn.Module):
        """
        Adaptive Neuro-Fuzzy Inference System (Takagi-Sugeno type).

        Architecture:
          Layer 1 — Gaussian membership functions per rule per input
          Layer 2 — Rule firing strengths (product of MFs)
          Layer 3 — Normalized firing strengths
          Layer 4 — Linear consequent functions (ax + b per rule)
          Layer 5 — Weighted sum output
        """
        def __init__(self, n_inputs: int, n_rules: int):
            super().__init__()
            self.n_inputs = n_inputs
            self.n_rules = n_rules

            # Learnable Gaussian MF parameters
            self.mus = nn.Parameter(torch.randn(n_rules, n_inputs))
            self.sigmas = nn.Parameter(torch.ones(n_rules, n_inputs) * 0.5)

            # Consequent parameters (linear output per rule)
            self.consequent_weights = nn.Parameter(torch.randn(n_rules, n_inputs) * 0.1)
            self.consequent_bias = nn.Parameter(torch.zeros(n_rules))

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            """
            Forward pass.
            Args:
                x: Input tensor of shape (batch_size, n_inputs)
            Returns:
                Output tensor of shape (batch_size,)
            """
            # Layer 1-2: Compute firing strengths
            x_exp = x.unsqueeze(1).expand(-1, self.n_rules, -1)       # (B, R, I)
            mus_exp = self.mus.unsqueeze(0)                              # (1, R, I)
            sigs_exp = self.sigmas.unsqueeze(0)                          # (1, R, I)

            mfs = torch.exp(-((x_exp - mus_exp) ** 2) / (2 * sigs_exp ** 2 + 1e-8))
            w = torch.prod(mfs, dim=2)                                   # (B, R)

            # Layer 3: Normalize
            w_norm = w / (w.sum(dim=1, keepdim=True) + 1e-8)            # (B, R)

            # Layer 4: Consequent (linear)
            linear = (x_exp * self.consequent_weights.unsqueeze(0)).sum(dim=2) \
                     + self.consequent_bias.unsqueeze(0)                 # (B, R)

            # Layer 5: Defuzzify
            out = (w_norm * linear).sum(dim=1)                           # (B,)
            return out

        def infer(self, x) -> float:
            """Single-sample inference without gradient computation."""
            with torch.no_grad():
                if not isinstance(x, torch.Tensor):
                    x = torch.tensor(x, dtype=torch.float32)
                if x.dim() == 1:
                    x = x.unsqueeze(0)
                return self.forward(x).item()

        def train_model(
            self,
            X: "torch.Tensor",
            y: "torch.Tensor",
            epochs: int = 200,
            lr: float = 0.01,
            verbose: bool = False,
        ) -> list:
            """
            Train the ANFIS with Adam optimizer and MSE loss.

            Args:
                X: Feature tensor (N, n_inputs)
                y: Target tensor (N,)
                epochs: Number of training epochs
                lr: Learning rate
                verbose: Print loss every 50 epochs

            Returns:
                List of loss values per epoch
            """
            optimizer = optim.Adam(self.parameters(), lr=lr)
            criterion = nn.MSELoss()
            losses = []

            self.train_mode()
            for epoch in range(epochs):
                optimizer.zero_grad()
                pred = self.forward(X)
                loss = criterion(pred, y)
                loss.backward()
                optimizer.step()
                losses.append(loss.item())
                if verbose and (epoch + 1) % 50 == 0:
                    logging.info(f"ANFIS Epoch [{epoch+1}/{epochs}] Loss: {loss.item():.6f}")

            self.eval()
            return losses

        def train_mode(self):
            """Switch to training mode."""
            self.train()

        def save(self, path: str):
            """Save model weights to disk."""
            torch.save(self.state_dict(), path)
            logging.info(f"ANFIS weights saved → {path}")

        def load(self, path: str):
            """Load model weights from disk."""
            self.load_state_dict(torch.load(path, map_location="cpu"))
            self.eval()
            logging.info(f"ANFIS weights loaded ← {path}")

else:
    class ANFIS:
        """Mock ANFIS used when PyTorch is not installed."""
        def __init__(self, n_inputs, n_rules):
            self.n_inputs = n_inputs
            self.n_rules = n_rules

        def infer(self, x) -> float:
            return random.random()

        def train_model(self, X, y, epochs=200, lr=0.01, verbose=False):
            return []

        def save(self, path: str):
            pass

        def load(self, path: str):
            pass
