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


def test_monthly_empty(client, auth_headers):
    res = client.post("/api/v1/analysis/monthly", headers=auth_headers).json()
    assert res["code"] == 0
    assert res["data"]["total"] == 0


def test_monthly_sums_and_top(client, auth_headers):
    _save(client, auth_headers, 30, "餐饮", "2026-08-01T10:00:00")
    _save(client, auth_headers, 80, "餐饮", "2026-08-05T10:00:00")
    _save(client, auth_headers, 50, "交通", "2026-08-08T10:00:00")

    res = client.post("/api/v1/analysis/monthly", headers=auth_headers).json()
    assert res["code"] == 0
    data = res["data"]
    assert data["total"] == 160
    assert data["top_category"] == "餐饮"
    assert "餐饮" in data["advice"]


def test_monthly_requires_auth(client):
    res = client.post("/api/v1/analysis/monthly")
    assert res.status_code == 401
