"""微信小程序登录：用 code 换 openid，再 upsert 用户并签发 JWT。"""
from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException
from app.core.response import ok
from app.core.security import create_token
from app.db.session import get_db
from app.models.user import User
from app.schemas import LoginIn, LoginOut

router = APIRouter(prefix="/user", tags=["user"])
logger = logging.getLogger(__name__)

WX_CODE2SESSION = "https://api.weixin.qq.com/sns/jscode2session"


@router.post("/login", response_model=None, summary="微信登录")
def login(body: LoginIn, db: Session = Depends(get_db)) -> dict:
    openid = _wx_code2openid(body.code)
    user = db.query(User).filter(User.openid == openid).one_or_none()
    if user is None:
        user = User(openid=openid, nickname="记账新手", avatar="")
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token(user.id)
    return ok(
        LoginOut(
            token=token,
            user_id=user.id,
            nickname=user.nickname,
            avatar=user.avatar,
        ).model_dump()
    )


def _wx_code2openid(code: str) -> str:
    """真实环境：调微信接口换 openid。缺凭证时走 dev mock。"""
    if not settings.wx_app_id or not settings.wx_app_secret:
        # dev mock：code 即视为 openid，保证流程跑通
        logger.warning("未配置 WX_APP_ID/WX_APP_SECRET，使用 dev mock openid")
        return f"mock-{code or uuid.uuid4().hex[:8]}"

    params = {
        "appid": settings.wx_app_id,
        "secret": settings.wx_app_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    try:
        resp = httpx.get(WX_CODE2SESSION, params=params, timeout=5.0)
        data = resp.json()
    except httpx.HTTPError as exc:
        raise BizException(50000, f"微信接口调用失败: {exc}") from exc

    if "openid" not in data:
        raise BizException(40000, f"微信返回异常: {data}")
    return data["openid"]
