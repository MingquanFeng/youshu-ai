# 开发粒度拆分 (ROADMAP)

> 原则：**一次开发任务 = 一个接口、一个页面、一个组件、或一个可独立验收的子模块**。
> 每条任务都有：目标 / 涉及文件 / 依赖 / 验收。下游任务依赖上游时标注 `←`。

约定：
- **后端** 一个接口 = 一次任务（路由 + schema + service + 测试）
- **前端** 一个页面 = 一次任务；通用组件单列；状态 / 工具类单列
- **基础设施** 跨多个接口的，单列一次任务
- 每条任务预估 0.5–2 小时开发 + 0.5 小时验证

---

## Phase 0 — 已交付（MVP 骨架）

> 上一轮已完成，仅列出作为后续任务的"起点"。改动不归零。

| 任务 | 状态 |
|---|---|
| 后端脚手架（FastAPI + 配置 + 异常 + JWT + ORM + 统一响应） | ✅ |
| 前端脚手架（UniApp + Vue3 + TS + Pinia + request 封装） | ✅ |
| `POST /api/v1/user/login`（微信登录 + JWT） | ✅ |
| `POST /api/v1/bill/upload`（图片上传） | ✅ |
| `POST /api/v1/bill/recognize`（AI 识别 OCR→vision→LLM 编排） | ✅ |
| `POST /api/v1/bill/save`（保存账单） | ✅ |
| `GET /api/v1/bill/list`（账单列表 + 分页 + 筛选） | ✅ |
| `POST /api/v1/analysis/monthly`（本月消费分析） | ✅ |
| 前端页面 `index`（首页入口） | ✅ |
| 前端页面 `recognize`（AI 记账页） | ✅ |
| 前端页面 `bill`（账单列表页） | ✅ |
| 前端页面 `analysis`（消费分析页） | ✅ |
| pytest 11 用例（user/bill/analysis） | ✅ |
| README / NOTES / LICENSE | ✅ |

---

## Phase 1 — MVP 收尾（让骨架变成可演示）

> 目标：用 mock 数据跑通"打开小程序 → 上传图 → AI 识别 → 保存 → 看账单 → 看分析"全流程，10 条以内任务。

### T-001 基础设施：CI 工作流
**目标**：GitHub Actions 跑 pytest + ruff。
**涉及**：`.github/workflows/ci.yml`
**验收**：PR 上显示 ✅ / ❌；main 分支强制绿。
**依赖**：无。

### T-002 后端：`GET /api/v1/bill/{id}`（账单详情）
**目标**：单个账单查询，供后续编辑页使用。
**涉及**：`api/v1/bill.py`、`schemas.py`、test
**验收**：传 id 返回完整字段；越权访问别人的账单返回 40400；测试覆盖。
**依赖**：无。

### T-003 后端：`PUT /api/v1/bill/{id}`（编辑账单）
**目标**：修改 AI 识别结果；自动记录 source 仍为 `image_ai`，但 `remark` 记"用户修正"。
**涉及**：`api/v1/bill.py`、`schemas.py`、test
**验收**：白名单字段更新；不修改 `source / ai_score`；鉴权 + 用户隔离。
**依赖**：T-002。

### T-004 后端：`DELETE /api/v1/bill/{id}`（软删）
**目标**：标记 `deleted_at`，不真删，便于审计。
**涉及**：`models/bill.py`（加字段）、migration、`api/v1/bill.py`、test
**验收**：删后 list 不再返回；DB 里仍可见；测试覆盖。
**依赖**：T-002。

### T-005 前端：`bill` 页面（列表）
**目标**：调通 `listBills`，渲染卡片列表，支持下拉刷新 + 上拉加载更多。
**涉及**：`pages/bill/bill.vue`、`api/bill.ts`（加 `loadMore`）
**验收**：列表能分页；空态显示提示；下拉刷新有效。
**依赖**：T-002。

### T-006 前端：`bill/detail` 页面（账单详情 + 编辑）
**目标**：从列表点击进入，可改金额 / 分类 / 商户 / 备注，保存调 T-003；底部"删除"调 T-004。
**涉及**：`pages/bill/detail.vue`、`api/bill.ts`（加 `get / update / remove`）
**验收**：改完点保存回到列表能看到新值；删除后回到列表，条目消失。
**依赖**：T-003、T-004、T-005。

### T-007 前端：`recognize` 页面（识别 + 编辑 + 保存）
**目标**：复用现有 `recognize.vue`，在识别结果上加"编辑"入口，跳到 detail 形态的本地编辑器；保存调 `save` 接口。
**涉及**：`pages/recognize/recognize.vue`
**验收**：识别后用户改值可保存；source 传 `image_ai`。
**依赖**：无（已有 API）。

### T-008 前端：`analysis` 页面（图表）
**目标**：在原页基础上加饼图（按分类）+ 折线（按日）。
**涉及**：`pages/analysis/analysis.vue`、后端 `analysis.py`（补 `/daily` `/category` 接口）
**验收**：饼图按分类占比；折线显示近 30 天。
**依赖**：T-009、T-010。

### T-009 后端：`POST /api/v1/analysis/daily`（日趋势）
**涉及**：`api/v1/analysis.py`、`schemas.py`、test
**验收**：返回近 N 天每天的总金额；天数可配。
**依赖**：无。

### T-010 后端：`POST /api/v1/analysis/category`（分类占比）
**涉及**：`api/v1/analysis.py`、`schemas.py`、test
**验收**：返回 `{category, amount, percent}` 列表；percent 之和 ≈ 1。
**依赖**：无。

