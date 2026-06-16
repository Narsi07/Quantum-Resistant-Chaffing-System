"""
Sessions API — full CRUD for traffic obfuscation sessions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..schemas.session import SessionCreate, SessionResponse, PacketLogResponse
from ..middleware.auth import get_current_user
from ..services import session_service

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all traffic sessions for the current user."""
    sessions = await session_service.list_sessions(
        db, user_id=str(current_user.id), limit=limit, offset=offset
    )
    return sessions


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new traffic session."""
    session = await session_service.create_session(
        db,
        user_id=str(current_user.id),
        session_name=data.session_name,
        config=data.config,
    )
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details for a specific session."""
    session = await session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")
    return session


@router.delete("/{session_id}", response_model=SessionResponse)
async def stop_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop and archive a session."""
    existing = await session_service.get_session(db, session_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(existing.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    stopped = await session_service.stop_session(db, session_id)
    return stopped


@router.get("/{session_id}/packets", response_model=list[PacketLogResponse])
async def get_packet_logs(
    session_id: str,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve paginated packet logs for a session."""
    existing = await session_service.get_session(db, session_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(existing.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    logs = await session_service.get_packet_logs(db, session_id, limit=limit, offset=offset)
    return logs
