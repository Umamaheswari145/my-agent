from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    application = FastAPI(title="Personal AI Agent", version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, prefix="/api")
    register_exception_handlers(application)
    return application


app = create_app()
