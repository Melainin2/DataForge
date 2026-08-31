from typing import Literal

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


def make_final(text: str) -> dict:
    return {"type": "final", "text": text}


def make_error(code: str, message: str) -> dict:
    return {"type": "error", "code": code, "message": message}