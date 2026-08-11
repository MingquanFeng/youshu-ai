"""v1 路由聚合。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import analysis, bill, user

api_v1_router = APIRouter()
api_v1_router.include_router(user.router)
api_v1_router.include_router(bill.router)
api_v1_router.include_router(analysis.router)
