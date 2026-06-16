"""
Adversarial Traffic Discriminator (GAN-style).

The discriminator is a binary LSTM classifier that tries to distinguish
real traffic sequences from ANFIS-generated dummy traffic.

In the obfuscation context:
  - If discriminability score is HIGH → dummy traffic is detectable → bad
  - If discriminability score is LOW  → traffic is indistinguishable → good

The generator (ANFIS) "wins" when the discriminator cannot tell real from fake.
This score is displayed on the dashboard as a quality metric.
"""
import logging
import collections

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

if TORCH_AVAILABLE:
    class TrafficDiscriminator(nn.Module):
        """
        LSTM-based binary classifier.
        Input:  Sequence of (normalized_size, iat) — shape (batch, seq_len, 2)
        Output: Probability [0, 1] that traffic is REAL (1=real, 0=generated)
        """
        def __init__(self, seq_length: int = 10):
            super().__init__()
            self.seq_length = seq_length

            self.lstm = nn.LSTM(
                input_size=2,
                hidden_size=64,
                num_layers=2,
                batch_first=True,
                dropout=0.2,
            )
            self.classifier = nn.Sequential(
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(32, 1),
                nn.Sigmoid(),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            out, _ = self.lstm(x)
            return self.classifier(out[:, -1, :])


class AdversarialEvaluator:
    """
    Maintains a rolling buffer of recent packets and periodically
    evaluates how distinguishable the generated traffic is.

    Usage:
        evaluator = AdversarialEvaluator()
        evaluator.add_packet(size, iat, is_dummy)
        score = evaluator.get_discriminability()  # 0.0 = perfect, 1.0 = detectable
    """
    SEQ_LEN = 10
    EVAL_EVERY = 20  # Evaluate every N packets

    def __init__(self):
        self.real_buf = collections.deque(maxlen=200)
        self.fake_buf = collections.deque(maxlen=200)
        self.packet_count = 0
        self.discriminability = 0.5  # Start at 50% (uncertain)

        if TORCH_AVAILABLE:
            self.discriminator = TrafficDiscriminator(seq_length=self.SEQ_LEN)
            self.optimizer = optim.Adam(self.discriminator.parameters(), lr=0.001)
            self.criterion = nn.BCELoss()
        else:
            self.discriminator = None

    def add_packet(self, size: int, iat_ms: float, is_dummy: bool):
        """Record a sent packet."""
        # Normalize
        norm_size = min(size / 1500.0, 1.0)
        norm_iat = min(iat_ms / 2000.0, 1.0)
        entry = (norm_size, norm_iat)

        if is_dummy:
            self.fake_buf.append(entry)
        else:
            self.real_buf.append(entry)

        self.packet_count += 1

        if self.packet_count % self.EVAL_EVERY == 0:
            self._evaluate()

    def get_discriminability(self) -> float:
        """
        Return current discriminability score.
        0.0 = perfectly obfuscated, 1.0 = easily detected.
        """
        return round(self.discriminability, 3)

    def _evaluate(self):
        """Run one discriminator train step and update the score."""
        if not TORCH_AVAILABLE or self.discriminator is None:
            # Without PyTorch, approximate using statistical distance
            self._statistical_score()
            return

        if len(self.real_buf) < self.SEQ_LEN or len(self.fake_buf) < self.SEQ_LEN:
            return

        try:
            real_seq = self._make_sequence(self.real_buf)
            fake_seq = self._make_sequence(self.fake_buf)

            real_labels = torch.ones(real_seq.size(0), 1)
            fake_labels = torch.zeros(fake_seq.size(0), 1)

            self.optimizer.zero_grad()
            loss_r = self.criterion(self.discriminator(real_seq), real_labels)
            loss_f = self.criterion(self.discriminator(fake_seq.detach()), fake_labels)
            loss = (loss_r + loss_f) / 2
            loss.backward()
            self.optimizer.step()

            # Discriminability = how well the discriminator separates them
            with torch.no_grad():
                real_score = self.discriminator(real_seq).mean().item()
                fake_score = self.discriminator(fake_seq).mean().item()
            # Perfect obfuscation: real_score ≈ fake_score ≈ 0.5
            self.discriminability = abs(real_score - fake_score)

        except Exception as e:
            logger.debug(f"Discriminator eval error: {e}")

    def _make_sequence(self, buf) -> "torch.Tensor":
        """Build a batch of overlapping sequences from the buffer."""
        items = list(buf)
        seqs = []
        for i in range(len(items) - self.SEQ_LEN + 1):
            seqs.append(items[i: i + self.SEQ_LEN])
        t = torch.tensor(seqs, dtype=torch.float32)  # (N, seq_len, 2)
        return t

    def _statistical_score(self):
        """Fallback: compare means of real vs fake distributions."""
        if len(self.real_buf) < 5 or len(self.fake_buf) < 5:
            return
        import math
        real_sizes = [x[0] for x in self.real_buf]
        fake_sizes = [x[0] for x in self.fake_buf]
        mean_r = sum(real_sizes) / len(real_sizes)
        mean_f = sum(fake_sizes) / len(fake_sizes)
        self.discriminability = min(1.0, abs(mean_r - mean_f))
