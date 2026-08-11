"""账单表。

source: manual / image_ai / voice_ai
ai_score: AI 可信度 0-1，人工记账时为 1.0
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Bill(Base):
    __tablename__ = "bill"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), index=True, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(32), index=True, default="")
    merchant: Mapped[str] = mapped_column(String(128), default="")
    pay_method: Mapped[str] = mapped_column(String(32), default="")
    bill_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    remark: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(16), default="manual")
    ai_score: Mapped[float] = mapped_column(Numeric(4, 3), default=1.0)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_bill_user_time", "user_id", "bill_time"),)
