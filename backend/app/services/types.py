"""AI 识别的统一数据结构。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecognizeResult(BaseModel):
    amount: float = Field(..., gt=0, description="金额，正数")
    merchant: str = Field("", description="商户名")
    category: str = Field("其他", description="一级分类")
    time: datetime = Field(..., description="消费发生时间")
    payment: str = Field("", description="支付方式，如 微信支付/支付宝")
    score: float = Field(0.0, ge=0, le=1, description="AI 可信度 0-1")
    raw_ocr: Optional[str] = Field(None, description="OCR 原文，便于追溯")
