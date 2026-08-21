"""请求 / 响应的 Pydantic Schema。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

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
    direction: str = "expense"  # expense 支出 | income 收入
    merchant: str
    category: str
    time: datetime
    payment: str
    score: float = 0.0


class SaveBillIn(BaseModel):
    # amount: 正数=收入, 负数=支出.  0 不允许 (无意义)
    amount: float
    _non_zero = None  # 标记, 实际验证在 endpoint 层 (Pydantic v2 ne=0 在 float 不可靠)

    @field_validator("amount")
    @classmethod
    def _amount_not_zero(cls, v: float) -> float:
        if v == 0:
            raise ValueError("amount 不能为 0")
        return v
    category: str = "其他"
    merchant: str = ""
    pay_method: str = ""
    bill_time: datetime
    remark: str = ""
    source: str = "manual"
    ai_score: float = 1.0
    image_id: str | None = None


class UpdateBillIn(BaseModel):
    amount: float | None = None

    @field_validator("amount")
    @classmethod
    def _amount_not_zero(cls, v):
        if v is not None and v == 0:
            raise ValueError("amount 不能为 0")
        return v
    category: str | None = None
    merchant: str | None = None
    pay_method: str | None = None
    bill_time: datetime | None = None
    remark: str | None = None


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
    """本月消费分析 (amount 存负数代表支出, 正数代表收入).

    - income: 收入合计 (正数)
    - expense: 支出合计 (正数绝对值, 用于显示)
    - total: 净支出 = expense - income (剩余可花)
    """

    income: float = 0
    expense: float = 0
    total: float = 0
    top_category: str
    advice: str


class DailyIn(BaseModel):
    days: int = Field(default=30, ge=1, le=365, description="回溯天数（含今天）")


class DailyItem(BaseModel):
    date: str        # YYYY-MM-DD
    total: float     # 当日总金额，无数据为 0


class DailyOut(BaseModel):
    days: list[DailyItem]


class CategoryIn(BaseModel):
    months: int = Field(default=1, ge=1, le=12, description="回溯月数（含本月），默认 1")


class CategoryItem(BaseModel):
    category: str
    amount: float
    percent: float


class CategoryOut(BaseModel):
    categories: list[CategoryItem]
    total: float
