from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, conversations, documents, health, memories, model_config, preferences
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    application = FastAPI(
        title="AI Agent",
        version="1.0.0",
        description="A private, context-aware AI assistant with long-term memory and document understanding.",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    application.include_router(health.router, prefix="/api")
    application.include_router(conversations.router, prefix="/api")
    application.include_router(chat.router, prefix="/api")
    application.include_router(memories.router, prefix="/api")
    application.include_router(preferences.router, prefix="/api")
    application.include_router(model_config.router, prefix="/api")
    application.include_router(documents.router, prefix="/api")

    register_exception_handlers(application)
    return application


app = create_app()
