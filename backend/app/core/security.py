"""JWT 鉴权：登录态写入 user_id，依赖 get_current_user 提取。"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from fastapi import Header
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import BizException

logger = logging.getLogger(__name__)

# JWT_SECRET 安全策略
DEV_DEFAULT_SECRET = "change-me-in-prod"  # .env.example 默认值, 必须改
MIN_SECRET_LENGTH = 32  # HS256 推荐 ≥ 256 bits = 32 字符


def validate_jwt_secret(env: str, secret: str) -> None:
    """启动时校验 JWT_SECRET 强度。

    dev/test: 默认值或过短 → logger.warning, 不阻塞开发
    prod:     默认值或过短 → raise RuntimeError, 阻止弱 secret 上生产
    """
    is_default = secret == DEV_DEFAULT_SECRET
    is_short = len(secret) < MIN_SECRET_LENGTH

    if not (is_default or is_short):
        return

    if is_default:
        msg = f"JWT_SECRET 是 dev 默认值 ({DEV_DEFAULT_SECRET!r})! 必须改成随机字符串"
    else:
        msg = f"JWT_SECRET 太短 ({len(secret)} 字符, 推荐 ≥ {MIN_SECRET_LENGTH})"

    if env == "prod":
        # 生产环境直接 fatal, 不允许弱 secret 上线
        raise RuntimeError(f"[FATAL] {msg}; 用 `openssl rand -hex 32` 生成")
    # dev/test 环境只 warning, 不阻塞开发
    logger.warning("[SECURITY] %s (env=%s, 建议 prod 部署前改)", msg, env)


# 启动时校验一次 (模块加载即生效, 不依赖 lifespan)
validate_jwt_secret(settings.app_env, settings.jwt_secret)


def create_token(user_id: int, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": dt.datetime.now(dt.UTC),
        "exp": dt.datetime.now(dt.UTC)
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
