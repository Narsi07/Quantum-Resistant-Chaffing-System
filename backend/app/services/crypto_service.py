"""
Crypto service — manages post-quantum key generation and storage.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.crypto import CryptoKey
from ..utils.security import encrypt_key_data, decrypt_key_data

logger = logging.getLogger(__name__)

# Add project root to sys.path so 'src' is importable
# Path: backend/app/services/crypto_service.py -> up 3 = project root
import sys, os
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.crypto.pq_wrapper import KEM, Signature


async def generate_keypair(
    db: AsyncSession,
    user_id: str,
    algorithm: str = "Kyber512",
) -> list[CryptoKey]:
    """
    Generate a post-quantum keypair, encrypt the keys, and store in DB.

    For KEM algorithms (Kyber*): stores kem_public and kem_secret
    For Signature algorithms (Dilithium*): stores sig_public and sig_secret

    Returns list of created CryptoKey records.
    """
    # Deactivate existing keys of same algorithm for this user
    await db.execute(
        update(CryptoKey)
        .where(CryptoKey.user_id == user_id, CryptoKey.algorithm == algorithm)
        .values(is_active=False)
    )

    created = []

    if "Kyber" in algorithm or "kyber" in algorithm.lower():
        kem = KEM(algorithm)
        pub_key, sec_key = kem.generate_keypair()

        for key_type, raw in [("kem_public", pub_key), ("kem_secret", sec_key)]:
            encrypted = encrypt_key_data(raw)
            record = CryptoKey(
                user_id=user_id,
                key_type=key_type,
                algorithm=algorithm,
                key_data=encrypted,
                is_active=True,
            )
            db.add(record)
            created.append(record)

    elif "Dilithium" in algorithm:
        sig = Signature(algorithm)
        pub_key, sec_key = sig.generate_keypair()

        for key_type, raw in [("sig_public", pub_key), ("sig_secret", sec_key)]:
            encrypted = encrypt_key_data(raw)
            record = CryptoKey(
                user_id=user_id,
                key_type=key_type,
                algorithm=algorithm,
                key_data=encrypted,
                is_active=True,
            )
            db.add(record)
            created.append(record)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use Kyber512 or Dilithium2.")

    await db.commit()
    for r in created:
        await db.refresh(r)

    logger.info(f"Generated {algorithm} keypair for user {user_id} | PQ={'real' if KEM().is_enabled() else 'simulation'}")
    return created


async def list_keys(
    db: AsyncSession,
    user_id: str,
    active_only: bool = True,
) -> list[CryptoKey]:
    """List a user's crypto keys (metadata only — no raw key material returned)."""
    q = select(CryptoKey).where(CryptoKey.user_id == user_id)
    if active_only:
        q = q.where(CryptoKey.is_active == True)
    q = q.order_by(CryptoKey.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_public_key_bytes(
    db: AsyncSession,
    key_id: str,
    user_id: str,
) -> Optional[bytes]:
    """
    Return the decrypted public key bytes for a given key record.
    Only returns public keys (kem_public or sig_public) — never secret keys.
    """
    result = await db.execute(
        select(CryptoKey).where(
            CryptoKey.id == key_id,
            CryptoKey.user_id == user_id,
            CryptoKey.key_type.in_(["kem_public", "sig_public"]),
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        return None
    return decrypt_key_data(key.key_data)


async def revoke_key(db: AsyncSession, key_id: str, user_id: str) -> bool:
    """Deactivate (revoke) a key."""
    result = await db.execute(
        select(CryptoKey).where(CryptoKey.id == key_id, CryptoKey.user_id == user_id)
    )
    key = result.scalar_one_or_none()
    if not key:
        return False
    key.is_active = False
    await db.commit()
    return True
