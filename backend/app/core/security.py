"""JWT 鉴权：登录态写入 user_id，依赖 get_current_user 提取。"""
from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import Depends, Header
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import BizException


def create_token(user_id: int, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": dt.datetime.now(dt.timezone.utc),
        "exp": dt.datetime.now(dt.timezone.utc)
        + dt.timedelta(minutes=settings.jwt_expire_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise BizException(40100, "token 无效或已过期", status_code=401) from exc


def get_current_user(authorization: str | None = Header(default=None)) -> int:
    """FastAPI 依赖：从 Authorization: Bearer <token> 提取 user_id。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise BizException(40100, "缺少 token", status_code=401)
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise BizException(40100, "token 缺少 sub", status_code=401)
    try:
        return int(sub)
    except ValueError as exc:
        raise BizException(40100, "token sub 不合法", status_code=401) from exc
