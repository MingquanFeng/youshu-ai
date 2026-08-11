"""SQLAlchemy 异步 engine 与 session。

开发环境走 SQLite 同步 driver 即可，省去 aiosqlite；生产可换 asyncpg。
这里使用 sync session，FastAPI 里用 Depends 注入即可。
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """统一基类，所有 ORM 模型继承它。"""


_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：每次请求一个 Session，请求结束自动 close。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """启动时建表（dev 简单方案；生产应走 Alembic 迁移）。"""
    # 导入 models 让 Base 知道它们的存在
    from app.models import bill, category, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
