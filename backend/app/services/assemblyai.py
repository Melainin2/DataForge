"""Real-time speech-to-text clients for the AssemblyAI Universal-Streaming (v3) API.

Part 1 ships two interchangeable clients behind the same interface:

* ``AssemblyAIRealtimeClient`` — streams PCM16 audio to the real
  ``wss://streaming.assemblyai.com/v3/ws`` endpoint and relays partial/final
  turns as events.
* ``MockAssemblyAIRealtimeClient`` — a deterministic fake used for local
  development and tests when no API key is available (``STT_MODE=mock``).

Wire protocol (verified against the official AssemblyAI docs, 2026):
server messages are JSON with ``type`` in {Begin, SpeechStarted, Turn,
Termination}; a ``Turn`` with ``end_of_turn=false`` is a partial transcript,
``end_of_turn=true`` is final. The client must send ``{"type": "Terminate"}``
before closing to flush the final transcript.
"""

from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from typing import Optional

import websockets

from app.config import Settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RealtimeEvent:
    """Event emitted by an STT client, consumed by the WebSocket relay."""

    kind: str  # connected | partial | final | session_closed | error
    text: str = ""
    message: str = ""
    data: dict = field(default_factory=dict)


class AssemblyAIRealtimeClient:
    """Thin async wrapper over the AssemblyAI Universal-Streaming WebSocket."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.events: asyncio.Queue[RealtimeEvent] = asyncio.Queue()
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._recv_task: Optional[asyncio.Task] = None
        self._closed = False

    async def connect(self) -> None:
        if self._ws is not None:
            raise RuntimeError("assemblyai client already connected")
        if not self._settings.assemblyai_api_key:
            raise RuntimeError("ASSEMBLYAI_API_KEY is not configured")
        try:
            ws = await websockets.connect(
                self._settings.streaming_ws_url,
                additional_headers={"Authorization": self._settings.assemblyai_api_key},
                max_size=2**20,
                open_timeout=10,
            )
        except Exception as exc:  # handshake refused (bad key, network, 401/403/410…)
            logger.error("assemblyai connect failed: %s", exc)
            self.events.put_nowait(RealtimeEvent("error", message=f"assemblyai_connection_failed: {exc}"))
            raise
        self._ws = ws
        self._recv_task = asyncio.create_task(self._recv_loop())
        self.events.put_nowait(RealtimeEvent("connected"))
        logger.info("assemblyai session connected")

    async def send_audio(self, data: bytes) -> None:
        if self._ws is None or self._ws.closed:
            return
        try:
            await self._ws.send(data)
        except Exception as exc:
            self.events.put_nowait(RealtimeEvent("error", message=f"audio_send_failed: {exc}"))

    async def send_agent_context(self, text: str) -> None:
        """Biases recognition toward the agent's last reply (UpdateConfiguration)."""
        if self._ws is None or self._ws.closed:
            return
        await self._ws.send(json.dumps({"type": "UpdateConfiguration", "agent_context": text}))

    async def _recv_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("non-json assemblyai message ignored")
                    continue
                msg_type = msg.get("type")
                if msg_type == "Turn":
                    final = bool(msg.get("end_of_turn"))
                    kind = "final" if final else "partial"
                    self.events.put_nowait(RealtimeEvent(kind, text=msg.get("transcript", ""), data=msg))
                    if final:
                        logger.info("final transcript: %s", msg.get("transcript", "")[:120])
                elif msg_type == "Termination":
                    self._closed = True
                    self.events.put_nowait(RealtimeEvent("session_closed"))
                    break
                elif msg_type in ("Begin", "SpeechStarted"):
                    logger.debug("assemblyai %s message ignored", msg_type)
                elif msg_type == "error":
                    self.events.put_nowait(RealtimeEvent("error", message=f"assemblyai_api_error: {msg}"))
                    break
        except Exception as exc:
            if not self._closed:
                logger.error("assemblyai receive loop ended: %s", exc)
                self.events.put_nowait(RealtimeEvent("error", message=f"assemblyai_stream_error: {exc}"))
        finally:
            self._closed = True

    async def close(self) -> None:
        """Send Terminate (required to flush the final transcript) and close."""
        if self._ws is not None and not self._ws.closed:
            try:
                await self._ws.send(json.dumps({"type": "Terminate"}))
            except Exception:
                pass
            # Give the server a moment to flush the final transcript (Termination).
            if self._recv_task is not None:
                try:
                    await asyncio.wait_for(asyncio.shield(self._recv_task), timeout=2.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
        if self._ws is not None and not self._ws.closed:
            try:
                await self._ws.close()
            except Exception:
                pass
        if self._recv_task is not None and not self._recv_task.done():
            self._recv_task.cancel()
            try:
                await self._recv_task
            except (asyncio.CancelledError, Exception):
                pass
        self._closed = True
        logger.info("assemblyai session closed")


def decode_pcm16(base64_payload: str) -> bytes:
    """Decode and validate a base64 PCM16 payload (raises ValueError on bad input)."""
    if not base64_payload:
        raise ValueError("empty audio payload")
    data = base64.b64decode(base64_payload, validate=True)
    if not data or len(data) % 2 != 0:
        raise ValueError("audio payload must be PCM16 (even byte count)")
    return data


class MockAssemblyAIRealtimeClient:
    """Deterministic fake used with STT_MODE=mock (dev/tests, no network)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.events: asyncio.Queue[RealtimeEvent] = asyncio.Queue()
        self._received_bytes = 0
        self._closed = False

    async def connect(self) -> None:
        self.events.put_nowait(RealtimeEvent("connected"))
        logger.info("mock assemblyai session connected")

    async def send_audio(self, data: bytes) -> None:
        self._received_bytes += len(data)
        if self._received_bytes // 32000 == 1:
            self.events.put_nowait(RealtimeEvent("partial", text="Hello"))
        elif self._received_bytes // 32000 == 2:
            self.events.put_nowait(RealtimeEvent("partial", text="Hello there"))

    async def send_agent_context(self, text: str) -> None:
        return

    async def close(self) -> None:
        if self._closed:
            return
        if self._received_bytes > 0:
            self.events.put_nowait(RealtimeEvent("final", text="Hello there, how can I help you?"))
        self._closed = True
        self.events.put_nowait(RealtimeEvent("session_closed"))
        logger.info("mock assemblyai session closed")


def build_client(settings: Settings):
    """Factory selecting the real or mock STT client based on STT_MODE."""
    if settings.stt_mode == "mock":
        return MockAssemblyAIRealtimeClient(settings)
    return AssemblyAIRealtimeClient(settings)