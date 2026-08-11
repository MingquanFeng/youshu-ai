"""OCR 文字提取。

MVP 阶段默认走 mock：识别图片尺寸/文件名后返回固定示例文本。
生产可替换为 PaddleOCR：见 _paddleocr_run。
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache

from PIL import Image

from app.core.config import settings
from app.core.exceptions import BizException

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _ocr_backend() -> str:
    return settings.ocr_backend.lower()


def run_ocr(image_path: str) -> str:
    """对一张本地图片跑 OCR，返回纯文本。"""
    if not os.path.exists(image_path):
        raise BizException(40400, "图片不存在", status_code=404)

    backend = _ocr_backend()
    if backend == "paddleocr":
        return _paddleocr_run(image_path)
    if backend == "mock":
        return _mock_run(image_path)
    raise BizException(50000, f"未知 OCR 后端: {backend}")


def _mock_run(image_path: str) -> str:
    """本地开发占位：根据文件名粗略生成 OCR 文本，方便端到端联调。"""
    name = os.path.basename(image_path).lower()
    if "wechat" in name or "wx" in name or "微信" in name:
        return "微信支付 35.80 元 星巴克 2026-08-11 12:30"
    if "alipay" in name or "ali" in name or "支付宝" in name:
        return "支付宝 88.00 元 海底捞 2026-08-10 19:15"
    return "微信支付 12.00 元 便利店 2026-08-11 09:00"


def _paddleocr_run(image_path: str) -> str:
    """真实 PaddleOCR 推理。延迟导入避免没装 paddle 时 import 失败。"""
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except ImportError as exc:
        raise BizException(50000, "未安装 paddleocr，无法使用该后端") from exc

    img = Image.open(image_path)
    w, h = img.size
    if w * h > 4000 * 4000:
        raise BizException(40000, "图片过大，请压缩到 16M 像素以下")

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    result = ocr.ocr(image_path, cls=True)
    lines: list[str] = []
    for page in result or []:
        for box in page or []:
            txt = box[1][0] if box and len(box) >= 2 else ""
            if txt:
                lines.append(txt)
    return "\n".join(lines)
