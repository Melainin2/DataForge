from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ASSEMBLYAI_STREAMING_BASE = "https://streaming.assemblyai.com"
ASSEMBLYAI_V3_WS_PATH = "/v3/ws"


class Settings(BaseSettings):
    """Centralized configuration loaded from environment / backend/.env."""

    assemblyai_api_key: str = ""
    assemblyai_base_url: str = ASSEMBLYAI_STREAMING_BASE
    assemblyai_speech_model: str = "universal-3-5-pro"
    sample_rate: int = 16000
    stt_mode: Literal["real", "mock"] = "real"
    frontend_origin: str = "http://localhost:3000"
    log_level: str = "INFO"
    max_audio_frame_bytes: int = 320_000

    # --- LLM (Part 2) ---
    llm_mode: Literal["real", "mock"] = "real"
    llm_provider: Literal["groq"] = "groq"
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512
    llm_timeout_seconds: float = 30.0
    # Bounded conversation history sent to the LLM per turn (latency control).
    max_context_messages: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def streaming_ws_url(self) -> str:
        return (
            f"{self.assemblyai_base_url}{ASSEMBLYAI_V3_WS_PATH}"
            f"?sample_rate={self.sample_rate}&speech_model={self.assemblyai_speech_model}&format_turns=true"
        )


def get_settings() -> Settings:
    return Settings()