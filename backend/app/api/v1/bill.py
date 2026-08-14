"""账单相关接口：上传、AI 识别、保存、列表。"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException
from app.core.response import ok
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.bill import Bill
from app.schemas import (
    BillItem,
    BillListOut,
    RecognizeIn,
    RecognizeOut,
    SaveBillIn,
    UpdateBillIn,
    UploadOut,
)
from app.services.pipeline import recognize_pipeline

router = APIRouter(prefix="/bill", tags=["bill"])
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=None, summary="上传支付截图")
def upload(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
) -> dict:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BizException(40000, f"不支持的图片类型: {file.content_type}")
    ext = _ext_from_mime(file.content_type)
    image_id = uuid.uuid4().hex
    rel_path = f"{user_id}/{image_id}{ext}"
    abs_dir = os.path.join(settings.storage_dir, str(user_id))
    os.makedirs(abs_dir, exist_ok=True)
    abs_path = os.path.join(abs_dir, f"{image_id}{ext}")

    size = 0
    with open(abs_path, "wb") as f:
        while chunk := file.file.read(64 * 1024):
            size += len(chunk)
            if size > MAX_IMAGE_BYTES:
                f.close()
                os.remove(abs_path)
                raise BizException(40000, "图片超过 10MB")
            f.write(chunk)

    image_url = f"/static/uploads/{rel_path}"
    return ok(UploadOut(image_id=image_id, image_url=image_url).model_dump())


@router.post("/recognize", response_model=None, summary="AI 识别账单")
def recognize(
    body: RecognizeIn,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    abs_path = _resolve_image(user_id, body.image_id)
    result = recognize_pipeline(db, user_id=user_id, image_path=abs_path)
    return ok(
        RecognizeOut(
            amount=result.amount,
            merchant=result.merchant,
            category=result.category,
            time=result.time,
            payment=result.payment,
            score=result.score,
        ).model_dump(mode="json")
    )


@router.post("/save", response_model=None, summary="保存账单")
def save(
    body: SaveBillIn,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = Bill(
        user_id=user_id,
        amount=body.amount,
        category=body.category or "其他",
        merchant=body.merchant,
        pay_method=body.pay_method,
        bill_time=body.bill_time,
        remark=body.remark,
        source=body.source,
        ai_score=body.ai_score,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return ok({"id": bill.id})


@router.get("/list", response_model=None, summary="查询账单")
def list_bills(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    date: str | None = Query(None, description="YYYY-MM-DD"),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    q = db.query(Bill).filter(Bill.user_id == user_id)
    if category:
        q = q.filter(Bill.category == category)
    if date:
        try:
            day = datetime.strptime(date, "%Y-%m-%d")
        except ValueError as exc:
            raise BizException(40000, "date 必须是 YYYY-MM-DD") from exc
        q = q.filter(func.date(Bill.bill_time) == day.date())

    total = q.count()
    items = (
        q.order_by(Bill.bill_time.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return ok(
        BillListOut(
            total=total,
            page=page,
            size=size,
            items=[
                BillItem(
                    id=b.id,
                    amount=float(b.amount),
                    category=b.category,
                    merchant=b.merchant,
                    pay_method=b.pay_method,
                    bill_time=b.bill_time,
                    remark=b.remark,
                    source=b.source,
                    ai_score=float(b.ai_score),
                )
                for b in items
            ],
        ).model_dump(mode="json")
    )


@router.get("/{bill_id}", response_model=None, summary="账单详情")
def get_bill(
    bill_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = db.query(Bill).filter(Bill.id == bill_id).one_or_none()
    if bill is None or bill.user_id != user_id:
        raise BizException(40400, "账单不存在")
    # TODO(T-004): 加 deleted_at 过滤
    return ok(BillItem(
        id=bill.id,
        amount=float(bill.amount),
        category=bill.category,
        merchant=bill.merchant,
        pay_method=bill.pay_method,
        bill_time=bill.bill_time,
        remark=bill.remark,
        source=bill.source,
        ai_score=float(bill.ai_score),
    ).model_dump(mode="json"))


WHITELIST = {"amount", "category", "merchant", "pay_method", "bill_time", "remark"}


@router.put("/{bill_id}", response_model=None, summary="编辑账单")
def update_bill(
    bill_id: int,
    body: UpdateBillIn,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    bill = db.query(Bill).filter(Bill.id == bill_id).one_or_none()
    if bill is None or bill.user_id != user_id:
        raise BizException(40400, "账单不存在")
    # TODO(T-004): 加 deleted_at 过滤

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise BizException(40000, "至少更新一个字段")

    applied = {k: v for k, v in updates.items() if k in WHITELIST}
    for k, v in applied.items():
        setattr(bill, k, v)

    # audit: 用户修正后给 remark 加 "[修正] " 前缀
    # TODO(T-AUDIT): 引入 updated_at 列后可移除此前缀
    base_remark = applied.get("remark", bill.remark)
    bill.remark = f"[修正] {base_remark}"

    db.commit()
    db.refresh(bill)
    return ok(BillItem(
        id=bill.id,
        amount=float(bill.amount),
        category=bill.category,
        merchant=bill.merchant,
        pay_method=bill.pay_method,
        bill_time=bill.bill_time,
        remark=bill.remark,
        source=bill.source,
        ai_score=float(bill.ai_score),
    ).model_dump(mode="json"))


# ------------------------------ 工具 ------------------------------ #

def _ext_from_mime(mime: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
    }.get(mime, ".jpg")


def _resolve_image(user_id: int, image_id: str) -> str:
    user_dir = os.path.join(settings.storage_dir, str(user_id))
    if not os.path.isdir(user_dir):
        raise BizException(40400, "图片不存在")
    for name in os.listdir(user_dir):
        if name.startswith(image_id):
            return os.path.join(user_dir, name)
    raise BizException(40400, "图片不存在")
