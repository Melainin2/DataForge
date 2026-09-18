"""Tests for the agent intelligence layer: agent loop, memory, context and
LLM error handling.

The mock provider is deterministic, so these tests assert exact prose.
``asyncio.run`` is used directly to avoid depending on pytest-asyncio config.
"""

import asyncio
import base64
import json
import os

import httpx
import pytest

from app.agent.agent import EmptyTranscriptError, VoiceAgent
from app.agent.llm import (
    GROQ_DEFAULT_MODEL,
    LLMInvalidKeyError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    GroqLLMProvider,
    MockLLMProvider,
)
from app.agent.memory import ConversationManager
from app.agent.prompts import FALLBACK_REPLY


def make_agent(*, max_messages: int = 24) -> VoiceAgent:
    return VoiceAgent(llm=MockLLMProvider(), memory=ConversationManager(max_messages=max_messages))


# -- agent basics --------------------------------------------------------------


def test_greeting_returns_agent_reply():
    reply = asyncio.run(make_agent().process("Hello", session_id="s1"))
    assert reply == "Hello! How can I help you?"


def test_agent_remembers_name_across_turns():
    agent = make_agent()
    asyncio.run(agent.process("My name is Ahmed.", session_id="s1"))
    reply = asyncio.run(agent.process("What is my name?", session_id="s1"))
    assert "Ahmed" in reply


def test_agent_uses_context_from_previous_turns():
    agent = make_agent()
    asyncio.run(agent.process("I love machine learning.", session_id="s1"))
    reply = asyncio.run(agent.process("What do I love?", session_id="s1"))
    assert "machine learning" in reply.lower()


def test_agent_isolation_between_sessions():
    agent = make_agent()
    asyncio.run(agent.process("My name is Sara.", session_id="s1"))
    reply = asyncio.run(agent.process("What is my name?", session_id="s2"))
    assert "Sara" not in reply


def test_empty_transcript_raises():
    agent = make_agent()
    with pytest.raises(EmptyTranscriptError):
        asyncio.run(agent.process("   ", session_id="s1"))


def test_missing_session_is_created_on_demand():
    agent = make_agent()
    assert agent.memory.get("unknown") is None
    asyncio.run(agent.process("Hello", session_id="unknown"))
    assert agent.memory.get("unknown") is not None


# -- trust gate + action extraction (process_turn) ------------------------------


def test_low_confidence_turn_asks_for_confirmation_without_calling_llm():
    class ExplodingLLM:
        async def complete(self, messages):
            raise AssertionError("low-confidence turns must not reach the LLM")

        async def aclose(self):
            return None

    agent = VoiceAgent(llm=ExplodingLLM(), memory=ConversationManager())
    result = asyncio.run(
        agent.process_turn("Book a flight to Denver", session_id="s1", confidence=0.4)
    )
    assert result.needs_confirmation is True
    assert result.action_item is None
    assert "Book a flight to Denver" in result.reply
    # The turn is still recorded so context isn't lost on the next attempt.
    assert [m.role for m in agent.memory.messages("s1")] == ["user", "assistant"]


def test_high_confidence_turn_extracts_action_item():
    agent = make_agent()
    result = asyncio.run(
        agent.process_turn("Please book an appointment for tomorrow", session_id="s1", confidence=0.92)
    )
    assert result.needs_confirmation is False
    assert result.action_item is not None
    assert result.action_item.category == "booking"
    assert result.reply  # normal conversational reply still produced


def test_turn_without_actionable_intent_has_no_action_item():
    agent = make_agent()
    result = asyncio.run(agent.process_turn("Hello", session_id="s1", confidence=0.9))
    assert result.action_item is None
    assert result.reply == "Hello! How can I help you?"


def test_missing_confidence_behaves_like_high_confidence():
    agent = make_agent()
    result = asyncio.run(agent.process_turn("My printer is broken", session_id="s1"))
    assert result.needs_confirmation is False
    assert result.action_item is not None
    assert result.action_item.category == "support_ticket"


# -- memory --------------------------------------------------------------------


def test_memory_records_user_and_assistant_messages():
    memory = ConversationManager()
    memory.add_message("s1", "user", "hi")
    memory.add_message("s1", "assistant", "hello!")
    roles = [m.role for m in memory.messages("s1")]
    assert roles == ["user", "assistant"]


def test_memory_trims_oldest_messages():
    memory = ConversationManager(max_messages=4)
    for i in range(6):
        memory.add_message("s1", "user", f"msg-{i}")
    remaining = [m.content for m in memory.messages("s1")]
    assert remaining == ["msg-2", "msg-3", "msg-4", "msg-5"]


