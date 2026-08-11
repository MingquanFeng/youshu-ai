"""用户接口。"""
from __future__ import annotations


def test_login_returns_token_and_creates_user(client):
    res = client.post("/api/v1/user/login", json={"code": "abc"})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    data = body["data"]
    assert "token" in data and len(data["token"]) > 20
    assert data["user_id"] > 0


def test_login_same_openid_returns_same_user(client):
    r1 = client.post("/api/v1/user/login", json={"code": "same"}).json()["data"]
    r2 = client.post("/api/v1/user/login", json={"code": "same"}).json()["data"]
    assert r1["user_id"] == r2["user_id"]


def test_login_rejects_missing_code(client):
    res = client.post("/api/v1/user/login", json={})
    assert res.status_code == 422
