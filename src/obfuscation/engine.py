import time
import threading
import queue
import logging
import os
import random
import math

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..neuro_fuzzy.generator import TrafficGenerator
from ..crypto.pq_wrapper import KEM, Signature

logger = logging.getLogger(__name__)


def compute_entropy(data: bytes) -> float:
    """Compute Shannon entropy (bits/byte) of a byte string."""
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    n = len(data)
    entropy = -sum((c / n) * math.log2(c / n) for c in freq.values())
    return round(entropy, 4)


class ObfuscationEngine:
    """
    Post-Quantum Metadata Obfuscation Engine.

    Sends a constant-rate stream of packets mixing real (encrypted) data
    with AI-generated dummy packets. Uses AES-256-GCM symmetric encryption
    keyed from the post-quantum KEM shared secret.
    """

    def __init__(self, output_callback=None):
        """
        Args:
            output_callback: Callable(packet_bytes: bytes, metadata: dict)
                             Called for every packet sent.
                             metadata contains: is_dummy, size, entropy, iat_ms, path_id
        """
        self.pkt_queue = queue.Queue()
        self.traffic_gen = TrafficGenerator()
        self.output_callback = output_callback
        self.running = False
        self.lock = threading.Lock()

        # Stats
        self.total_packets = 0
        self.real_packets = 0
        self.dummy_packets = 0
        self.total_bytes = 0
        self.discriminability_score = 0.5  # 0=perfect obfuscation, 1=easily detected

        # Post-Quantum Crypto setup
        self.kem = KEM()
        self.signer = Signature()
        self.pub_key, self.sec_key = self.kem.generate_keypair()

        # Derive a 256-bit AES key from the KEM shared secret
        # In real usage: Alice encapsulates to Bob's pub_key and sends ciphertext;
        # Bob decapsulates to get the same shared_secret.
        # Here we simulate both sides on one node for demo.
        _ct, shared_secret = self.kem.encaps(self.pub_key)
        # Use first 32 bytes of shared_secret as AES-GCM key
        self._aes_key = shared_secret[:32].ljust(32, b'\x00')
        self._aesgcm = AESGCM(self._aes_key)

        logger.info(
            f"ObfuscationEngine ready | KEM={self.kem.alg_name} | "
            f"Sig={self.signer.alg_name} | PQ={'real' if self.kem.is_enabled() else 'simulation'}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Starts the constant-rate traffic generation loop."""
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("ObfuscationEngine started.")

    def stop(self):
        """Stops the engine gracefully."""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=3)
        logger.info(
            f"ObfuscationEngine stopped | total={self.total_packets} "
            f"real={self.real_packets} dummy={self.dummy_packets}"
        )

    def send_data(self, data: bytes):
        """
        Encrypt and enqueue data for transmission.

        Uses AES-256-GCM with a random 96-bit nonce per packet.
        The nonce is prepended to the ciphertext (standard practice).
        """
        nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
        ciphertext = self._aesgcm.encrypt(nonce, data, None)
        # Packet format: [12-byte nonce][ciphertext+16-byte GCM tag]
        encrypted_payload = nonce + ciphertext
        self.pkt_queue.put(encrypted_payload)
        logger.debug(f"Queued encrypted packet ({len(encrypted_payload)} bytes)")

    def decrypt_data(self, packet: bytes) -> bytes:
        """
        Decrypt a packet that was encrypted by send_data().
        Raises InvalidTag if the packet was tampered with.
        """
        nonce = packet[:12]
        ciphertext = packet[12:]
        return self._aesgcm.decrypt(nonce, ciphertext, None)

    def get_stats(self) -> dict:
        """Return current engine statistics."""
        total = self.total_packets or 1
        return {
            "total_packets": self.total_packets,
            "real_packets": self.real_packets,
            "dummy_packets": self.dummy_packets,
            "total_bytes": self.total_bytes,
            "dummy_ratio": round(self.dummy_packets / total, 3),
            "discriminability": round(self.discriminability_score, 3),
            "pq_mode": "real" if self.kem.is_enabled() else "simulation",
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _pad_packet(self, data: bytes, target_size: int) -> bytes:
        """Pad packet to target_size with random bytes (hides true length)."""
        if len(data) < target_size:
            return data + os.urandom(target_size - len(data))
        return data

    def _run_loop(self):
        last_send_time = time.monotonic()

        while self.running:
            # Get predicted next packet parameters from ANFIS
            target_size, target_iat = self.traffic_gen.generate_next_packet()

            # Wait for the inter-arrival time
            time.sleep(max(0.001, target_iat))

            now = time.monotonic()
            actual_iat_ms = (now - last_send_time) * 1000
            last_send_time = now

            # Decide: real data or dummy
            try:
                real_packet = self.pkt_queue.get_nowait()
                is_dummy = False
                payload = self._pad_packet(real_packet, target_size)
            except queue.Empty:
                is_dummy = True
                # Dummy: random bytes — indistinguishable from encrypted data
                payload = os.urandom(target_size)

            # Compute packet entropy (for dashboard / discriminator)
            entropy = compute_entropy(payload)

            # Update stats
            with self.lock:
                self.total_packets += 1
                self.total_bytes += len(payload)
                if is_dummy:
                    self.dummy_packets += 1
                else:
                    self.real_packets += 1

            # Build metadata
            metadata = {
                "is_dummy": is_dummy,
                "size": len(payload),
                "entropy": entropy,
                "iat_ms": round(actual_iat_ms, 2),
                "path_id": random.randint(0, 2),  # Multipath (0-2)
                "pq_mode": "real" if self.kem.is_enabled() else "simulation",
            }

            if self.output_callback:
                self.output_callback(payload, metadata)

            logger.debug(
                f"{'DUMMY' if is_dummy else 'REAL '} | "
                f"size={len(payload)} | entropy={entropy:.3f} | iat={actual_iat_ms:.1f}ms"
            )
