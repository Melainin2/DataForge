"""Session-based short-term conversation memory (in-memory).

The ``ConversationManager`` stores recent messages per session and keeps the
context window bounded so LLM latency / token usage stays low. It is the
session layer the Agent reads from and writes to.

This is intentionally a lightweight, framework-free implementation. A
persistent store / checkpointer (e.g. SQLite or a vector index) can replace
this class later without changing the ``VoiceAgent`` interface.
"""

from __future__ import annotations

from collections import OrderedDict

from app.agent.types import Conversation, Message


class ConversationManager:
    def __init__(self, *, max_sessions: int = 1000, max_messages: int = 24) -> None:
        self._sessions: OrderedDict[str, Conversation] = OrderedDict()
        self._max_sessions = max_sessions
        self._max_messages = max_messages

    # -- retrieval ---------------------------------------------------------

    def get(self, session_id: str) -> Conversation | None:
        conv = self._sessions.get(session_id)
        if conv is not None:
            self._sessions.move_to_end(session_id)
        return conv

    def get_or_create(self, session_id: str) -> Conversation:
        conv = self.get(session_id)
        if conv is None:
            conv = Conversation(session_id=session_id)
            self._sessions[session_id] = conv
            self._evict_if_needed()
        return conv

    def messages(self, session_id: str, *, limit: int | None = None) -> list[Message]:
        conv = self.get(session_id)
        if conv is None:
            return []
        msgs = conv.messages
        if limit is not None and limit < len(msgs):
            msgs = msgs[-limit:]
        return list(msgs)

    # -- writes ------------------------------------------------------------

    def add_message(self, session_id: str, role: str, content: str) -> Conversation:
        conv = self.get_or_create(session_id)
        conv.messages.append(Message(role=role, content=content))
        # Bound the context window: drop the oldest turns beyond the cap.
        if len(conv.messages) > self._max_messages:
            del conv.messages[: len(conv.messages) - self._max_messages]
        return conv

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def clear_all(self) -> None:
        self._sessions.clear()

    def count(self) -> int:
        return len(self._sessions)

    def _evict_if_needed(self) -> None:
        while len(self._sessions) > self._max_sessions:
            self._sessions.popitem(last=False)