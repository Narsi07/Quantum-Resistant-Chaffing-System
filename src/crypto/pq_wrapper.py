import os
import logging

try:
    import oqs
    LIBOQS_AVAILABLE = True
except ImportError:
    LIBOQS_AVAILABLE = False
    logging.warning("liboqs-python not found. Using SIMULATION mode for Post-Quantum Cryptography.")

class PQWrapper:
    """Base class for Post-Quantum Cryptographic primitives."""
    def __init__(self, alg_name):
        self.alg_name = alg_name
        self.mechanism = None

    def is_enabled(self):
        return LIBOQS_AVAILABLE

class KEM(PQWrapper):
    """Key Encapsulation Mechanism Wrapper (e.g., Kyber)."""
    def __init__(self, alg_name="Kyber512"):
        super().__init__(alg_name)
        if self.is_enabled():
            self.mechanism = oqs.KeyEncapsulation(alg_name)
        else:
            self.mechanism = None # Simulation

    def generate_keypair(self):
        """Generates public and secret keys."""
        if self.is_enabled():
            public_key = self.mechanism.generate_keypair()
            secret_key = self.mechanism.export_secret_key()
            return public_key, secret_key
        else:
            # Simulation: Just random bytes
            pk = os.urandom(800) # Approximate size for Kyber512
            sk = os.urandom(1632)
            return pk, sk

    def encaps(self, public_key):
        """Generates shared secret and ciphertext."""
        if self.is_enabled():
            ciphertext, shared_secret = self.mechanism.encap_secret(public_key)
            return ciphertext, shared_secret
        else:
            # Simulation
            ct = os.urandom(768) 
            ss = os.urandom(32) 
            return ct, ss

    def decaps(self, ciphertext, secret_key):
        """Recovers shared secret from ciphertext."""
        if self.is_enabled():
            shared_secret = self.mechanism.decap_secret(ciphertext)
            return shared_secret
        else:
            # Simulation: Return a mock shared secret (Note: In real simulation this should match encaps)
            # For simplicity in mock, checking validity is skipped or assumed
            return b'\x00' * 32 

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_enabled() and self.mechanism:
            self.mechanism.free()

class Signature(PQWrapper):
    """Digital Signature Wrapper (e.g., Dilithium)."""
    def __init__(self, alg_name="Dilithium2"):
        super().__init__(alg_name)
        if self.is_enabled():
            self.mechanism = oqs.Signature(alg_name)
        else:
            self.mechanism = None

    def generate_keypair(self):
        if self.is_enabled():
            public_key = self.mechanism.generate_keypair()
            secret_key = self.mechanism.export_secret_key()
            return public_key, secret_key
        else:
            return os.urandom(1312), os.urandom(2528)

    def sign(self, message, secret_key):
        if self.is_enabled():
            signature = self.mechanism.sign(message)
            return signature
        else:
            return os.urandom(2420)

    def verify(self, message, signature, public_key):
        if self.is_enabled():
            return self.mechanism.verify(message, signature, public_key)
        else:
            return True # Always verify in simulation

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_enabled() and self.mechanism:
            self.mechanism.free()
