"""自定义异常 + 全局处理。"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import fail

logger = logging.getLogger(__name__)


class BizException(Exception):
    """业务异常：携带 code / message。"""

    def __init__(self, code: int, message: str, status_code: int = status.HTTP_200_OK) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizException)
    async def _biz(_: Request, exc: BizException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(fail(exc.code, exc.message)),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # 把 Pydantic ValidationError 列表简化为 {field: msg} 字典
        # 前端按字段名直接展示在对应 input 旁
        errors: dict[str, str] = {}
        for err in exc.errors():
            loc = err.get("loc", ())
            field = str(loc[-1]) if loc else "_"
            # 同字段多错时取第一条
            errors.setdefault(field, err.get("msg", "校验失败"))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(fail(42200, "请求参数校验失败", data=errors)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(fail(50000, "服务内部错误")),
        )