def test_memory_clear_and_limit():
    memory = ConversationManager()
    for i in range(5):
        memory.add_message("s1", "user", f"m{i}")
    assert len(memory.messages("s1", limit=2)) == 2
    memory.clear("s1")
    assert memory.messages("s1") == []
    assert memory.count() == 0


def test_memory_evicts_oldest_sessions():
    memory = ConversationManager(max_sessions=2)
    for sid in ("a", "b", "c"):
        memory.add_message(sid, "user", "hi")
    assert memory.get("a") is None
    assert memory.get("b") is not None and memory.get("c") is not None


# -- system prompt -------------------------------------------------------------


def test_system_prompt_is_injected_first():
    """The LLM must see the system prompt as its very first message."""
    captured: dict = {}

    class CapturingLLM:
        async def complete(self, messages):
            captured["messages"] = messages
            return "ok"

        async def aclose(self):
            return None

    agent = VoiceAgent(llm=CapturingLLM(), memory=ConversationManager())
    asyncio.run(agent.process("Hi", session_id="s1"))
    first = captured["messages"][0]
    assert first["role"] == "system"
    assert "voice agent" in first["content"].lower()


# -- Groq provider (httpx MockTransport) ---------------------------------------


def groq_provider(handler, **kwargs):
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return GroqLLMProvider(api_key="gsk_test", client=client, **kwargs)


def test_groq_provider_success_shape():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        assert request.headers["authorization"] == "Bearer gsk_test"
        body = json.loads(request.content)
        assert body["model"] == GROQ_DEFAULT_MODEL
        assert body["messages"][0]["role"] == "system"
        return httpx.Response(200, json={"choices": [{"message": {"content": "Hi!"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 3}})

    provider = groq_provider(handler)
    reply = asyncio.run(provider.complete([{"role": "system", "content": "sys"}]))
    assert reply == "Hi!"


def test_groq_provider_invalid_key():
    def handler(request):  # noqa: ARG001
        return httpx.Response(401, text="unauthorized")

    provider = groq_provider(handler)
    with pytest.raises(LLMInvalidKeyError):
        asyncio.run(provider.complete([]))


def test_groq_provider_rate_limit():
    def handler(request):  # noqa: ARG001
        return httpx.Response(429, text="rate limited")

    provider = groq_provider(handler)
    with pytest.raises(LLMRateLimitError):
        asyncio.run(provider.complete([]))


def test_groq_provider_server_error():
    def handler(request):  # noqa: ARG001
        return httpx.Response(500, text="boom")

    provider = groq_provider(handler)
    with pytest.raises(LLMProviderError):
        asyncio.run(provider.complete([]))


def test_groq_provider_timeout():
    def handler(request):  # noqa: ARG001
        raise httpx.ReadTimeout("connection timed out")

    provider = groq_provider(handler)
    with pytest.raises(LLMTimeoutError):
        asyncio.run(provider.complete([]))


def test_groq_provider_empty_content_is_stripped():
    def handler(request):  # noqa: ARG001
        return httpx.Response(200, json={"choices": [{"message": {"content": "   "}}]})

    provider = groq_provider(handler)
    assert asyncio.run(provider.complete([])) == ""


# -- router integration: agent errors -> natural fallback -----------------------


def _drain(ws, desired_types, max_messages=25):
    seen = []
    for _ in range(max_messages):
        msg = ws.receive_json()
        seen.append(msg)
        if msg["type"] in desired_types:
            break
    return seen


def test_router_maps_llm_error_to_natural_fallback():
    from fastapi.testclient import TestClient

    from app.main import create_app

    class FailingLLM:
        async def complete(self, messages):
            raise LLMRateLimitError("429 rate limit exceeded by provider")

        async def aclose(self):
            return None

    os.environ["STT_MODE"] = "mock"
    os.environ["LLM_MODE"] = "mock"
    app = create_app()
    with TestClient(app) as client:
        app.state.agent = VoiceAgent(llm=FailingLLM(), memory=ConversationManager())
        pcm = base64.b64encode(b"\x00\x00" * 16000).decode()
        with client.websocket_connect("/ws/voice") as ws:
            ws.receive_json()  # connected
            ws.send_json({"type": "start_session"})
            _drain(ws, {"state"})
            ws.send_json({"type": "audio", "data": pcm})
            ws.send_json({"type": "audio", "data": pcm})
            ws.send_json({"type": "stop_session"})
            _drain(ws, {"final"})
            msgs = _drain(ws, {"agent_message"})
            reply = next(m for m in msgs if m["type"] == "agent_message")["text"]
            assert reply == FALLBACK_REPLY
            assert "429" not in reply and "provider" not in reply.lower()
            assert [m["state"] for m in msgs if m["type"] == "state"] == ["PROCESSING", "THINKING"]