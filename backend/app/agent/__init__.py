"""Agent intelligence layer (Part 2)."""

from __future__ import annotations

from app.agent.agent import AgentError, EmptyTranscriptError, VoiceAgent
from app.agent.llm import (
    LLMConnectionError,
    LLMError,
    LLMInvalidKeyError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    build_llm,
)
from app.agent.memory import ConversationManager
from app.agent.prompts import AGENT_UNSET_MSG, FALLBACK_REPLY, SYSTEM_PROMPT
from app.agent.types import ActionItem, AgentTurnResult

__all__ = [
    "AGENT_UNSET_MSG",
    "ActionItem",
    "AgentError",
    "AgentTurnResult",
    "ConversationManager",
    "EmptyTranscriptError",
    "FALLBACK_REPLY",
    "LLMConnectionError",
    "LLMError",
    "LLMInvalidKeyError",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "SYSTEM_PROMPT",
    "VoiceAgent",
    "build_llm",
    "create_agent",
]


def create_agent(settings) -> VoiceAgent:
    """Factory used by the application to build the agent from Settings."""
    llm = build_llm(settings)
    memory = ConversationManager(max_messages=settings.max_context_messages)
    return VoiceAgent(llm=llm, memory=memory, context_limit=settings.max_context_messages)