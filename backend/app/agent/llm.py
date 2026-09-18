"""LLM provider layer.

The rest of the application only talks to the ``LLMProvider`` interface so the
provider stays swappable. Two implementations ship:

* ``GroqLLMProvider`` — calls the OpenAI-compatible Groq free tier
  (``https://api.groq.com/openai/v1/chat/completions``) with httpx; picks the
  fast ``llama-3.3-70b-versatile`` model by default. No extra SDK dependency.
* ``MockLLMProvider`` — deterministic local fake for dev/tests (no key) that
  demonstrates short-term memory ("what is my name?", preferences…).
"""

from __future__ import annotations

import re
import time
from typing import Optional, Protocol

import httpx

from app.utils.logging import get_logger

logger = get_logger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


# -- errors -----------------------------------------------------------------


class LLMError(Exception):
    """Base class; raised to the Agent layer, mapped to user-safe fallbacks."""


class LLMTimeoutError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMInvalidKeyError(LLMError):
    pass


class LLMConnectionError(LLMError):
    pass


class LLMProviderError(LLMError):
    pass


# -- interface ---------------------------------------------------------------


class LLMProvider(Protocol):
    async def complete(self, messages: list[dict[str, str]]) -> str: ...

    async def aclose(self) -> None: ...


# -- Groq (real) --------------------------------------------------------------


class GroqLLMProvider:
    """OpenAI-compatible chat completions against the Groq free tier."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = GROQ_DEFAULT_MODEL,
        base_url: str = GROQ_BASE_URL,
        temperature: float = 0.7,
        max_tokens: int = 512,
        timeout_seconds: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)

    async def complete(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        started = time.perf_counter()
        logger.info("llm request: model=%s messages=%d", self._model, len(messages))
        try:
            response = await self._client.post(self._url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"llm request timed out: {exc}") from exc
        except httpx.TransportError as exc:
            raise LLMConnectionError(f"llm connection failed: {exc}") from exc

        latency_ms = (time.perf_counter() - started) * 1000
        if response.status_code == 401:
            raise LLMInvalidKeyError("llm rejected the api key (401)")
        if response.status_code == 429:
            raise LLMRateLimitError("llm rate limit exceeded (429)")
        if response.status_code >= 400:
            raise LLMProviderError(f"llm provider error: {response.status_code} {response.text[:200]}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMProviderError(f"unexpected llm response shape: {exc}") from exc

        usage = data.get("usage", {})
        logger.info(
            "llm response: latency_ms=%.0f prompt_tokens=%s completion_tokens=%s",
            latency_ms,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        return (content or "").strip()

    async def aclose(self) -> None:
        await self._client.aclose()


# -- Mock (deterministic) ------------------------------------------------------


_TOKEN_RE = re.compile(r"[a-z0-9']+", re.IGNORECASE)
_GREETINGS = {"hello", "hi", "hey", "yo", "hiya", "bonjour", "greetings", "sup"}


class MockLLMProvider:
    """Rule-based fake that proves the agent + memory wiring without a key.

    Deterministic, so tests are stable:
    * greeting  -> friendly opener
    * "my name is X" -> remembers the name, addresses the user
    * "what is my name?" -> recalls it
    * "i love/like/enjoy X" -> remembers the preference
    * anything else -> generic conversational reply
    """

    async def complete(self, messages: list[dict[str, str]]) -> str:
        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
        if not user_msgs:
            return "I'm ready when you are."
        last = user_msgs[-1].strip()
        lower = last.lower()

        name = self._remembered_name(user_msgs)
        liked = self._remembered_preference(user_msgs)
        words = set(_TOKEN_RE.findall(lower))

        if "my name is" in lower:
            return f"Nice to meet you, {name}."
        if name and words & {"what", "name"} and "is my name" in lower:
            return f"Your name is {name}."
        if liked and words & {"do", "love", "like", "enjoy"}:
            return f"You told me you love {liked}."
        if words & _GREETINGS:
            return "Hello! How can I help you?"
        return "I'm here — what would you like to talk about?"

    @staticmethod
    def _remembered_name(user_msgs: list[str]) -> Optional[str]:
        for msg in reversed(user_msgs):
            m = re.search(r"(?:my name is|i'm called|call me)\s+([a-z][a-z0-9' ]+?)[.!?]?\s*$", msg, re.IGNORECASE)
            if m:
                return m.group(1).strip().split()[0].strip("'")
        return None

    @staticmethod
    def _remembered_preference(user_msgs: list[str]) -> Optional[str]:
        for msg in reversed(user_msgs):
            m = re.search(r"(?:i (?:love|like|enjoy|am into)\s+)(.+)", msg, re.IGNORECASE)
            if m:
                return m.group(1).strip().strip(".!?").strip()
        return None

    async def aclose(self) -> None:
        return None


# -- factory -------------------------------------------------------------------


def build_llm(settings) -> LLMProvider:
    from app.config import Settings

    assert isinstance(settings, Settings)  # keep accidental wrong types out
    if settings.llm_mode == "mock":
        return MockLLMProvider()
    if settings.llm_provider != "groq":
        raise ValueError(f"unsupported llm_provider: {settings.llm_provider}")
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured (set LLM_MODE=mock to run without a key)")
    return GroqLLMProvider(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout_seconds=settings.llm_timeout_seconds,
    )