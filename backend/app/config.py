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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def streaming_ws_url(self) -> str:
        return (
            f"{self.assemblyai_base_url}{ASSEMBLYAI_V3_WS_PATH}"
            f"?sample_rate={self.sample_rate}&speech_model={self.assemblyai_speech_model}&format_turns=true"
        )


def get_settings() -> Settings:
    return Settings()