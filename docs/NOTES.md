# AI 记账助手 — 工程笔记

## 关键技术决策

| 决策 | 选择 | 理由 |
|---|---|---|
| Web 框架 | FastAPI | PRD/MVP 文档指定 |
| ORM | SQLAlchemy 2.x 同步 | dev 简单；生产可换 async + asyncpg |
| 主键类型 | `Integer`（非 `BigInteger`） | SQLite 上 `BigInteger + autoincrement` 不会自增，已在冒烟阶段踩坑修复 |
| AI 编排 | OCR → Vision → LLM 三层 | 文档定义；每层都可独立替换 |
| 后端默认 | 全部 mock | 不依赖外网 API 也能跑通流程 |
| 鉴权 | JWT (HS256) | API 文档约定 |
| 文件存储 | 本地静态目录 | dev；生产换 OSS/COS |
| 微信登录 | dev mock | 无 WX_APP_ID 时用 `mock-<code>` 当 openid，方便联调 |

## 已知限制

- 启动时 `Base.metadata.create_all` 仅适合 dev，生产必须上 Alembic 迁移。
- `/static/uploads` 直接挂文件系统，未做签名 URL。
- `Bill.amount` 用 `Numeric(12,2)`：足够个人记账，但企业级需要再调。
- 没有上传限流和图片病毒扫描，生产前要补。
- 前端是骨架级别，UI 用原生 `<view>` + scss；上线前需按 uView Plus 规范替换组件。

## 下一步建议（按优先级）

1. 接通 PaddleOCR，跑通真实截图识别；用一批微信/支付宝截图做评测，盯「识别准确率 ≥ 90%」指标。
2. 接通 Qwen3-VL，省掉 OCR 步骤直接多模态输出 JSON。
3. 给后端加 pytest 覆盖（登录、上传、识别、保存、列表、分析），CI 跑 ruff + mypy + pytest。
4. 前端补 uView Plus 组件、图表（uCharts），把首页"今日消费金额"做出来。
5. 接入 Redis 做识别结果缓存，减少 Qwen/DeepSeek 重复调用。
6. 引入 Celery / Arq，把识别放到后台队列，避免 HTTP 长连接被掐。
