# 真模型接入指南

三层 AI pipeline，**任何一层缺失依赖 / Key 自动降级 mock + warning log**，不中断请求。这样：
- 开发期不装 dashscope/openai/paddleocr 也能端到端跑通
- 生产填了 Key + 装依赖自动切真模型

## 三层架构

```
   用户上传支付截图
        │
        ▼
   ┌─────────┐     OCR 文本 (本地图片 → 文字)
   │   OCR   │     后端: paddleocr (本地推理) | mock (按文件名 mock)
   └────┬────┘
        │ ocr_text
        ▼
   ┌─────────┐     多模态: 图片 + OCR 文本 → 结构化 RecognizeResult
   │ VISION  │     后端: qwen-vl-plus (阿里云百炼) | mock (正则解析)
   └────┬────┘
        │
        ▼
   ┌─────────┐     LLM 校验: 修正异常金额 + 优化分类
   │   LLM   │     后端: deepseek-chat (DeepSeek) | mock (关键词)
   └────┬────┘
        │
        ▼
   保存到 DB (bill + ai_record)
```

## 切换步骤

### 1. 安装依赖

```bash
cd backend
pip install -e ".[ai]"
# 安装 paddleocr / paddlepaddle / dashscope / openai
```

### 2. 申请 Key

| 服务 | 平台 | Key 申请 |
|---|---|---|
| Qwen-VL-Plus | 阿里云百炼 | https://bailian.console.aliyun.com/ 开通模型后创建 API-KEY |
| DeepSeek | DeepSeek 开放平台 | https://platform.deepseek.com/api_keys |

PaddleOCR 本地推理，**不需要 Key**，但首次运行会下载 ~100MB 模型权重。

### 3. 改 `.env`

```bash
OCR_BACKEND=paddleocr
VISION_BACKEND=qwen-vl
LLM_BACKEND=deepseek

DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 4. 重启后端

```bash
.venv/bin/uvicorn app.main:app --reload
```

观察启动 log：
- `降级到 mock vision` 表示 dashscope 没装或 key 缺失
- `Application startup complete` 表示三层都已就位

## 验证真模型

上传一张真实支付截图，看 `/api/v1/bill/recognize` 返回的 `score`：
- mock: `0.85` (固定)
- qwen-vl: `0.95` (固定，表示多模态)
- deepseek refine 后: 0.6-0.99 动态

## 模型选择建议

| 后端 | 成本 | 速度 | 准确率 | 适用 |
|---|---|---|---|---|
| mock | 0 | 最快 | 取决于图片命名 | 开发调试 |
| paddleocr | 0 | 中 (CPU/GPU) | 中文印刷体 ~95% | 离线场景 |
| qwen-vl-plus | ¥0.003/张 | 2-5s | 多模态 ~95% | 生产首选 |
| DeepSeek-V3 | ¥0.001/次 | 1-3s | 文本理解最强 | refine 兜底 |

**推荐组合**（生产）：
- OCR: paddleocr (本地, 省钱) **或** mock + qwen-vl (省一道)
- VISION: **qwen-vl** (图片直接读, 跳过 OCR 也行)
- LLM: **deepseek** (审查兜底)

## 降级策略

每个后端函数都遵循：
1. 依赖 (pip 包) 缺失 → 降级 mock + warning
2. API key 缺失 → 降级 mock + warning  
3. API 调用失败 (网络/超时) → 当前会抛 50000; 后续可加重试 + 降级

生产部署建议：在 `app/core/config.py` 加 `production: bool` 字段，降级策略在生产模式可以更严格（不允许 mock fallback）。

## 调试

启动日志会打印降级原因：
```bash
tail -f logs/$(date +%Y%m%d).log | grep -i '降级\|dashscope\|deepseek'
```

或 dev 环境：
```bash
.venv/bin/uvicorn app.main:app --log-level info 2>&1 | grep 降级
```
---

## MiniMax 一站式接入 (推荐)

MiniMax 同时提供 **VL 多模态** 和 **文本模型**，API 兼容 OpenAI SDK，
**一个 MINIMAX_API_KEY 覆盖 vision + llm 两层**，最简配置。

### 配置

```bash
# .env
pip install openai          # MiniMax API 兼容 OpenAI SDK, 不用装额外包
VISION_BACKEND=minimax
LLM_BACKEND=minimax
OCR_BACKEND=mock            # MiniMax-VL 直接读图, OCR step 可跳过
MINIMAX_API_KEY=your-key-here
```

### 模型选择

| 字段 | 默认值 | 说明 |
|---|---|---|
| `MINIMAX_BASE_URL` | `https://api.minimaxi.com/v1` | API 端点 |
| `MINIMAX_VL_MODEL` | `MiniMax-01-Vis-32k` | 视觉模型 |
| `MINIMAX_TEXT_MODEL` | `MiniMax-Text-01` | 文本模型 |

### 优势

- **1 个 key 覆盖 2 层**（vision + llm）
- **复用现有 openai 包**（无需新增依赖）
- **国内访问稳定**（不需要代理）
- **VL 直接读图**（OCR step 可跳过，端到端延迟更低）
