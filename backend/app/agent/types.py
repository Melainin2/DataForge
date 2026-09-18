"""Agent intelligence layer: turns final transcripts into assistant replies.

Domain model used by the voice agent. Kept framework-free so the memory
backend can be swapped for a persistent checkpointer later without touching
the rest of the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

Role = str  # "system" | "user" | "assistant"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    """A single conversational turn."""

    role: Role
    content: str
    timestamp: str = field(default_factory=_utcnow)

    def to_llm(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    """Short-term conversation context bound to one session."""

    session_id: str
    messages: list[Message] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class ActionItem:
    """A structured task/ticket lifted from a high-confidence user turn."""

    title: str
    category: str


@dataclass
class AgentTurnResult:
    """Everything one completed user turn produces for the caller."""

    reply: str
    needs_confirmation: bool = False
    action_item: Optional[ActionItem] = None
    confidence: Optional[float] = None