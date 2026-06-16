"""
Standalone ANFIS training script.

Run this once to pre-train and save ANFIS weights:
    python -m src.neuro_fuzzy.train_anfis

The trained weights are saved to:
    src/neuro_fuzzy/models/anfis_size.pt
    src/neuro_fuzzy/models/anfis_iat.pt
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("  ANFIS Traffic Generator — Training Script")
    logger.info("=" * 60)

    try:
        import torch
        logger.info(f"PyTorch {torch.__version__} detected ✓")
    except ImportError:
        logger.error("PyTorch is not installed. Run: pip install torch")
        sys.exit(1)

    # Force re-train (delete existing weights if any)
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    for f in ["anfis_size.pt", "anfis_iat.pt"]:
        p = models_dir / f
        if p.exists():
            p.unlink()
            logger.info(f"Removed old weights: {f}")

    logger.info("\nTraining on synthetic traffic profiles:")
    logger.info("  • HTTP browsing   — medium packets, variable timing")
    logger.info("  • Video streaming — large packets, steady timing")
    logger.info("  • Idle/heartbeat  — small packets, long gaps")
    logger.info("")

    from .generator import TrafficGenerator
    gen = TrafficGenerator()

    # Test a few predictions
    logger.info("\nTest predictions after training:")
    for i in range(5):
        size, iat = gen.generate_next_packet()
        logger.info(f"  Packet {i+1}: size={size} bytes, IAT={iat*1000:.1f} ms")

    logger.info("\n✅ Training complete! Weights saved to src/neuro_fuzzy/models/")


if __name__ == "__main__":
    main()
