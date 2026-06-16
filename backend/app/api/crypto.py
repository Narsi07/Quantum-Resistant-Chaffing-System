"""
Crypto API — post-quantum key management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..models.user import User
from ..schemas.crypto import KeyGenerateRequest, CryptoKeyResponse
from ..middleware.auth import get_current_user
from ..services import crypto_service

router = APIRouter(prefix="/api/crypto", tags=["Cryptography"])

SUPPORTED_ALGORITHMS = ["Kyber512", "Kyber768", "Kyber1024", "Dilithium2", "Dilithium3"]


@router.get("/keys", response_model=List[CryptoKeyResponse])
async def list_keys(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all cryptographic keys for the current user."""
    keys = await crypto_service.list_keys(db, str(current_user.id), active_only=active_only)
    return keys


@router.post(
    "/keys/generate",
    response_model=List[CryptoKeyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_keys(
    request: KeyGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a new post-quantum keypair.

    Supported algorithms:
    - **Kyber512** — Key Encapsulation Mechanism (NIST PQC standard)
    - **Kyber768** — Higher security KEM
    - **Dilithium2** — Digital signature scheme (NIST PQC standard)
    - **Dilithium3** — Higher security signatures

    The secret key is encrypted with Fernet before storage.
    Only public key bytes are ever returned to the client.
    """
    if request.algorithm not in SUPPORTED_ALGORITHMS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported algorithm. Choose from: {SUPPORTED_ALGORITHMS}",
        )
    try:
        keys = await crypto_service.generate_keypair(
            db, str(current_user.id), algorithm=request.algorithm
        )
        return keys
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/keys/{key_id}/public")
async def export_public_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export a public key as raw bytes (for sharing with peers).
    Only kem_public and sig_public keys can be exported.
    """
    key_bytes = await crypto_service.get_public_key_bytes(
        db, key_id, str(current_user.id)
    )
    if key_bytes is None:
        raise HTTPException(
            status_code=404,
            detail="Key not found, not yours, or is a secret key (cannot export)",
        )
    return Response(
        content=key_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=public_key_{key_id[:8]}.bin"},
    )


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke (deactivate) a cryptographic key."""
    ok = await crypto_service.revoke_key(db, key_id, str(current_user.id))
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found or not yours")
