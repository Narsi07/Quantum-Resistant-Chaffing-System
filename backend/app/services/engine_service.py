"""
Engine service — singleton manager for ObfuscationEngine instances.

One engine runs per active session. Supports WebSocket broadcasting
of live packet statistics to connected clients.
"""
import asyncio
import logging
import threading
from typing import Optional, Dict, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

import sys, os
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.obfuscation.engine import ObfuscationEngine
from src.adversarial.discriminator import AdversarialEvaluator


@dataclass
class EngineInstance:
    engine: ObfuscationEngine
    evaluator: AdversarialEvaluator
    session_id: str
    websocket_clients: Set = field(default_factory=set)
    loop: Optional[asyncio.AbstractEventLoop] = None


class EngineManager:
    """
    Thread-safe singleton that manages running ObfuscationEngine instances.
    One instance per session_id.
    """
    _instances: Dict[str, EngineInstance] = {}
    _lock = threading.Lock()

    @classmethod
    def start_engine(cls, session_id: str, config: Optional[dict] = None) -> dict:
        """Start a new engine for the given session."""
        with cls._lock:
            if session_id in cls._instances:
                return {"status": "already_running", "session_id": session_id}

            evaluator = AdversarialEvaluator()

            def on_packet(payload: bytes, meta: dict):
                """Callback: receives every packet from the engine."""
                # Update GAN evaluator
                evaluator.add_packet(
                    size=meta["size"],
                    iat_ms=meta["iat_ms"],
                    is_dummy=meta["is_dummy"],
                )
                meta["discriminability"] = evaluator.get_discriminability()

                # Broadcast to WebSocket clients (non-blocking)
                instance = cls._instances.get(session_id)
                if instance and instance.websocket_clients and instance.loop:
                    import json
                    msg = json.dumps({
                        "type": "packet",
                        "data": {
                            "is_dummy": meta["is_dummy"],
                            "size": meta["size"],
                            "entropy": meta["entropy"],
                            "iat_ms": meta["iat_ms"],
                            "path_id": meta["path_id"],
                            "discriminability": meta["discriminability"],
                            "pq_mode": meta.get("pq_mode", "simulation"),
                        }
                    })
                    dead_clients = set()
                    for ws in list(instance.websocket_clients):
                        try:
                            asyncio.run_coroutine_threadsafe(
                                ws.send_text(msg), instance.loop
                            )
                        except Exception:
                            dead_clients.add(ws)
                    instance.websocket_clients -= dead_clients

            engine = ObfuscationEngine(output_callback=on_packet)
            instance = EngineInstance(
                engine=engine,
                evaluator=evaluator,
                session_id=session_id,
            )
            cls._instances[session_id] = instance
            engine.start()

            logger.info(f"Engine started for session {session_id}")
            return {"status": "started", "session_id": session_id}

    @classmethod
    def stop_engine(cls, session_id: str) -> dict:
        """Stop and remove the engine for a session."""
        with cls._lock:
            instance = cls._instances.pop(session_id, None)
            if not instance:
                return {"status": "not_found", "session_id": session_id}
            instance.engine.stop()
            logger.info(f"Engine stopped for session {session_id}")
            return {"status": "stopped", "session_id": session_id, **instance.engine.get_stats()}

    @classmethod
    def get_status(cls, session_id: str) -> dict:
        """Return current engine stats."""
        with cls._lock:
            instance = cls._instances.get(session_id)
            if not instance:
                return {"status": "not_running", "session_id": session_id}
            stats = instance.engine.get_stats()
            stats["discriminability"] = instance.evaluator.get_discriminability()
            stats["status"] = "running"
            stats["session_id"] = session_id
            return stats

    @classmethod
    def list_running(cls) -> list:
        """Return list of all currently running session IDs."""
        with cls._lock:
            return [
                {"session_id": sid, **inst.engine.get_stats()}
                for sid, inst in cls._instances.items()
            ]

    @classmethod
    def register_websocket(cls, session_id: str, ws, loop: asyncio.AbstractEventLoop):
        """Register a WebSocket client for live updates."""
        with cls._lock:
            instance = cls._instances.get(session_id)
            if instance:
                instance.websocket_clients.add(ws)
                instance.loop = loop
                logger.info(f"WebSocket registered for session {session_id}")

    @classmethod
    def unregister_websocket(cls, session_id: str, ws):
        """Remove a WebSocket client."""
        with cls._lock:
            instance = cls._instances.get(session_id)
            if instance:
                instance.websocket_clients.discard(ws)

    @classmethod
    def send_data(cls, session_id: str, data: bytes) -> bool:
        """Send real data through a running engine."""
        with cls._lock:
            instance = cls._instances.get(session_id)
            if not instance:
                return False
            instance.engine.send_data(data)
            return True
