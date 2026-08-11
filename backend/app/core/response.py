"""统一响应包装：code / message / data。

约定：
    0 业务成功
    40000 通用业务错误
    40100 未登录 / token 失效
    40300 无权限
    40400 资源不存在
    50000 服务端异常
"""
from __future__ import annotations

from typing import Any


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}
