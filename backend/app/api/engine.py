"""
Engine API — start/stop/status + real-time WebSocket streaming.
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..middleware.auth import get_current_user
from ..services.engine_service import EngineManager
from ..services import session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/engine", tags=["Obfuscation Engine"])


class EngineStartRequest(BaseModel):
    session_id: str
    config: Optional[dict] = None


class SendDataRequest(BaseModel):
    session_id: str
    message: str  # Plain text message to send through the obfuscation layer


@router.post("/start")
async def start_engine(
    request: EngineStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start the obfuscation engine for a session.

    The engine will immediately begin sending constant-rate traffic
    (mix of real + AI-generated dummy packets) until stopped.
    """
    # Validate session ownership
    session = await session_service.get_session(db, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")
    if session.status == "stopped":
        session.status = "active"
        session.ended_at = None
        await db.commit()
    elif session.status != "active":
        raise HTTPException(status_code=400, detail=f"Session is {session.status}, not active")

    result = EngineManager.start_engine(request.session_id, config=request.config)
    return result


@router.post("/stop")
async def stop_engine(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop the obfuscation engine for a session."""
    session = await session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your session")

    result = EngineManager.stop_engine(session_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=400, detail="Engine not running for this session")

    # Update session in DB
    await session_service.stop_session(db, session_id)
    return result


@router.get("/status/{session_id}")
async def engine_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get live statistics for a running engine."""
    return EngineManager.get_status(session_id)


@router.get("/running")
async def list_running(
    current_user: User = Depends(get_current_user),
):
    """List all currently running engine sessions."""
    return EngineManager.list_running()


@router.post("/send")
async def send_data(
    request: SendDataRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message through the obfuscation layer.

    The message will be AES-256-GCM encrypted and transmitted
    alongside dummy packets so it is indistinguishable from noise.
    """
    ok = EngineManager.send_data(request.session_id, request.message.encode("utf-8"))
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Engine not running for this session. Start it first.",
        )
    return {"status": "queued", "bytes": len(request.message.encode())}


@router.websocket("/stream/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time packet statistics.

    Connect to: ws://localhost:8000/api/engine/stream/{session_id}

    Each message is a JSON object:
    {
        "type": "packet",
        "data": {
            "is_dummy": bool,
            "size": int,
            "entropy": float,
            "iat_ms": float,
            "path_id": int,
            "discriminability": float,
            "pq_mode": "real" | "simulation"
        }
    }
    """
    await websocket.accept()
    loop = asyncio.get_event_loop()
    EngineManager.register_websocket(session_id, websocket, loop)

    logger.info(f"WebSocket connected for session {session_id}")

    try:
        # Keep alive — wait for client disconnect
        while True:
            try:
                # Wait for ping/pong or any client message
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except asyncio.TimeoutError:
                # Send keepalive stats
                stats = EngineManager.get_status(session_id)
                import json
                await websocket.send_text(json.dumps({"type": "stats", "data": stats}))
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    finally:
        EngineManager.unregister_websocket(session_id, websocket)
