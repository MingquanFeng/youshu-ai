"""pytest 公共夹具：临时 SQLite + TestClient + 已登录 token。"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 用临时库文件，避免污染真实数据库
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.core.config import settings  # noqa: E402  必须在环境变量之后导入
from app.db import session as db_session  # noqa: E402
from app.main import app  # noqa: E402
from app.api.v1 import user as user_api  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    db_session.Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()
    os.unlink(_tmp.name)


@pytest.fixture()
def db(engine) -> Iterator:
    """每个用例一个独立 session，结束时回滚。"""
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    s = Session()
    # 把 app.db.session 模块的 SessionLocal/Engine 替换成测试用的，便于依赖注入
    db_session.engine = engine
    db_session.SessionLocal = Session
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(db) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """登录拿到 token，返回可直接放进请求头的 dict。"""
    res = client.post("/api/v1/user/login", json={"code": "pytest"})
    assert res.status_code == 200
    token = res.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
