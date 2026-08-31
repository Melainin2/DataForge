from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config import get_settings
from app.utils.logging import get_logger
from app.ws.router import router as voice_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DataForge Voice Agent API", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(voice_router)

    @app.get("/")
    async def root() -> dict:
        return {"service": "DataForge Voice Agent API", "docs": "/api/docs", "health": "/api/health"}

    logger.info("DataForge voice backend initialised (stt_mode=%s)", settings.stt_mode)
    return app


app = create_app()