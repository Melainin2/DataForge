"""WebSocket router: streams browser mic audio to AssemblyAI and relays
transcripts + agent replies + state back to the browser.

Browser -> Backend:  start_session | audio (base64 PCM16) | stop_session | ping
Backend -> Browser:  state | partial | final | agent_message | session_closed |
                     error | pong

Agent pipeline (Part 2): when the STT client emits a *final* transcript (a
completed user turn, end_of_turn=true) the backend runs the Agent against the
session's conversation and streams the reply back as an ``agent_message``,
driving the UI through PROCESSING -> THINKING -> LISTENING.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent import (
    AGENT_UNSET_MSG,
    FALLBACK_REPLY,
    AgentTurnResult,
    LLMError,
    VoiceAgent,
)
from app.config import Settings
from app.models.ws import (
    ClientMessage,
    make_agent_message,
    make_error,
    make_final,
    make_partial,
    make_state,
)
from app.services.assemblyai import build_client, decode_pcm16
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["voice"])


def _settings(websocket: WebSocket) -> Settings:
    return websocket.app.state.settings


def _agent(websocket: WebSocket) -> Optional[VoiceAgent]:
    return websocket.app.state.agent


async def _send(websocket: WebSocket, payload: dict) -> None:
    try:
        await websocket.send_json(payload)
    except (WebSocketDisconnect, RuntimeError):
        pass


async def _run_agent_turn(
    websocket: WebSocket,
    settings: Settings,
    session_id: str,
    text: str,
    confidence: Optional[float] = None,
) -> None:
    """Turn the final transcript into an agent reply with clean UI states."""
    agent = _agent(websocket)
    if agent is None:
        logger.warning("agent unavailable (%s)", AGENT_UNSET_MSG)
        return

    await _send(websocket, make_state("PROCESSING"))
    await _send(websocket, make_state("THINKING"))
    started = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            agent.process_turn(text, session_id=session_id, confidence=confidence),
            timeout=settings.llm_timeout_seconds + 10,
        )
    except (asyncio.TimeoutError, LLMError) as exc:
        logger.error("agent turn failed: %s", exc)
        result = AgentTurnResult(reply=FALLBACK_REPLY)
    except Exception as exc:  # never expose provider internals to the browser
        logger.error("agent turn crashed: %s", exc, exc_info=True)
        result = AgentTurnResult(reply=FALLBACK_REPLY)

    action_item_payload = asdict(result.action_item) if result.action_item else None
    await _send(
        websocket,
        make_agent_message(
            result.reply,
            needs_confirmation=result.needs_confirmation,
            action_item=action_item_payload,
        ),
    )
    await _send(websocket, make_state("LISTENING"))
    logger.info("agent reply sent: session=%s latency_ms=%.0f", session_id, (time.perf_counter() - started) * 1000)


async def _relay_events(websocket: WebSocket, client, settings: Settings, session_id: str) -> None:
    """Forward STT client events to the browser; run the agent on final turns."""
    while True:
        event = await client.events.get()
        if event.kind == "connected":
            logger.info("session relay started: session=%s", session_id)
        elif event.kind == "partial":
            await _send(websocket, make_partial(event.text))
        elif event.kind == "final":
            confidence = event.data.get("end_of_turn_confidence") if event.data else None
            await _send(websocket, make_final(event.text, confidence))
            text = (event.text or "").strip()
            if text:
                logger.info("final transcript received: session=%s text=%r", session_id, text[:120])
                await _run_agent_turn(websocket, settings, session_id, text, confidence)
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
    session_id = str(uuid4())
    logger.info("voice websocket connected: session=%s", session_id)
    await _send(websocket, {"type": "connected", "session_id": session_id})

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
                relay_task = asyncio.create_task(_relay_events(websocket, client, settings, session_id))
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
        logger.info("voice websocket disconnected: session=%s", session_id)
    except Exception as exc:  # never let an unexpected failure kill the server
        logger.error("voice websocket crashed: %s", exc)
        await _send(websocket, make_error("internal", "unexpected server error"))
    finally:
        if client is not None:
            await _close_client(client)
        if relay_task is not None:
            relay_task.cancel()
        logger.info("voice websocket closed: session=%s", session_id)