from fastapi import APIRouter, Request

from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(request: Request) -> dict:
    settings = request.app.state.settings
    agent = getattr(request.app.state, "agent", None)
    body = {
        "status": "ok",
        "service": "dataforge-voice-backend",
        "version": "0.2.0",
        "stt_mode": settings.stt_mode,
        "assemblyai_configured": bool(settings.assemblyai_api_key),
        "llm_mode": settings.llm_mode,
        "llm_provider": settings.llm_provider,
        "llm_configured": bool(settings.groq_api_key),
        "agent_enabled": agent is not None,
    }
    logger.debug("health check", extra=body)
    return body