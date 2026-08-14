"""账单接口：上传、识别、保存、列表；鉴权与异常路径。"""
from __future__ import annotations

import io


def _png_bytes() -> bytes:
    """最小的合法 PNG，避免外部文件依赖。"""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
        b"\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_upload_requires_auth(client):
    res = client.post(
        "/api/v1/bill/upload",
        files={"file": ("wechat.png", _png_bytes(), "image/png")},
    )
    assert res.status_code == 401
    assert res.json()["code"] == 40100


def test_upload_and_recognize_and_save_and_list(client, auth_headers):
    # 1) 上传
    up = client.post(
        "/api/v1/bill/upload",
        files={"file": ("wechat.png", _png_bytes(), "image/png")},
        headers=auth_headers,
    ).json()
    assert up["code"] == 0
    image_id = up["data"]["image_id"]
    assert image_id

    # 2) 识别
    rec = client.post(
        "/api/v1/bill/recognize",
        json={"image_id": image_id},
        headers=auth_headers,
    ).json()
    assert rec["code"] == 0
    assert "amount" in rec["data"]
    assert "merchant" in rec["data"]

    # 3) 保存
    save = client.post(
        "/api/v1/bill/save",
        json={
            "amount": 35.8,
            "category": "餐饮",
            "merchant": "星巴克",
            "pay_method": "微信支付",
            "bill_time": "2026-08-11T12:30:00",
            "source": "image_ai",
            "ai_score": 0.85,
            "image_id": image_id,
        },
        headers=auth_headers,
    ).json()
    assert save["code"] == 0
    assert save["data"]["id"] > 0

    # 4) 列表
    lst = client.get(
        "/api/v1/bill/list",
        params={"page": 1, "size": 10, "category": "餐饮"},
        headers=auth_headers,
    ).json()
    assert lst["code"] == 0
    assert lst["data"]["total"] >= 1
    assert any(item["merchant"] == "星巴克" for item in lst["data"]["items"])


def test_list_invalid_date(client, auth_headers):
    res = client.get(
        "/api/v1/bill/list",
        params={"date": "not-a-date"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40000


def test_recognize_unknown_image(client, auth_headers):
    res = client.post(
        "/api/v1/bill/recognize",
        json={"image_id": "does-not-exist"},
        headers=auth_headers,
    )
    body = res.json()
    assert body["code"] == 40400


def test_save_rejects_non_positive_amount(client, auth_headers):
    res = client.post(
        "/api/v1/bill/save",
        json={
            "amount": 0,
            "category": "餐饮",
            "bill_time": "2026-08-11T12:30:00",
        },
        headers=auth_headers,
    )
    assert res.status_code == 422


# ----------------------------- T-002: get_bill ----------------------------- #

def _save_one(client, headers, **overrides) -> int:
    body = {
        "amount": 35.8, "category": "餐饮", "merchant": "星巴克",
        "pay_method": "微信支付", "bill_time": "2026-08-11T12:30:00",
        "source": "image_ai", "ai_score": 0.85, "remark": "",
    }
    body.update(overrides)
    r = client.post("/api/v1/bill/save", json=body, headers=headers).json()
    return r["data"]["id"]


def test_get_bill_success(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.get(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["id"] == bill_id
    assert body["data"]["amount"] == 35.8
    assert body["data"]["merchant"] == "星巴克"
    assert body["data"]["source"] == "image_ai"
    assert body["data"]["remark"] == ""
    expected_keys = {
        "id", "amount", "category", "merchant", "pay_method",
        "bill_time", "remark", "source", "ai_score",
    }
    assert set(body["data"].keys()) == expected_keys


def test_get_bill_not_found(client, auth_headers):
    res = client.get("/api/v1/bill/999999", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400
    assert body["message"]


def test_get_bill_forbidden_returns_404(client):
    # 用户 A 创建账单
    res_a = client.post("/api/v1/user/login", json={"code": "user-a"})
    headers_a = {"Authorization": f"Bearer {res_a.json()['data']['token']}"}
    bill_id = _save_one(client, headers_a)

    # 用户 B 登录并尝试访问
    res_b = client.post("/api/v1/user/login", json={"code": "other-user"})
    headers_b = {"Authorization": f"Bearer {res_b.json()['data']['token']}"}
    res = client.get(f"/api/v1/bill/{bill_id}", headers=headers_b)
    assert res.status_code == 200
    assert res.json()["code"] == 40400
    # 与不存在的账单响应完全等价（侧信道）
    res_missing = client.get("/api/v1/bill/999999", headers=headers_b)
    assert res_missing.status_code == res.status_code
    assert res_missing.json() == res.json()


def test_get_bill_requires_auth(client):
    res = client.get("/api/v1/bill/1")
    assert res.status_code == 401
    assert res.json()["code"] == 40100


def test_get_bill_id_must_be_int(client, auth_headers):
    res = client.get("/api/v1/bill/abc", headers=auth_headers)
    assert res.status_code == 422
    body = res.json()
    assert body["code"] == 40000
    assert isinstance(body["data"], list)
