from fastapi import APIRouter, Request

from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(request: Request) -> dict:
    settings = request.app.state.settings
    body = {
        "status": "ok",
        "service": "dataforge-voice-backend",
        "version": "0.1.0",
        "stt_mode": settings.stt_mode,
        "assemblyai_configured": bool(settings.assemblyai_api_key),
    }
    logger.debug("health check", extra=body)
    return body