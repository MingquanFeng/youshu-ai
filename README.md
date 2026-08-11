# AI 记账助手 (youshu-ai)

> AI 原生个人记账应用 —— 上传支付截图，AI 自动识别金额、商户、分类与时间。

## 1. 项目结构

```
youshu-ai/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/          # 路由：user / bill / analysis
│   │   ├── core/            # config / response / exceptions / security
│   │   ├── db/session.py    # SQLAlchemy engine & session
│   │   ├── models/          # ORM: user / bill / ai_record / category
│   │   ├── services/        # ocr / vision / classify / pipeline
│   │   ├── schemas.py       # Pydantic
│   │   └── main.py
│   ├── storage/uploads/     # 本地图片存储（生产换 OSS/COS）
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/                # UniApp 前端 (Vue3 + TS + Pinia + uView Plus)
│   └── src/
│       ├── pages/           # index / recognize / bill / analysis
│       ├── api/             # bill.ts / analysis.ts
│       ├── store/user.ts
│       ├── utils/request.ts
│       └── pages.json
└── docs/                    # 原始 PRD / MVP / API / DB / 架构
```

## 2. MVP 范围

| 优先级 | 功能 | 状态 |
|---|---|---|
| P0 | 微信登录 | ✅ |
| P0 | 上传截图 + AI 识别 | ✅ |
| P0 | 保存账单 | ✅ |
| P0 | 账单列表 | ✅ |
| P1 | 账单编辑 | 🔜 |
| P1 | 消费分析 | ✅ |

不做：家庭账本、银行卡同步、理财、社交。

## 3. 快速启动

### 后端

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env       # 默认全是 mock，无需配置即可跑
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- API: <http://127.0.0.1:8000/api/v1>
- Swagger: <http://127.0.0.1:8000/docs>
- 健康检查: <http://127.0.0.1:8000/health>

### 前端

```bash
cd frontend
npm install
npm run dev:h5             # 浏览器预览（Vite dev server，端口 5173）
npm run dev:mp-weixin      # 编译产物到 unpackage/dist/dev/mp-weixin/
                            # 然后用「微信开发者工具」打开该目录即可预览 / 调试
```

> 跑微信小程序**不需要 HBuilderX**。UniApp 编译用 CLI 完成；运行时交给微信开发者工具。HBuilderX 只是可选的 GUI 外壳。

## 4. 核心 API（统一返回 `{code, message, data}`）

| Method | Path | 说明 |
|---|---|---|
| POST | `/api/v1/user/login` | 微信 code 换 JWT |
| POST | `/api/v1/bill/upload` | multipart 上传支付截图，返回 image_id |
| POST | `/api/v1/bill/recognize` | 对 image_id 跑 OCR → 视觉模型 → LLM，返回结构化结果 |
| POST | `/api/v1/bill/save` | 保存账单（可带 image_id 关联 AI 记录） |
| GET | `/api/v1/bill/list` | 分页 + 按分类 / 日期筛选 |
| POST | `/api/v1/analysis/monthly` | 本月总消费 / Top 分类 / 建议 |

所有 `bill/*` 与 `analysis/*` 接口需要 `Authorization: Bearer <token>`。

## 5. AI 流水线

```
用户上传图片
    ↓ multipart
保存到 storage/uploads/<user_id>/<image_id>.jpg
    ↓
OCR  (app/services/ocr.py)         —— PaddleOCR / mock
    ↓
Vision (app/services/vision.py)    —— Qwen3-VL / mock，结构化 JSON
    ↓
Refine (app/services/classify.py)  —— DeepSeek-V3 / mock，可信度校验
    ↓
ai_record 落库
    ↓
前端确认后 → /bill/save
```

每个 AI 后端都支持 mock，方便本地不依赖外网服务就能跑通流程。
生产启用方式（`.env`）：

```ini
OCR_BACKEND=paddleocr
VISION_BACKEND=qwen-vl
LLM_BACKEND=deepseek
DASHSCOPE_API_KEY=...
DEEPSEEK_API_KEY=...
```

## 6. 数据库

开发：SQLite (`./youshu_ai.db`)，`Base.metadata.create_all` 自动建表。
生产：把 `DATABASE_URL` 改成 PostgreSQL，并加 Alembic 迁移。

四张表：

| 表 | 作用 |
|---|---|
| `user` | 微信用户 |
| `bill` | 账单，user_id 隔离 |
| `ai_record` | 每次 AI 识别的 OCR / 模型 / 结果，留作审计 |
| `category` | 二级分类（餐饮→早餐/午餐 …） |

## 7. 验证清单（CLAUDE.md 硬底线）

```bash
# 1. 后端 4 道门
.venv/bin/python -c "from app.main import app; print(len(app.routes))"   # 导入
.venv/bin/uvicorn app.main:app --port 8000 &                              # 启动
curl -sf http://127.0.0.1:8000/health                                    # health
# 端到端：login → upload → recognize → save → list → analysis  全绿

# 2. 前端
cd frontend && npm install
npm run type-check   # vue-tsc
npm run dev:h5       # 浏览器看
```

## 8. 后续版本

- **V2**：AI 聊天助手 / 自动预算 / 消费预测
- **V3**：家庭账本 / 多账户 / 资产管理

详见 [docs/](docs/) 中的原始 PRD / MVP，以及 [docs/ROADMAP.md](docs/ROADMAP.md) 中的开发粒度拆分（一接口 / 一页面 = 一次任务）。
