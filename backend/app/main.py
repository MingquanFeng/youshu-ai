"""AI 记账助手后端入口。

启动方式：
    cd backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.response import ok
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 替代 @app.on_event("startup") (FastAPI 0.93+ 弃用)
    init_db()
    logger.info("Database initialized: %s", settings.database_url)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI 原生个人记账应用 - 后端 API",
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)

    # 本地存储的图片通过 /static/uploads/... 直接访问
    os.makedirs(settings.storage_dir, exist_ok=True)
    application.mount(
        "/static/uploads",
        StaticFiles(directory=settings.storage_dir),
        name="uploads",
    )

    @application.get("/health", tags=["meta"])
    def health() -> dict:
        return ok({"status": "ok", "env": settings.app_env})

    application.include_router(api_v1_router, prefix="/api/v1")
    return application


app = create_app()
