"""文本分析层：把 vision 输出再用 LLM 校验/分类。

MVP 用关键词直接分类。生产可接 DeepSeek-V3 做兜底纠错与建议生成。
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings
from app.core.exceptions import BizException
from app.services.types import RecognizeResult

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _llm_backend() -> str:
    return settings.llm_backend.lower()


def refine(result: RecognizeResult) -> RecognizeResult:
    """对 vision 结果做二次校验：修正异常金额、补默认分类。"""
    backend = _llm_backend()
    if backend == "deepseek":
        return _deepseek_run(result)
    if backend == "mock":
        return _mock_run(result)
    raise BizException(50000, f"未知 LLM 后端: {backend}")


def _mock_run(result: RecognizeResult) -> RecognizeResult:
    out = result.model_copy()
    if out.amount <= 0 or out.amount > 1_000_000:
        out.score = max(0.0, out.score - 0.4)
    if not out.category:
        out.category = "其他"
    return out


def _deepseek_run(result: RecognizeResult) -> RecognizeResult:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise BizException(50000, "未安装 openai 客户端") from exc

    if not settings.deepseek_api_key:
        raise BizException(50000, "缺少 DEEPSEEK_API_KEY")

    client = OpenAI(api_key=settings.deepseek_api_key, base_url="https://api.deepseek.com")
    prompt = (
        "你是记账审查助手，对下面识别结果做合理性检查，仅返回 JSON："
        f" {result.model_dump_json()}"
    )
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    import json

    data = json.loads(resp.choices[0].message.content)
    return RecognizeResult(
        amount=float(data.get("amount", result.amount)),
        merchant=str(data.get("merchant", result.merchant)),
        category=str(data.get("category", result.category)),
        time=result.time,
        payment=str(data.get("payment", result.payment)),
        score=float(data.get("score", result.score)),
        raw_ocr=result.raw_ocr,
    )
