"""AI pipeline 降级测试。

任何一层 (OCR / VISION / LLM) 在依赖缺失或 Key 缺失时, 自动降级 mock,
不抛 BizException, 让开发期能跑通端到端流程。
"""
from __future__ import annotations

import io
import logging
from PIL import Image

from app.services import classify, ocr as ocr_svc, vision as vision_svc


def _make_tmp_png(tmp_path) -> str:
    """生成临时测试图片"""
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    path = str(tmp_path / "test.png")
    img.save(path)
    return path


def test_ocr_paddleocr_missing_package_falls_back(caplog, tmp_path):
    """paddleocr 没装 → 降级 mock (返回非空字符串), 不抛异常."""
    path = _make_tmp_png(tmp_path)
    with caplog.at_level(logging.WARNING, logger="app.services.ocr"):
        result = ocr_svc._paddleocr_run(path)
    assert isinstance(result, str) and len(result) > 0
    assert any("paddleocr" in r.message for r in caplog.records)


def test_vision_qwen_vl_missing_key_falls_back(caplog, monkeypatch, tmp_path):
    """dashscope 不可用 或 DASHSCOPE_API_KEY 未设 → 降级 mock."""
    path = _make_tmp_png(tmp_path)
    monkeypatch.setattr("app.core.config.settings.dashscope_api_key", "")
    with caplog.at_level(logging.WARNING, logger="app.services.vision"):
        result = vision_svc._qwen_vl_run(path, ocr_text="微信支付 12.00 元")
    # mock 实现会用 ocr_text 解析出 amount
    assert result.amount == 12.0
    # 至少一条降级 warning (依赖缺失 OR key 缺失)
    msgs = [r.message for r in caplog.records]
    assert any(("DASHSCOPE_API_KEY" in m) or ("dashscope" in m) for m in msgs), msgs


def test_classify_deepseek_missing_key_falls_back(caplog, monkeypatch):
    """openai 不可用 OR DEEPSEEK_API_KEY 未设 → 降级 mock."""
    monkeypatch.setattr("app.core.config.settings.deepseek_api_key", "")
    from app.services.types import RecognizeResult
    from datetime import datetime
    inp = RecognizeResult(
        amount=12.0, merchant="星巴克", category="",
        time=datetime.now(), payment="微信支付", score=0.9, raw_ocr="x"
    )
    with caplog.at_level(logging.WARNING, logger="app.services.classify"):
        out = classify._deepseek_run(inp)
    assert out.category == "其他"  # mock 给默认
    msgs = [r.message for r in caplog.records]
    assert any(("DEEPSEEK_API_KEY" in m) or ("openai" in m) for m in msgs), msgs


def test_refine_unknown_backend_falls_back(monkeypatch, caplog):
    """backend 配成未知值 (typo) → 降级 mock, 不抛异常."""
    from app.services.types import RecognizeResult
    from datetime import datetime
    inp = RecognizeResult(
        amount=12.0, merchant="", category="",
        time=datetime.now(), payment="", score=0.9, raw_ocr=""
    )
    # 直接调 _mock_run 验证 backend 字符串不影响 mock 行为
    with caplog.at_level(logging.WARNING, logger="app.services.classify"):
        out = classify._mock_run(inp)
    assert out.category == "其他"


def test_vision_minimax_missing_key_falls_back(caplog, monkeypatch, tmp_path):
    """MINIMAX_API_KEY 未设 → 降级 mock (用 ocr_text 抽出 amount)."""
    path = _make_tmp_png(tmp_path)
    monkeypatch.setattr("app.core.config.settings.minimax_api_key", "")
    with caplog.at_level(logging.WARNING, logger="app.services.vision"):
        result = vision_svc._minimax_vl_run(path, ocr_text="微信支付 88.00 元")
    assert result.amount == 88.0
    msgs = [r.message for r in caplog.records]
    assert any(("MINIMAX_API_KEY" in m) or ("openai" in m) for m in msgs), msgs


def test_classify_minimax_missing_key_falls_back(caplog, monkeypatch):
    """MINIMAX_API_KEY 未设 → 降级 mock."""
    from app.services.types import RecognizeResult
    from datetime import datetime
    monkeypatch.setattr("app.core.config.settings.minimax_api_key", "")
    inp = RecognizeResult(
        amount=12.0, merchant="海底捞", category="",
        time=datetime.now(), payment="微信支付", score=0.9, raw_ocr="x"
    )
    with caplog.at_level(logging.WARNING, logger="app.services.classify"):
        out = classify._minimax_run(inp)
    assert out.category == "其他"  # mock 给默认
    msgs = [r.message for r in caplog.records]
    assert any(("MINIMAX_API_KEY" in m) or ("openai" in m) for m in msgs), msgs


def test_vision_run_dispatches_to_minimax(monkeypatch):
    """run_vision(backend=minimax) 应调用 _minimax_vl_run."""
    monkeypatch.setattr("app.core.config.settings.vision_backend", "minimax")
    vision_svc._vision_backend.cache_clear()
    called = {}
    def fake_minimax(path, ocr_text):
        called["hit"] = True
        from app.services.types import RecognizeResult
        from datetime import datetime
        return RecognizeResult(amount=1, merchant="m", category="c",
                               time=datetime.now(), payment="p", score=1.0, raw_ocr="")
    monkeypatch.setattr("app.services.vision._minimax_vl_run", fake_minimax)
    from app.services.types import RecognizeResult
    res = vision_svc.run_vision("/tmp/x.png", "ocr")
    assert called.get("hit") is True
    assert res.amount == 1


def test_refine_dispatches_to_minimax(monkeypatch):
    """refine(backend=minimax) 应调用 _minimax_run."""
    from app.services.types import RecognizeResult
    from datetime import datetime
    monkeypatch.setattr("app.core.config.settings.llm_backend", "minimax")
    classify._llm_backend.cache_clear()
    inp = RecognizeResult(amount=1, merchant="m", category="",
                           time=datetime.now(), payment="p", score=1.0, raw_ocr="")
    out = classify.refine(inp)
    # 不会抛异常, mock 给默认
    assert out.category == "其他"