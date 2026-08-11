"""请求 / 响应的 Pydantic Schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ---------------------- 通用 ---------------------- #

class LoginIn(BaseModel):
    code: str = Field(..., description="微信 code")


class LoginOut(BaseModel):
    token: str
    user_id: int
    nickname: str = ""
    avatar: str = ""


class UploadOut(BaseModel):
    image_id: str
    image_url: str


class RecognizeIn(BaseModel):
    image_id: str


class RecognizeOut(BaseModel):
    amount: float
    merchant: str
    category: str
    time: datetime
    payment: str
    score: float = 0.0


class SaveBillIn(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = "其他"
    merchant: str = ""
    pay_method: str = ""
    bill_time: datetime
    remark: str = ""
    source: str = "manual"
    ai_score: float = 1.0
    image_id: str | None = None


class BillItem(BaseModel):
    id: int
    amount: float
    category: str
    merchant: str
    pay_method: str
    bill_time: datetime
    remark: str = ""
    source: str
    ai_score: float


class BillListOut(BaseModel):
    total: int
    page: int
    size: int
    items: list[BillItem]


class MonthlyAnalysisOut(BaseModel):
    total: float
    top_category: str
    advice: str
