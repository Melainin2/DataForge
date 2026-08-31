"""WebSocket router: streams browser mic audio to AssemblyAI and relays
transcripts + agent state back to the browser.

Browser -> Backend:  start_session | audio (base64 PCM16) | stop_session | ping
Backend -> Browser:  state | partial | final | session_closed | error | pong
"""

from __future__ import annotations

import asyncio
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import Settings
from app.models.ws import ClientMessage, make_error, make_final, make_partial, make_state
from app.services.assemblyai import build_client, decode_pcm16
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["voice"])


def _settings(websocket: WebSocket) -> Settings:
    return websocket.app.state.settings


async def _send(websocket: WebSocket, payload: dict) -> None:
    try:
        await websocket.send_json(payload)
    except (WebSocketDisconnect, RuntimeError):
        pass


async def _relay_events(websocket: WebSocket, client) -> None:
    """Forward STT client events to the browser until the session ends."""
    while True:
        event = await client.events.get()
        if event.kind == "connected":
            logger.info("session relay started")
        elif event.kind == "partial":
            await _send(websocket, make_partial(event.text))
        elif event.kind == "final":
            await _send(websocket, make_final(event.text))
        elif event.kind == "session_closed":
            await _send(websocket, {"type": "session_closed"})
            break
        elif event.kind == "error":
            await _send(websocket, make_error("assemblyai_error", event.message))
            break


async def _close_client(client) -> None:
    try:
        await client.close()
    except Exception:
        pass


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    settings = _settings(websocket)
    logger.info("voice websocket connected")
    await _send(websocket, {"type": "connected", "session_id": str(uuid4())})

    client = None
    relay_task: Optional[asyncio.Task] = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = ClientMessage.model_validate_json(raw)
            except Exception as exc:
                await _send(websocket, make_error("invalid_message", f"malformed message: {exc}"))
                continue

            if message.type == "ping":
                await _send(websocket, {"type": "pong"})

            elif message.type == "start_session":
                if client is not None:
                    await _send(websocket, make_error("session_active", "a voice session is already active"))
                    continue
                client = build_client(settings)
                try:
                    await client.connect()
                except Exception as exc:
                    await _send(websocket, make_error("assemblyai_error", f"cannot start session: {exc}"))
                    client = None
                    continue
                relay_task = asyncio.create_task(_relay_events(websocket, client))
                await _send(websocket, make_state("LISTENING"))

            elif message.type == "audio":
                if client is None:
                    await _send(websocket, make_error("not_listening", "start a session before sending audio"))
                    continue
                try:
                    payload = decode_pcm16(message.data)
                except ValueError as exc:
                    await _send(websocket, make_error("invalid_audio", str(exc)))
                    continue
                if len(payload) > settings.max_audio_frame_bytes:
                    await _send(websocket, make_error("invalid_audio", "audio frame too large"))
                    continue
                await client.send_audio(payload)

            elif message.type == "stop_session":
                if client is not None:
                    await _close_client(client)
                    if relay_task is not None:
                        await relay_task
                client = None
                relay_task = None
                await _send(websocket, make_state("IDLE"))

    except WebSocketDisconnect:
        logger.info("voice websocket disconnected")
    except Exception as exc:  # never let an unexpected failure kill the server
        logger.error("voice websocket crashed: %s", exc)
        await _send(websocket, make_error("internal", "unexpected server error"))
    finally:
        if client is not None:
            await _close_client(client)
        if relay_task is not None:
            relay_task.cancel()
        logger.info("voice websocket closed")