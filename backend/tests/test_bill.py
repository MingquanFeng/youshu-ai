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


def test_save_rejects_zero_amount(client, auth_headers):
    """amount=0 仍被拒 (无意义, 支出/收入都不能为0), 但负数 (支出) 现在允许."""
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
    assert body["code"] == 42200
    assert isinstance(body["data"], dict)


# ----------------------------- T-003: update_bill ----------------------------- #

def test_update_bill_success(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={
            "amount": 99.5,
            "category": "交通",
            "merchant": "滴滴出行",
            "pay_method": "支付宝",
            "bill_time": "2026-08-12T18:00:00",
            "remark": "加班打车",
        },
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["id"] == bill_id
    assert data["amount"] == 99.5
    assert data["category"] == "交通"
    assert data["merchant"] == "滴滴出行"
    assert data["pay_method"] == "支付宝"
    assert data["bill_time"].startswith("2026-08-12T18:00:00")
    # audit 前缀
    assert data["remark"] == "[修正] 加班打车"
    # 非白名单字段保持原值
    assert data["source"] == "image_ai"
    assert data["ai_score"] == 0.85


def test_update_bill_partial_only_amount(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 99.9},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["amount"] == 99.9
    # 其他 5 个白名单字段保持原值
    assert data["category"] == "餐饮"
    assert data["merchant"] == "星巴克"
    assert data["pay_method"] == "微信支付"
    assert data["bill_time"].startswith("2026-08-11T12:30:00")
    assert data["remark"] == "[修正] "  # audit 前缀


def test_update_bill_ignores_source_in_body(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 10.0, "source": "manual"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["source"] == "image_ai"


def test_update_bill_ignores_ai_score_in_body(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 10.0, "ai_score": 0.1},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["ai_score"] == 0.85


def test_update_bill_not_found(client, auth_headers):
    res = client.put(
        "/api/v1/bill/999999",
        json={"amount": 50.0},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400


def test_update_bill_forbidden_returns_404(client):
    # 用户 A 创建账单
    res_a = client.post("/api/v1/user/login", json={"code": "user-a"})
    headers_a = {"Authorization": f"Bearer {res_a.json()['data']['token']}"}
    bill_id = _save_one(client, headers_a)

    # 用户 B 登录并尝试修改
    res_b = client.post("/api/v1/user/login", json={"code": "other-user"})
    headers_b = {"Authorization": f"Bearer {res_b.json()['data']['token']}"}
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 1.0},
        headers=headers_b,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400
    # 与 not_found 响应等价（侧信道）
    res_missing = client.put(
        "/api/v1/bill/999999",
        json={"amount": 1.0},
        headers=headers_b,
    )
    assert res_missing.status_code == res.status_code
    assert res_missing.json() == res.json()


def test_update_bill_requires_auth(client):
    res = client.put("/api/v1/bill/1", json={"amount": 50.0})
    assert res.status_code == 401
    assert res.json()["code"] == 40100


def test_update_bill_rejects_zero_amount_allows_negative(client, auth_headers):
    """amount=0 仍 422, amount<0 (支出) 现在允许."""
    bill_id = _save_one(client, auth_headers)
    # 0 仍被拒
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 0},
        headers=auth_headers,
    )
    assert res.status_code == 422
    assert res.json()["code"] == 42200
    # 负数 (支出) 允许
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": -50.0},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["code"] == 0


def test_update_bill_empty_body_rejected(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40000
    assert "至少更新一个字段" in body["message"]


def test_update_bill_id_must_be_int(client, auth_headers):
    res = client.put(
        "/api/v1/bill/abc",
        json={"amount": 50.0},
        headers=auth_headers,
    )
    assert res.status_code == 422
    body = res.json()
    assert body["code"] == 42200


def test_update_bill_adds_correction_marker_to_remark(client, auth_headers):
    bill_id = _save_one(client, auth_headers, remark="午餐")
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 60.0},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["remark"] == "[修正] 午餐"


# ----------------------------- T-004: delete_bill ----------------------------- #

def _login_headers(client, code: str = "pytest") -> dict[str, str]:
    """登录拿到 token，返回可直接放进请求头的 dict（不同于 session-scoped auth_headers）。"""
    res = client.post("/api/v1/user/login", json={"code": code})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['data']['token']}"}


def test_delete_bill_success(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    res = client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["id"] == bill_id
    assert body["data"]["deleted_at"]  # 非空字符串


def test_delete_bill_soft_deleted_hidden_from_list(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    # 删前能查到
    lst_before = client.get("/api/v1/bill/list", headers=auth_headers).json()
    assert any(item["id"] == bill_id for item in lst_before["data"]["items"])

    # 软删
    client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers)

    # 删后查不到
    lst_after = client.get("/api/v1/bill/list", headers=auth_headers).json()
    assert all(item["id"] != bill_id for item in lst_after["data"]["items"])


def test_delete_bill_get_returns_404_after_delete(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    res = client.get(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400
    assert body["message"]


def test_delete_bill_update_returns_404_after_delete(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    res = client.put(
        f"/api/v1/bill/{bill_id}",
        json={"amount": 99.0},
        headers=auth_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400


def test_delete_bill_repeat_returns_404(client, auth_headers):
    bill_id = _save_one(client, auth_headers)
    # 第一次删成功
    first = client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    assert first.json()["code"] == 0

    # 重复删：deleted_at 已非空，filter 查不到，返 404
    second = client.delete(f"/api/v1/bill/{bill_id}", headers=auth_headers)
    assert second.status_code == 200
    assert second.json()["code"] == 40400


def test_delete_bill_not_found(client, auth_headers):
    res = client.delete("/api/v1/bill/999999", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400


def test_delete_bill_forbidden_returns_404(client):
    # 用户 A 创建账单
    headers_a = _login_headers(client, "user-a")
    bill_id = _save_one(client, headers_a)

    # 用户 B 登录并尝试删除
    headers_b = _login_headers(client, "other-user")
    res = client.delete(f"/api/v1/bill/{bill_id}", headers=headers_b)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 40400
    # 与 not_found 响应等价（侧信道）
    res_missing = client.delete("/api/v1/bill/999999", headers=headers_b)
    assert res_missing.status_code == res.status_code
    assert res_missing.json() == res.json()


def test_delete_bill_requires_auth(client):
    res = client.delete("/api/v1/bill/1")
    assert res.status_code == 401
    assert res.json()["code"] == 40100


def test_delete_bill_id_must_be_int(client, auth_headers):
    res = client.delete("/api/v1/bill/abc", headers=auth_headers)
    assert res.status_code == 422
    body = res.json()
    assert body["code"] == 42200
    assert isinstance(body["data"], dict)
