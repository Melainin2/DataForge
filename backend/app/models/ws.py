from typing import Literal, Optional

from pydantic import BaseModel, Field


class ClientMessage(BaseModel):
    """Message sent from the browser to the voice backend."""

    type: Literal["start_session", "audio", "stop_session", "ping"]
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    data: str = Field(default="", description="base64-encoded PCM16 audio for type=audio")


def make_state(state: str) -> dict:
    return {"type": "state", "state": state}


def make_partial(text: str) -> dict:
    return {"type": "partial", "text": text}


def make_final(text: str, confidence: Optional[float] = None) -> dict:
    payload: dict = {"type": "final", "text": text}
    if confidence is not None:
        payload["confidence"] = round(confidence, 3)
    return payload


def make_agent_message(
    text: str,
    *,
    needs_confirmation: bool = False,
    action_item: Optional[dict] = None,
) -> dict:
    payload: dict = {"type": "agent_message", "text": text}
    if needs_confirmation:
        payload["needs_confirmation"] = True
    if action_item is not None:
        payload["action_item"] = action_item
    return payload


def make_error(code: str, message: str) -> dict:
    return {"type": "error", "code": code, "message": message}