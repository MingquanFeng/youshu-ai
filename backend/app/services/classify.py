"""文本分析层：把 vision 输出再用 LLM 校验/分类。

MVP 用关键词直接分类。生产可接 DeepSeek / MiniMax 做兜底纠错与建议生成。
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings
from app.services.types import RecognizeResult

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _llm_backend() -> str:
    return settings.llm_backend.lower()


def refine(result: RecognizeResult) -> RecognizeResult:
    """对 vision 结果做二次校验：修正异常金额、补默认分类。

    backend 缺失依赖/Key 时自动降级 mock, 不中断请求。
    """
    backend = _llm_backend()
    if backend == "deepseek":
        return _deepseek_run(result)
    if backend == "minimax":
        return _minimax_run(result)
    if backend == "mock":
        return _mock_run(result)
    logger.warning("未知 LLM 后端: %s, 降级 mock", backend)
    return _mock_run(result)


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
    except ImportError:
        logger.warning(
            "openai 未安装 (pip install -e '.[ai]'), 降级到 mock classify"
        )
        return _mock_run(result)

    if not settings.deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY 未设置, 降级到 mock classify")
        return _mock_run(result)

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


def _minimax_run(result: RecognizeResult) -> RecognizeResult:
    """MiniMax 文本模型做识别结果校验/分类 (OpenAI 兼容协议).

    缺包 / 缺 key → 降级 mock.
    注意: MiniMax 不支持 response_format=json_object, prompt 强制要求纯 JSON 输出.
    """
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        logger.warning("openai 未安装, 降级到 mock classify")
        return _mock_run(result)

    if not settings.minimax_api_key:
        logger.warning("MINIMAX_API_KEY 未设置, 降级到 mock classify")
        return _mock_run(result)

    client = OpenAI(api_key=settings.minimax_api_key, base_url=settings.minimax_base_url)
    prompt = (
        "你是记账审查助手。对下面识别结果做合理性检查并修正: "
        f"{result.model_dump_json()}。"
        "只返回 JSON (字段 amount/merchant/category/payment/score), "
        "不要解释, 不要 markdown 代码块, 不要前后缀。"
    )
    resp = client.chat.completions.create(
        model=settings.minimax_text_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )

    import json
    import re

    text = resp.choices[0].message.content.strip()
    # MiniMax 可能返回 markdown 包裹 ```json ... ``` 或前后有杂文本, 提取 JSON
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"MiniMax 返回非 JSON: {text[:200]}")
    data = json.loads(m.group(0))

    return RecognizeResult(
        amount=float(data.get("amount", result.amount)),
        merchant=str(data.get("merchant", result.merchant)),
        category=str(data.get("category", result.category)),
        time=result.time,
        payment=str(data.get("payment", result.payment)),
        score=float(data.get("score", result.score)),
        raw_ocr=result.raw_ocr,
    )
