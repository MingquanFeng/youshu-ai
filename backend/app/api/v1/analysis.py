"""消费分析：当前月的总消费、Top 分类、给一句建议。"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.bill import Bill
from app.schemas import MonthlyAnalysisOut

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/monthly", response_model=None, summary="本月消费分析")
def monthly(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = (
        db.query(Bill.category, func.sum(Bill.amount))
        .filter(Bill.user_id == user_id, Bill.bill_time >= start)
        .group_by(Bill.category)
        .all()
    )
    total = float(sum(amount for _, amount in rows))
    if not rows:
        return ok(MonthlyAnalysisOut(total=0, top_category="暂无", advice="本月还没有账单，先记一笔吧～").model_dump())

    counter = Counter({cat: float(amt) for cat, amt in rows})
    top_category, top_amount = counter.most_common(1)[0]
    ratio = top_amount / total if total else 0
    advice = _make_advice(top_category, ratio, total)

    return ok(
        MonthlyAnalysisOut(
            total=round(total, 2),
            top_category=top_category,
            advice=advice,
        ).model_dump()
    )


def _make_advice(category: str, ratio: float, total: float) -> str:
    if ratio >= 0.5:
        return f"本月 {category} 占比 {int(ratio * 100)}%，建议适当控制该类支出。"
    if total >= 5000:
        return f"本月已支出 {total:.0f} 元，整体消费偏高，注意预算。"
    return f"继续保持，{category} 类支出较为合理。"
