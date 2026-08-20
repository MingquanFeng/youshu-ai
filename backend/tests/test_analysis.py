"""消费分析接口。"""
from __future__ import annotations


def _save(client, headers, amount: float, category: str, time: str):
    return client.post(
        "/api/v1/bill/save",
        json={
            "amount": amount,
            "category": category,
            "merchant": "test",
            "pay_method": "微信支付",
            "bill_time": time,
            "source": "manual",
            "ai_score": 1.0,
        },
        headers=headers,
    )


def _save_daily(client, headers, amount, bill_time):
    # amount 参数表达"支出多少", 自动转负数存 (符合前端保存逻辑)
    return client.post(
        "/api/v1/bill/save",
        json={
            "amount": -abs(amount),  # 支出 = 负数
            "category": "餐饮",
            "merchant": "测试",
            "pay_method": "微信",
            "bill_time": bill_time,
            "source": "manual",
            "ai_score": 1.0,
        },
        headers=headers,
    )


def _save_category(client, headers, amount, category, bill_time):
    return client.post(
        "/api/v1/bill/save",
        json={
            "amount": amount,
            "category": category,
            "merchant": "test",
            "pay_method": "微信",
            "bill_time": bill_time,
            "source": "manual",
            "ai_score": 1.0,
        },
        headers=headers,
    )


def test_monthly_empty(client, auth_headers):
    res = client.post("/api/v1/analysis/monthly", headers=auth_headers).json()
    assert res["code"] == 0
    assert res["data"]["total"] == 0


def test_monthly_sums_and_top(client, auth_headers):
    # 支出: amount 存负数
    _save(client, auth_headers, -30, "餐饮", "2026-08-01T10:00:00")
    _save(client, auth_headers, -80, "餐饮", "2026-08-05T10:00:00")
    _save(client, auth_headers, -50, "交通", "2026-08-08T10:00:00")
    # 收入: 工资 (amount > 0)
    _save(client, auth_headers, 5000, "工资", "2026-08-01T10:00:00")

    res = client.post("/api/v1/analysis/monthly", headers=auth_headers).json()
    assert res["code"] == 0
    data = res["data"]
    assert data["expense"] == 160       # abs(-30) + abs(-80) + abs(-50)
    assert data["income"] == 5000       # 工资
    assert data["total"] == -4840       # expense - income (净支出)
    assert data["top_category"] == "餐饮"
    assert "餐饮" in data["advice"]


def test_monthly_requires_auth(client):
    res = client.post("/api/v1/analysis/monthly")
    assert res.status_code == 401


# ------------------------------ T-009: daily ------------------------------ #


def _day(offset: int) -> str:
    """相对今天的日期字符串 YYYY-MM-DD，offset=0 表今天。"""
    from datetime import date, timedelta

    return (date.today() + timedelta(days=offset)).isoformat()


def test_daily_basic(client, auth_headers):
    # 灌 3 天数据（每天多条）
    _save_daily(client, auth_headers, 10, f"{_day(-2)}T10:00:00")
    _save_daily(client, auth_headers, 20, f"{_day(-2)}T12:00:00")
    _save_daily(client, auth_headers, 30, f"{_day(-1)}T10:00:00")
    _save_daily(client, auth_headers, 40, f"{_day(0)}T10:00:00")
    _save_daily(client, auth_headers, 50, f"{_day(0)}T18:00:00")

    res = client.post("/api/v1/analysis/daily", json={"days": 3}, headers=auth_headers).json()
    assert res["code"] == 0
    days = res["data"]["days"]
    assert len(days) == 3
    # 日期升序
    assert [d["date"] for d in days] == [_day(-2), _day(-1), _day(0)]
    # total 求和正确
    assert days[0]["total"] == 30  # 10+20
    assert days[1]["total"] == 30
    assert days[2]["total"] == 90  # 40+50


def test_daily_default_days(client, auth_headers):
    _save_daily(client, auth_headers, 100, f"{_day(0)}T10:00:00")

    res = client.post("/api/v1/analysis/daily", headers=auth_headers).json()
    assert res["code"] == 0
    days = res["data"]["days"]
    assert len(days) == 30
    # 仅今天 total>0
    assert all(d["total"] == 0 for d in days[:-1])
    assert days[-1]["total"] == 100


def test_daily_empty(client, auth_headers):
    res = client.post("/api/v1/analysis/daily", json={"days": 30}, headers=auth_headers).json()
    assert res["code"] == 0
    days = res["data"]["days"]
    assert len(days) == 30
    assert all(d["total"] == 0 for d in days)


def test_daily_partial(client, auth_headers):
    # 仅第 1 天（最老那天）灌 1 条
    _save_daily(client, auth_headers, 77, f"{_day(-29)}T10:00:00")

    res = client.post("/api/v1/analysis/daily", json={"days": 30}, headers=auth_headers).json()
    assert res["code"] == 0
    days = res["data"]["days"]
    assert len(days) == 30
    # 仅第 1 天 total>0
    assert days[0]["total"] == 77
    assert all(d["total"] == 0 for d in days[1:])


def test_daily_requires_auth(client):
    res = client.post("/api/v1/analysis/daily", json={"days": 7})
    assert res.status_code == 401
    assert res.json()["code"] == 40100


def test_daily_days_zero(client, auth_headers):
    res = client.post("/api/v1/analysis/daily", json={"days": 0}, headers=auth_headers)
    assert res.status_code == 422
    assert res.json()["code"] == 42200


def test_daily_days_too_large(client, auth_headers):
    res = client.post("/api/v1/analysis/daily", json={"days": 366}, headers=auth_headers)
    assert res.status_code == 422
    assert res.json()["code"] == 42200