---

## Phase 2 — AI 真实接入

> 目标：把 mock 换成真实模型，对外保持接口不变。每条任务对应一个 AI 后端的接入。

### T-101 后端：接 PaddleOCR
**目标**：在 `services/ocr.py` 里把 `OCR_BACKEND=paddleocr` 跑通。
**涉及**：`services/ocr.py`、`.env.example`、test（识别示例图片）
**验收**：喂一张微信截图，OCR 文本能覆盖金额 / 商户；首次加载 < 5s。
**依赖**：无。

### T-102 后端：接 Qwen3-VL
**目标**：用多模态模型直接读图，跳过 OCR。
**涉及**：`services/vision.py`、`.env.example`
**验收**：图片 → 结构化 JSON 单跳返回；JSON 字段符合 `RecognizeResult`。
**依赖**：T-101（OCR 保留兜底）。

### T-103 后端：接 DeepSeek-V3 校验
**目标**：对 Qwen-VL 输出做合理性检查，修正异常金额、补默认分类。
**涉及**：`services/classify.py`、`.env.example`
**验收**：异常样本被纠正；正常样本分数提升。
**依赖**：T-102。

### T-104 前端：识别结果可"重试 / 人工修正"分流
**目标**：`score < 0.6` 时提示用户复核；> 0.9 直接保存。
**涉及**：`pages/recognize/recognize.vue`
**验收**：低分时显示警告条；高分时显示"看起来没问题"。
**依赖**：T-102。

---

## Phase 3 — 体验补全

### T-201 前端：分类筛选组件
**目标**：账单列表上方加分类下拉，多选。
**涉及**：`components/CategoryFilter.vue`、`pages/bill/bill.vue`
**验收**：选了"餐饮"列表只显示该分类；可清空。

### T-202 前端：日期范围选择组件
**目标**：账单列表支持"本月 / 上月 / 自定义"快捷区间。
**涉及**：`components/DateRangePicker.vue`、`pages/bill/bill.vue`
**验收**：切到上月列表刷新；自定义区间传 `from / to` 到 API。

### T-203 前端：首页"今日消费金额"
**目标**：首页加今日合计 + 最近 3 笔。
**涉及**：`pages/index/index.vue`、后端 `GET /api/v1/bill/today`
**验收**：进入首页立即看到今日合计；点击"最近账单"跳到列表。
**依赖**：T-203-API（后端任务，类同 T-009 套路）。

### T-204 前端：登录态管理
**目标**：封装"未登录跳登录"逻辑；Token 失效统一处理。
**涉及**：`store/user.ts`、`utils/request.ts`
**验收**：40100 自动清 token 跳首页；首启未登录时引导走 `/pages/login`。

### T-205 前端：图片预览组件
**目标**：上传前预览、识别结果图可点击放大。
**涉及**：`components/ImagePreview.vue`
**验收**：长按 / 点击触发全屏预览；可保存到本地相册。

---

## Phase 4 — 工程化

### T-301 后端：日志 + 监控
**目标**：用 `loguru` 替换标准日志；接入 Sentry。
**涉及**：`app/core/log.py`、`main.py`
**验收**：异常堆栈自动上报；本地 JSON 结构化日志。

### T-302 后端：Redis 缓存识别结果
**目标**：相同图片 hash 不重复调模型。
**涉及**：`app/core/cache.py`、`services/pipeline.py`
**验收**：第二次传同一张图耗时 < 200ms；缓存 TTL 7 天。

### T-303 后端：异步队列（Celery / Arq）
**目标**：把识别放到后台任务，HTTP 接口秒回。
**涉及**：新增 `tasks/`，改造 `recognize`
**验收**：接口响应 < 300ms；前端轮询结果。

### T-304 后端：PostgreSQL 迁移 + Alembic
**目标**：切到 PG，加迁移工具。
**涉及**：`DATABASE_URL`、`alembic init`
**验收**：`alembic upgrade head` 一次到位；CI 跑迁移校验。

### T-305 DevOps：Docker 化
**目标**：后端 Dockerfile + docker-compose（含 PG + Redis）。
**涉及**：`backend/Dockerfile`、`docker-compose.yml`
**验收**：`docker compose up` 一键起后端；前端 dist 静态托管。

### T-306 DevOps：CI 接入前端
**目标**：vue-tsc + uni-build 跑通。
**涉及**：`.github/workflows/ci.yml`
**验收**：前端 lint / type-check / build 三道门过。

---

## Phase 5 — V2 / V3（来自 PRD）

- T-401 AI 聊天助手（自然语言记账）
- T-402 自动预算（每月各类上限 + 提醒）
- T-403 消费预测（基于历史的 LSTM / 简单回归）
- T-404 家庭账本（多 user_id 共享账本）
- T-405 多账户管理（银行卡 / 信用卡聚合）
- T-406 资产管理（净值追踪）

---

## 怎么用这张表

1. **挑任务**：选一条 `依赖：✅` 的（依赖项都已经 ✅）。
2. **建分支**：`git checkout -b feat/T-005-bill-list-page`
3. **实现 + 写测试 + 自验**：`pytest` + 端到端 curl + 前端预览。
4. **PR + CI 全绿 + 自己 review**。
5. **merge 后勾掉**：勾完继续下一条。

每条任务做完都能独立交付、独立回滚、独立演示。这是粒度的核心。
