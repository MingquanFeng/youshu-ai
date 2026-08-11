"""AI 编排入口：上传图片 → OCR → vision → refine，全过程落 ai_record。"""
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_record import AIRecord
from app.services.classify import refine
from app.services.ocr import run_ocr
from app.services.types import RecognizeResult
from app.services.vision import run_vision


def recognize_pipeline(
    db: Session, user_id: int, image_path: str, model_tag: str = "default"
) -> RecognizeResult:
    """完整识别流程，并把原始数据落库，便于审计。"""
    ocr_text = run_ocr(image_path)
    vision_result = run_vision(image_path, ocr_text)
    final = refine(vision_result)

    record = AIRecord(
        user_id=user_id,
        bill_id=None,
        image_url=_to_public_url(image_path),
        ocr_text=ocr_text,
        model=model_tag,
        result_json=final.model_dump(mode="json"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return final


def _to_public_url(image_path: str) -> str:
    """本地存储时返回相对路径；生产应替换为 OSS/COS 公开链接。"""
    rel = os.path.relpath(image_path, settings.storage_dir)
    return f"/static/uploads/{rel}"
