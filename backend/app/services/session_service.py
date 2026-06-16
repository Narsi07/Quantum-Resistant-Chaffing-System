"""
Session service — manages traffic session lifecycle and packet logging.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.session import TrafficSession, PacketLog

logger = logging.getLogger(__name__)


async def create_session(
    db: AsyncSession,
    user_id: str,
    session_name: Optional[str] = None,
    config: Optional[dict] = None,
) -> TrafficSession:
    """Create a new traffic session record in the database."""
    session = TrafficSession(
        user_id=user_id,
        session_name=session_name or f"Session-{datetime.now().strftime('%H%M%S')}",
        config=config or {},
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(f"Session created: {session.id} ({session.session_name})")
    return session


async def stop_session(db: AsyncSession, session_id: str) -> Optional[TrafficSession]:
    """Mark a session as stopped and record end time."""
    result = await db.execute(
        select(TrafficSession).where(TrafficSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return None

    session.ended_at = datetime.now(timezone.utc)
    session.status = "stopped"
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Optional[TrafficSession]:
    """Fetch a session by ID."""
    result = await db.execute(
        select(TrafficSession).where(TrafficSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TrafficSession]:
    """List sessions, optionally filtered by user."""
    q = select(TrafficSession).order_by(TrafficSession.started_at.desc())
    if user_id:
        q = q.where(TrafficSession.user_id == user_id)
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return list(result.scalars().all())


async def log_packet(
    db: AsyncSession,
    session_id: str,
    packet_type: str,
    size_bytes: int,
    iat_ms: Optional[float] = None,
    path_id: Optional[int] = None,
    metadata: Optional[dict] = None,
):
    """Append a single packet record to packet_logs."""
    pkt = PacketLog(
        session_id=session_id,
        packet_type=packet_type,
        size_bytes=size_bytes,
        iat_ms=iat_ms,
        path_id=path_id,
        encrypted=True,
        extra_meta=metadata or {},
    )
    db.add(pkt)

    # Update session aggregates
    await db.execute(
        update(TrafficSession)
        .where(TrafficSession.id == session_id)
        .values(
            total_packets=TrafficSession.total_packets + 1,
            total_bytes=TrafficSession.total_bytes + size_bytes,
            real_packets=TrafficSession.real_packets + (1 if packet_type == "real" else 0),
            dummy_packets=TrafficSession.dummy_packets + (1 if packet_type == "dummy" else 0),
        )
    )
    await db.commit()


async def get_packet_logs(
    db: AsyncSession,
    session_id: str,
    limit: int = 100,
    offset: int = 0,
) -> list[PacketLog]:
    """Fetch packet logs for a session."""
    result = await db.execute(
        select(PacketLog)
        .where(PacketLog.session_id == session_id)
        .order_by(PacketLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
