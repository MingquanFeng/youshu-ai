"""视觉模型层。

MVP 用 mock：基于 OCR 文本抽取结构化信息。
生产可以替换为 Qwen3-VL 多模态直接读图，跳过 OCR。
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from functools import lru_cache

from app.core.config import settings
from app.core.exceptions import BizException
from app.services.types import RecognizeResult

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _vision_backend() -> str:
    return settings.vision_backend.lower()


def run_vision(image_path: str, ocr_text: str) -> RecognizeResult:
    backend = _vision_backend()
    if backend == "qwen-vl":
        return _qwen_vl_run(image_path, ocr_text)
    if backend == "mock":
        return _mock_run(image_path, ocr_text)
    raise BizException(50000, f"未知视觉后端: {backend}")


# ------------------------------ mock 实现 ------------------------------ #

_AMOUNT_RE = re.compile(r"(\d+(?:\.\d+)?)")
_DATE_RE = re.compile(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}(?:日)?(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?)")


def _mock_run(image_path: str, ocr_text: str) -> RecognizeResult:
    text = ocr_text or ""
    amount = 0.0
    m = _AMOUNT_RE.search(text)
    if m:
        amount = float(m.group(1))

    pay = ""
    if "微信" in text:
        pay = "微信支付"
    elif "支付宝" in text:
        pay = "支付宝"

    merchant = ""
    parts = text.split()
    if len(parts) >= 2:
        merchant = parts[1]

    time = datetime.now()
    d = _DATE_RE.search(text)
    if d:
        raw = d.group(1).replace("年", "-").replace("月", "-").replace("日", "")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                time = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue

    return RecognizeResult(
        amount=amount,
        merchant=merchant,
        category=_guess_category(merchant),
        time=time,
        payment=pay,
        score=0.85,
        raw_ocr=text,
    )


# ------------------------------ Qwen-VL ------------------------------ #

QWEN_PROMPT = """你是专业记账助手。
从消费图片中提取：
- 金额
- 商户
- 时间
- 支付方式
- 消费分类
只返回 JSON，不要解释。"""


def _qwen_vl_run(image_path: str, ocr_text: str) -> RecognizeResult:
    """真实 Qwen-VL 多模态调用：图片 + prompt，返回 JSON。"""
    try:
        import dashscope  # type: ignore
        from dashscope import MultiModalConversation  # type: ignore
    except ImportError as exc:
        raise BizException(50000, "未安装 dashscope，无法使用 Qwen-VL 后端") from exc

    if not settings.dashscope_api_key:
        raise BizException(50000, "缺少 DASHSCOPE_API_KEY")

    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{os.path.abspath(image_path)}"},
                {"text": QWEN_PROMPT},
            ],
        }
    ]
    resp = MultiModalConversation.call(
        model="qwen-vl-plus",
        messages=messages,
        api_key=settings.dashscope_api_key,
    )
    content = resp.output.choices[0].message.content
    text = content[0]["text"] if isinstance(content, list) else str(content)

    import json

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BizException(50000, f"Qwen-VL 返回非 JSON: {text[:200]}") from exc

    return RecognizeResult(
        amount=float(data.get("amount", 0)),
        merchant=str(data.get("merchant", "")),
        category=str(data.get("category") or "其他"),
        time=datetime.fromisoformat(data["time"]) if "time" in data else datetime.now(),
        payment=str(data.get("payment") or data.get("pay_method", "")),
        score=0.95,
        raw_ocr=ocr_text,
    )


_CATEGORY_KEYWORDS = {
    "餐饮": ["星巴克", "麦当劳", "肯德基", "海底捞", "瑞幸", "美团", "饿了么", "餐厅", "食堂"],
    "交通": ["滴滴", "高德", "出租车", "公交", "地铁", "高铁", "12306"],
    "购物": ["淘宝", "京东", "拼多多", "便利店", "超市", "沃尔玛"],
    "娱乐": ["影院", "电影", "KTV", "剧本杀", "密室"],
}


def _guess_category(merchant: str) -> str:
    for cat, kws in _CATEGORY_KEYWORDS.items():
        if any(k in merchant for k in kws):
            return cat
    return "其他"
