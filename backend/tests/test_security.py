"""JWT_SECRET 启动校验测试。

dev/test: 默认值/弱 secret 只 warning, 不阻塞
prod:     默认值/弱 secret 必须 raise RuntimeError
"""
from __future__ import annotations

import logging

import pytest

from app.core.security import (
    DEV_DEFAULT_SECRET,
    MIN_SECRET_LENGTH,
    validate_jwt_secret,
)


def test_dev_default_secret_only_warns(caplog):
    """dev 环境: 默认值只 warning, 不 raise."""
    with caplog.at_level(logging.WARNING, logger="app.core.security"):
        validate_jwt_secret("dev", DEV_DEFAULT_SECRET)  # 不抛异常
    assert any("JWT_SECRET 是 dev 默认值" in r.message for r in caplog.records)


def test_dev_short_secret_only_warns(caplog):
    """dev 环境: 弱 secret 也只 warning."""
    with caplog.at_level(logging.WARNING, logger="app.core.security"):
        validate_jwt_secret("dev", "abc")  # 不抛
    assert any("JWT_SECRET 太短" in r.message for r in caplog.records)


def test_dev_strong_secret_passes():
    """dev 环境: 强 secret (≥32 字符 + 不是 dev 默认) 通过."""
    strong = "a" * 64  # 64 chars, 远高于 32 阈值
    validate_jwt_secret("dev", strong)  # 不抛


def test_prod_default_secret_raises():
    """prod 环境: 默认值必须 raise."""
    with pytest.raises(RuntimeError) as exc:
        validate_jwt_secret("prod", DEV_DEFAULT_SECRET)
    assert "FATAL" in str(exc.value)
    assert "dev 默认值" in str(exc.value)


def test_prod_short_secret_raises():
    """prod 环境: 弱 secret raise."""
    with pytest.raises(RuntimeError) as exc:
        validate_jwt_secret("prod", "short")
    assert "FATAL" in str(exc.value)
    assert "太短" in str(exc.value)


def test_prod_strong_secret_passes():
    """prod 环境: 强 secret 通过."""
    strong = "a" * MIN_SECRET_LENGTH
    validate_jwt_secret("prod", strong)  # 不抛


def test_boundary_exactly_min_length():
    """正好 32 字符: 视为通过 (边界)."""
    secret = "x" * MIN_SECRET_LENGTH
    assert secret != DEV_DEFAULT_SECRET  # 避免默认值巧合
    validate_jwt_secret("prod", secret)  # 不抛


def test_just_below_min_length_raises_in_prod():
    """31 字符: prod raise (差 1 字符也算弱)."""
    with pytest.raises(RuntimeError):
        validate_jwt_secret("prod", "x" * (MIN_SECRET_LENGTH - 1))


def test_error_message_includes_remediation():
    """错误信息应包含如何生成强 secret 的命令."""
    with pytest.raises(RuntimeError) as exc:
        validate_jwt_secret("prod", DEV_DEFAULT_SECRET)
    assert "openssl rand -hex 32" in str(exc.value)