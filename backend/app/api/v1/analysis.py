"""消费分析：当前月的总消费、Top 分类、给一句建议。"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Body, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.bill import Bill
from app.schemas import (
    CategoryIn,
    CategoryItem,
    CategoryOut,
    DailyIn,
    DailyItem,
    DailyOut,
    MonthlyAnalysisOut,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/monthly", response_model=None, summary="本月消费分析")
def monthly(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 支出 (amount < 0): 绝对值累加, 用于显示
    expense_rows = (
        db.query(func.coalesce(func.sum(-Bill.amount), 0))
        .filter(
            Bill.user_id == user_id,
            Bill.bill_time >= start,
            Bill.amount < 0,
        )
        .one()
    )
    expense = float(expense_rows[0] or 0)

    # 收入 (amount > 0): 累加
    income_rows = (
        db.query(func.coalesce(func.sum(Bill.amount), 0))
        .filter(
            Bill.user_id == user_id,
            Bill.bill_time >= start,
            Bill.amount > 0,
        )
        .one()
    )
    income = float(income_rows[0] or 0)

    if expense == 0 and income == 0:
        return ok(
            MonthlyAnalysisOut(
                income=0, expense=0, total=0,
                top_category="暂无", advice="本月还没有账单，先记一笔吧～"
            ).model_dump()
        )

    # 找 top 支出分类 (按绝对值)
    top_rows = (
        db.query(Bill.category, func.sum(-Bill.amount).label("s"))
        .filter(
            Bill.user_id == user_id,
            Bill.bill_time >= start,
            Bill.amount < 0,
        )
        .group_by(Bill.category)
        .order_by(func.sum(-Bill.amount).desc())
        .limit(1)
        .all()
    )
    top_category = top_rows[0][0] if top_rows else "暂无"
    top_amount = float(top_rows[0][1]) if top_rows else 0
    ratio = top_amount / expense if expense else 0
    advice = _make_advice(top_category, ratio, expense)

    return ok(
        MonthlyAnalysisOut(
            income=round(income, 2),
            expense=round(expense, 2),
            total=round(expense - income, 2),
            top_category=top_category,
            advice=advice,
        ).model_dump()
    )


@router.post("/daily", response_model=None, summary="近 N 天每日消费趋势")
def daily(
    body: DailyIn = Body(default_factory=DailyIn),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    today = date.today()
    start = today - timedelta(days=body.days - 1)

    # 时区安全：用 substr(1,10) 按存储格式截取 YYYY-MM-DD，避免 SQLite func.date() 按 UTC 切日期
    rows = (
        db.query(
            func.substr(Bill.bill_time, 1, 10).label("d"),
            func.sum(Bill.amount).label("s"),
        )
        .filter(
            Bill.user_id == user_id,
            Bill.deleted_at.is_(None),
            func.substr(Bill.bill_time, 1, 10) >= start.isoformat(),
            func.substr(Bill.bill_time, 1, 10) <= today.isoformat(),
        )
        .group_by(func.substr(Bill.bill_time, 1, 10))
        .all()
    )
    totals = {d: float(s) for d, s in rows}

    items = []
    for i in range(body.days):
        d = start + timedelta(days=i)
        items.append(DailyItem(date=d.isoformat(), total=totals.get(d.isoformat(), 0)))

    return ok(DailyOut(days=items).model_dump())


@router.post("/category", response_model=None, summary="近 N 个月分类消费占比")
def category(
    body: CategoryIn = Body(default_factory=CategoryIn),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    today = datetime.now()
    start = (today - relativedelta(months=body.months - 1)).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    # 时区安全：用 substr(1,10) 按存储格式截取 YYYY-MM-DD，避免 SQLite 隐式时区转换导致首末几天偏差
    # 与 T-009 /daily 保持一致
    rows = (
        db.query(
            case((Bill.category == "", "其他"), else_=Bill.category).label("cat"),
            func.sum(Bill.amount).label("s"),
        )
        .filter(
            Bill.user_id == user_id,
            Bill.deleted_at.is_(None),
            func.substr(Bill.bill_time, 1, 10) >= start.strftime("%Y-%m-%d"),
        )
        .group_by(case((Bill.category == "", "其他"), else_=Bill.category))
        .order_by(func.sum(Bill.amount).desc())
        .all()
    )

    grand_total = sum(float(amt) for _, amt in rows)
    if grand_total == 0:
        return ok(CategoryOut(categories=[], total=0).model_dump())

    items = []
    for cat, amt in rows:
        rounded_amt = round(float(amt), 2)
        items.append(
            CategoryItem(
                category=cat,
                amount=rounded_amt,
                percent=round(rounded_amt / grand_total, 4),
            )
        )

    return ok(CategoryOut(categories=items, total=round(grand_total, 2)).model_dump())


def _make_advice(category: str, ratio: float, expense: float) -> str:
    if ratio >= 0.5:
        return f"本月 {category} 占比 {int(ratio * 100)}%，建议适当控制该类支出。"
    if expense >= 5000:
        return f"本月已支出 {expense:.0f} 元，整体消费偏高，注意预算。"
    return f"继续保持，{category} 类支出较为合理。"
