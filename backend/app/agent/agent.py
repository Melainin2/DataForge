"""The Voice Agent: the intelligence layer of the DataForge voice system.

Flow::

    User transcript
         |
         v
    VoiceAgent.process(transcript, session_id)
         |
         +--> ConversationManager  (append user message, read bounded history)
         |
         v
    LLMProvider (abstraction, e.g. Groq)
         |
         v
    response appended to memory + returned

Errors are raised to the caller (WebSocket router), which maps them to a
natural, user-safe fallback message. The agent never leaks provider details.
"""

from __future__ import annotations

import re
from typing import Optional

from app.agent.llm import LLMProvider, LLMProviderError
from app.agent.memory import ConversationManager
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.types import ActionItem, AgentTurnResult
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Below this AssemblyAI end-of-turn confidence, the transcript is treated as
# "possibly misheard": the agent asks the user to confirm instead of acting
# on it. Chosen from AssemblyAI's own guidance that turns above ~0.6 are
# reliably formatted; anything lower is worth a cheap human confirmation
# rather than a wrong action.
LOW_CONFIDENCE_THRESHOLD = 0.55

# Keyword -> category heuristics for lifting a structured action item out of
# an already-trusted (high confidence) utterance. Intentionally simple and
# deterministic: no extra LLM round-trip, works identically in mock mode, and
# is what turns "a chatbot that talks" into "a voice agent that produces
# reviewable work" (support tickets / bookings / tasks / order lookups).
_ACTION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("booking", ("book", "schedule", "appointment", "reserve", "reservation")),
    ("support_ticket", ("broken", "issue", "problem", "not working", "doesn't work", "fix", "bug", "leak", "error")),
    ("order", ("order", "refund", "return", "shipment", "delivery", "package", "tracking")),
    ("task", ("remind me", "todo", "to-do", "need to", "don't forget", "add a task")),
)


def extract_action_item(text: str) -> Optional[ActionItem]:
    """Best-effort structured task extraction from a trusted transcript."""
    lower = text.lower()
    for category, keywords in _ACTION_PATTERNS:
        if any(keyword in lower for keyword in keywords):
            title = re.sub(r"\s+", " ", text).strip().rstrip(".!?")
            if len(title) > 80:
                title = title[:77].rstrip() + "..."
            if title:
                title = title[0].upper() + title[1:]
            return ActionItem(title=title, category=category)
    return None


class AgentError(Exception):
    """Base agent error."""


class EmptyTranscriptError(AgentError):
    """Raised when the agent is asked to process a blank transcript."""


class VoiceAgent:
    def __init__(
        self,
        llm: LLMProvider,
        memory: Optional[ConversationManager] = None,
        system_prompt: str = SYSTEM_PROMPT,
        context_limit: Optional[int] = None,
    ) -> None:
        self._llm = llm
        self._memory = memory or ConversationManager()
        self._system_prompt = system_prompt
        self._context_limit = context_limit

    @property
    def memory(self) -> ConversationManager:
        return self._memory

    async def process(self, transcript: str, *, session_id: str) -> str:
        """Handle one completed user turn and return the agent's reply."""
        text = (transcript or "").strip()
        if not text:
            raise EmptyTranscriptError("cannot process an empty transcript")

        self._memory.add_message(session_id, "user", text)
        logger.info("agent invoked: session=%s text=%r", session_id, text[:120])

        messages = [{"role": "system", "content": self._system_prompt}]
        messages.extend(m.to_llm() for m in self._memory.messages(session_id, limit=self._context_limit))

        response = (await self._llm.complete(messages)).strip()
        if not response:
            raise LLMProviderError("llm returned an empty response")

        self._memory.add_message(session_id, "assistant", response)
        return response

    async def process_turn(
        self,
        transcript: str,
        *,
        session_id: str,
        confidence: Optional[float] = None,
    ) -> AgentTurnResult:
        """Full turn pipeline: trust-gate on STT confidence, then reply.

        Low-confidence turns (a likely mishearing) never reach the LLM as a
        command to act on — the transcript is recorded for context, but the
        agent asks the user to confirm instead of guessing. High-confidence
        turns get the normal reply *plus* a best-effort structured action
        item, so a spoken request also produces something reviewable.
        """
        text = (transcript or "").strip()
        if not text:
            raise EmptyTranscriptError("cannot process an empty transcript")

        if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
            self._memory.add_message(session_id, "user", text)
            clarification = (
                f'I only caught part of that clearly — did you say "{text}"? '
                "Please confirm or say it again."
            )
            self._memory.add_message(session_id, "assistant", clarification)
            logger.info(
                "low-confidence turn gated: session=%s confidence=%.2f", session_id, confidence
            )
            return AgentTurnResult(reply=clarification, needs_confirmation=True, confidence=confidence)

        reply = await self.process(text, session_id=session_id)
        action_item = extract_action_item(text)
        if action_item:
            logger.info(
                "action item extracted: session=%s category=%s", session_id, action_item.category
            )
        return AgentTurnResult(reply=reply, action_item=action_item, confidence=confidence)

    def clear_session(self, session_id: str) -> None:
        self._memory.clear(session_id)

    async def aclose(self) -> None:
        try:
            await self._llm.aclose()
        except Exception:
            pass