from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import create_agent
from app.api.health import router as health_router
from app.config import get_settings
from app.utils.logging import get_logger
from app.ws.router import router as voice_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    agent = None
    try:
        if settings.llm_mode == "mock" or settings.groq_api_key:
            agent = create_agent(settings)
            logger.info("voice agent ready: llm_mode=%s provider=%s", settings.llm_mode, settings.llm_provider)
        else:
            logger.warning("voice agent disabled until GROQ_API_KEY is set (or LLM_MODE=mock)")
    except ValueError as exc:
        logger.warning("voice agent disabled: %s", exc)
    app.state.agent = agent
    yield
    if agent is not None:
        await agent.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="DataForge Voice Agent API", version="0.2.0", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)
    app.state.settings = settings
    app.state.agent = None

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

    logger.info("DataForge voice backend initialised (stt_mode=%s, llm_mode=%s)", settings.stt_mode, settings.llm_mode)
    return app


app = create_app()