"""AI 识别记录表：保存每次识别的原始 OCR / 模型输出，便于审计和回溯。"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AIRecord(Base):
    __tablename__ = "ai_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), index=True, nullable=False
    )
    bill_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bill.id"), nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), default="")
    ocr_text: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(64), default="")
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
