"""视觉模型层。

MVP 用 mock：基于 OCR 文本抽取结构化信息。
生产可以替换为 Qwen3-VL 或 MiniMax-VL 多模态直接读图，跳过 OCR。
"""
from __future__ import annotations

import base64
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
    """视觉模型：缺依赖/key 自动降级 mock."""
    backend = _vision_backend()
    if backend == "qwen-vl":
        return _qwen_vl_run(image_path, ocr_text)
    if backend == "minimax":
        return _minimax_vl_run(image_path, ocr_text)
    if backend == "mock":
        return _mock_run(image_path, ocr_text)
    logger.warning("未知视觉后端: %s, 降级 mock", backend)
    return _mock_run(image_path, ocr_text)


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
        direction=_guess_direction(pay, merchant, text),
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
**只返回纯 JSON, 不要 markdown 代码块标记, 不要解释, 不要前后缀**。字段: amount (数字, 元) / merchant (字符串) / category (餐饮/交通/购物/居家/娱乐/医疗/其他) / time (ISO 8601) / payment (微信支付/支付宝/银行卡/现金 等)"""


def _qwen_vl_run(image_path: str, ocr_text: str) -> RecognizeResult:
    """真实 Qwen-VL 多模态调用：图片 + prompt，返回 JSON。

    依赖或 key 缺失 → 降级 mock + warning, 不中断请求。
    这样开发期没装 dashscope 也能端到端跑, 生产填了 key 自动切真模型。
    """
    try:
        from dashscope import MultiModalConversation  # type: ignore
    except ImportError:
        logger.warning(
            "dashscope 未安装 (pip install -e '.[ai]'), 降级到 mock vision. 文件: %s",
            image_path,
        )
        return _mock_run(image_path, ocr_text)

    if not settings.dashscope_api_key:
        logger.warning("DASHSCOPE_API_KEY 未设置, 降级到 mock vision. 文件: %s", image_path)
        return _mock_run(image_path, ocr_text)

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
    import re

    # 容错提取 JSON: 模型偶尔返回 markdown ```json ... ``` 包裹或前后有杂文本
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise BizException(50000, f"Qwen-VL 返回非 JSON: {text[:200]}") from None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise BizException(50000, f"Qwen-VL 返回非 JSON: {text[:200]}") from exc

    raw_amount = float(data.get("amount", 0))
    amount = abs(raw_amount) if raw_amount != 0 else 0.01
    # LLM 识别 direction: 红包/收款/退款/转入零钱 → income, 其余 expense
    direction = _guess_direction(
        str(data.get("payment", "")),
        str(data.get("merchant", "")),
        ocr_text
    )
    return RecognizeResult(
        amount=amount,
        direction=direction,
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


_INCOME_KEYWORDS = [
    # 直接关键词
    "收款", "收到", "转入", "退款", "红包", "转账收", "入账",
    "零钱通", "零钱收入", "提现到账", "已到账", "已收款", "已到账",
    "退还", "返款", "报销", "工资", "退款成功", "提现", "余额宝",
    # 节日/礼金/转账描述
    "七夕", "生日", "新年", "春节", "中秋", "圣诞", "感恩", "教师",
    "礼金", "红包", "压岁", "恭喜", "祝福", "感谢", "转账",
    "还款", "借入", "退款", "红包来", "对方", "来自",
]


def _guess_direction(payment: str, merchant: str, raw_ocr: str = "") -> str:
    """从支付方式/商户/OCR 文本启发判断 收入/支出.

    默认 expense (支出), 命中收入关键字 → income.
    """
    text = " ".join([payment or "", merchant or "", raw_ocr or ""])
    for kw in _INCOME_KEYWORDS:
        if kw in text:
            return "income"
    return "expense"


# ------------------------------ MiniMax-VL ------------------------------ #

VISION_PROMPT = """你是专业记账助手。从这张消费图片(支付截图/小票/订单截图)中提取结构化信息,只返回 JSON:
{
  "amount": 数字 (元, 必填, 取最明显的成交金额),
  "merchant": 商家名称字符串,
  "category": 消费分类 (餐饮/交通/购物/居家/娱乐/医疗/其他 七选一),
  "time": ISO 8601 时间字符串 (从图中读取, 不可读时用当前时间),
  "payment": 支付方式 (微信支付/支付宝/银行卡/现金 等)
}
只输出 JSON, 不要解释, 不要 markdown 代码块标记。"""


def _minimax_vl_run(image_path: str, ocr_text: str) -> RecognizeResult:
    """MiniMax-VL 多模态调用: 用 OpenAI 兼容 client, image 转 base64 内联。

    缺包 (openai 没装) / 缺 key → 降级 mock + warning。
    """
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        logger.warning(
            "openai 未安装 (pip install openai), 降级到 mock vision. 文件: %s", image_path
        )
        return _mock_run(image_path, ocr_text)

    if not settings.minimax_api_key:
        logger.warning(
            "MINIMAX_API_KEY 未设置, 降级到 mock vision. 文件: %s", image_path
        )
        return _mock_run(image_path, ocr_text)

    # 图片转 base64 data URL (MiniMax API 兼容 OpenAI vision 格式)
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        ext = os.path.splitext(image_path)[1].lstrip(".").lower() or "png"
        image_data_url = f"data:image/{ext};base64,{b64}"
    except OSError as exc:
        logger.warning("读取图片失败: %s, 降级 mock", exc)
        return _mock_run(image_path, ocr_text)

    client = OpenAI(api_key=settings.minimax_api_key, base_url=settings.minimax_base_url)
    resp = client.chat.completions.create(
        model=settings.minimax_vl_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=512,
    )
    import json

    text = resp.choices[0].message.content
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BizException(50000, f"MiniMax-VL 返回非 JSON: {text[:200]}") from exc

    direction = _guess_direction(
        str(data.get("payment", "")),
        str(data.get("merchant", "")),
        ""
    )
    return RecognizeResult(
        amount=float(data.get("amount", 0)),
        direction=direction,
        merchant=str(data.get("merchant", "")),
        category=str(data.get("category") or "其他"),
        time=datetime.fromisoformat(data["time"]) if "time" in data else datetime.now(),
        payment=str(data.get("payment") or data.get("pay_method", "")),
        score=0.95,
        raw_ocr=ocr_text,
    )