def test_daily_soft_delete_filtered(client, auth_headers):
    # 灌 2 条
    r1 = _save_daily(client, auth_headers, 100, f"{_day(0)}T10:00:00")
    _save_daily(client, auth_headers, 50, f"{_day(0)}T12:00:00")
    # 软删第 1 条
    bill_id = r1.json()["data"]["id"]
    assert client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers).status_code == 200

    res = client.post("/api/v1/analysis/daily", json={"days": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    assert res["data"]["days"][0]["total"] == 50


def test_daily_user_isolation(client, auth_headers):
    # 用户 A 灌数据
    _save_daily(client, auth_headers, 999, f"{_day(0)}T10:00:00")
    # 用户 B 登录
    res_b = client.post("/api/v1/user/login", json={"code": "other"})
    assert res_b.status_code == 200
    headers_b = {"Authorization": f"Bearer {res_b.json()['data']['token']}"}

    res = client.post("/api/v1/analysis/daily", json={"days": 1}, headers=headers_b).json()
    assert res["code"] == 0
    assert res["data"]["days"][0]["total"] == 0


def test_daily_timezone_edge(client, auth_headers):
    # 灌一条北京时间凌晨 00:30 的数据（UTC 为前一天 16:30）
    today_str = _day(0)
    yesterday_str = _day(-1)
    _save_daily(client, auth_headers, 120, f"{today_str}T00:30:00+08:00")

    res = client.post("/api/v1/analysis/daily", json={"days": 30}, headers=auth_headers).json()
    assert res["code"] == 0
    days = {d["date"]: d["total"] for d in res["data"]["days"]}
    # 该条计入今天而非昨天
    assert days[today_str] == 120
    assert days[yesterday_str] == 0


# ------------------------------ T-010: category ------------------------------ #


def _month_day(month_offset: int, day: int = 15) -> str:
    """相对今天的月份日期字符串，month_offset=0 表本月。"""
    from datetime import datetime

    from dateutil.relativedelta import relativedelta

    d = datetime.now() - relativedelta(months=month_offset)
    return d.replace(day=day).strftime("%Y-%m-%dT%H:%M:%S")


def test_category_basic(client, auth_headers):
    # 灌 3 类（餐饮 100、交通 50、购物 30）
    _save_category(client, auth_headers, 100, "餐饮", _month_day(0))
    _save_category(client, auth_headers, 50, "交通", _month_day(0))
    _save_category(client, auth_headers, 30, "购物", _month_day(0))

    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    data = res["data"]
    assert len(data["categories"]) == 3
    assert data["total"] == 180
    # percent 求和 ≈ 1（允许 ±0.001）
    assert abs(sum(c["percent"] for c in data["categories"]) - 1.0) < 0.001
    # 降序
    amounts = [c["amount"] for c in data["categories"]]
    assert amounts == sorted(amounts, reverse=True)


def test_category_single(client, auth_headers):
    _save_category(client, auth_headers, 200, "餐饮", _month_day(0))

    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    data = res["data"]
    assert len(data["categories"]) == 1
    assert data["categories"][0]["percent"] == 1.0
    assert data["total"] == 200


def test_category_empty(client, auth_headers):
    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    assert res["data"]["categories"] == []
    assert res["data"]["total"] == 0


def test_category_requires_auth(client):
    res = client.post("/api/v1/analysis/category")
    assert res.status_code == 401
    assert res.json()["code"] == 40100


def test_category_months_zero(client, auth_headers):
    res = client.post("/api/v1/analysis/category", json={"months": 0}, headers=auth_headers)
    assert res.status_code == 422
    assert res.json()["code"] == 42200


def test_category_months_too_large(client, auth_headers):
    res = client.post("/api/v1/analysis/category", json={"months": 13}, headers=auth_headers)
    assert res.status_code == 422
    assert res.json()["code"] == 42200


def test_category_soft_delete_filtered(client, auth_headers):
    # 灌 2 条（餐饮 100 + 交通 50）
    r1 = _save_category(client, auth_headers, 100, "餐饮", _month_day(0))
    _save_category(client, auth_headers, 50, "交通", _month_day(0))
    # 软删餐饮
    bill_id = r1.json()["data"]["id"]
    assert client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers).status_code == 200

    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    assert len(res["data"]["categories"]) == 1
    assert res["data"]["categories"][0]["category"] == "交通"
    assert res["data"]["total"] == 50


def test_category_user_isolation(client, auth_headers):
    # 用户 A 灌数据
    _save_category(client, auth_headers, 999, "餐饮", _month_day(0))
    # 用户 B 登录
    res_b = client.post("/api/v1/user/login", json={"code": "other"})
    assert res_b.status_code == 200
    headers_b = {"Authorization": f"Bearer {res_b.json()['data']['token']}"}

    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=headers_b).json()
    assert res["code"] == 0
    assert res["data"]["total"] == 0


def test_category_empty_category_fallback(client, auth_headers):
    _save_category(client, auth_headers, 50, "", _month_day(0))

    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    assert res["data"]["categories"][0]["category"] == "其他"


def test_category_time_boundary(client, auth_headers):
    # 灌 2 个月前数据 + 1 条今天数据
    _save_category(client, auth_headers, 999, "餐饮", _month_day(2))
    _save_category(client, auth_headers, 100, "交通", _month_day(0))

    res = client.post("/api/v1/analysis/category", json={"months": 1}, headers=auth_headers).json()
    assert res["code"] == 0
    # 仅统计今天那条
    assert res["data"]["total"] == 100
    assert len(res["data"]["categories"]) == 1
    assert res["data"]["categories"][0]["category"] == "交通"
