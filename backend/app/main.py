from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import (
    chat_router,
    customers_router,
    health_router,
    knowledge_router,
    metrics_router,
    product_chat_router,
    queue_router,
    seed_router,
    tickets_router,
)
from app.config.settings import is_auto_seed_enabled
from app.storage.repository import init_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_storage()

    if is_auto_seed_enabled():
        try:
            from app.services.seed_service import seed_demo_data
            seed_demo_data()
        except Exception:
            pass  # seed failure should never block startup

    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="SupportPilot AI",
        description="AI customer service operations platform MVP",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:5175",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(chat_router)
    application.include_router(product_chat_router)
    application.include_router(knowledge_router)
    application.include_router(metrics_router)
    application.include_router(queue_router)
    application.include_router(tickets_router)
    application.include_router(customers_router)
    application.include_router(seed_router)
    return application


app = create_app()
