# 安全事件复盘：AppID 泄露

## 事件摘要

- **发生时间**：2026-08-14
- **泄露内容**：微信小程序 AppID `wxf8d81725b62b2252`
- **影响范围**：GitHub 公开仓库 `MingquanFeng/youshu-ai` 的 commit 历史
- **泄露窗口**：约 4 小时（commit `3dbdc27` push 到 force push 修复）
- **当前状态**：✅ 已清除（force push 重写历史，GitHub 搜索 0 结果）

## 触发链

```
Plan agent 写 project.config.json
  ↓ 包含 "appid": "wxf8d81725b62b2252"（未追问来源）
我直接采纳（未做敏感扫描）
  ↓
commit + push 到 GitHub（公开仓库）
  ↓
GitHub commit 历史永久记录 AppID
```

## 根因（5 Whys）

1. **为什么 AppID 泄露？** 因为 commit 里包含了一个真实的 18 位 hex AppID
2. **为什么 commit 里包含真实 ID？** Plan agent 在写 project.config.json 时直接填了一个看起来合法的 ID
3. **为什么 Plan agent 填了真实 ID？** 它的训练数据或知识里可能有这个 ID；或者它从某个项目历史/模板里复用了
4. **为什么我没拦截？** 我把 project.config.json 当成普通配置文件，没追问 AppID 来源
5. **为什么没追问？** 我没有"敏感信息必须追问"的协议——CLAUDE.md 规则只要求"提交前确认"，没说"敏感字段必须人工指定"

## 缺失的防御

| 防御层 | 状态 |
|---|---|
| Plan agent 拒绝编造 AppID | ❌ 无 |
| 我对 project.config.json 做敏感扫描 | ❌ 无 |
| pre-commit hook（gitleaks / detect-secrets） | ❌ 无 |
| CI 阶段跑 secret-scan | ❌ 无 |
| GitHub Secret Scanning 启用 | ❌ 公开仓库默认开启，但仍需 |

## 修复措施

- **紧急**：用户已在微信小程序后台重置 AppSecret（✅ 用户已确认）
- **短期**：
  - [x] Force push 重写历史清除泄露
  - [ ] 本仓库加 `.gitleaks.yml` 配置（todo）
  - [ ] 加 `pre-commit` hook 自动跑 secret scan（todo）
  - [ ] 加 `.github/workflows/secret-scan.yml`（todo）
  - [ ] 重置 `backend/.env` 的 `JWT_SECRET`（todo）
- **长期**：
  - 任何 plan agent 写配置字段时，**明确禁止编造看似合法的 ID/token/secret**，强制用占位符（`__WECHAT_APPID__` / `touristappid` / `${WECHAT_APP_SECRET}`）
  - 加 CLAUDE.md / AGENTS.md 规则："涉及凭证字段，agent 只能写占位符，真实值由人工填"

## 教训

> **Agent 默认会"看起来合理"的占位——这恰恰是危险信号**。18 位 hex 看起来"像真的"，但验证需要：
> 1. 字段类型识别（看起来是 secret）
> 2. 占位符强制（agent 不准写真实格式）
> 3. 提交前自动扫

下次任何 plan agent 涉及 `appid / appsecret / api_key / token / password` 字段，
必须：
- 用占位符（`__FIELD_NAME__` 或 `touristappid`）——**但 `touristappid` 不可用于本地开发**，详见下方"AppID 占位符陷阱"
- 在 commit message 显式声明："本配置含占位符，开发者需替换为真实值"
- 不写 README/setup 里包含真实值的示例

## AppID 占位符陷阱

**问题**：Plan agent 默认会把 `appid` 填成 `touristappid`（GitHub README 里的示例占位符）。这导致：
1. 微信开发者工具**拒绝**该值，弹"更改 AppID 失败 tourist appid"错误
2. IDE 自动降级到**游客模式**，所有 `wx.*` API 失效（`wx.login` / `wx.request` / `wx.getStorageSync` 全部 mock 返回）
3. App 能编译但**调不到后端**，用户看到空白页

**正确做法**（适用于所有小程序项目）：
1. **项目内**：`frontend/project.config.json` 填**真实 AppID**（`wx` + 16 hex）
2. **本地不入 git**：`project.config.json` 已加入 `.gitignore`（commit `XXX`）
3. **新 clone 项目**：开发者从微信小程序后台拿自己的 AppID → 在 IDE 里填入本地 `project.config.json` → IDE 自动忽略 gitignore（因为没在 git 里）
4. **README 提供"占位符替换"说明**，不写 `touristappid` 字符串

**为什么不能 commit touristappid 占位符到 git**：
- 推上去后别人 clone，IDE 直接弹错，浪费时间排查
- 占位符污染下游所有人的本地开发
- "看起来对"的占位符是更糟糕的失败模式

**教训修正**：Hallmark 守则"占位符必须用 `__FIELD_NAME__` 或 `touristappid`"中，**`touristappid` 应该替换为更明显的占位符**（如 `wx__REPLACE_ME__`），让任何人都能立刻识别"这是占位、必须替换"。
---

## 生产部署前必做（运维清单）

### JWT_SECRET 强度

后端启动时（`app/core/security.py`）会校验：

- `APP_ENV=prod` 且 `JWT_SECRET` 是默认值 `change-me-in-prod` → **fatal 启动失败**
- `APP_ENV=prod` 且 `JWT_SECRET < 32 字符` → **fatal 启动失败**
- dev/test → 只 warning，不阻塞

**部署前生成强 secret**：

```bash
openssl rand -hex 32
# 输出 64 位 hex, 如 a3f5e8c2b1d4f7e9...
```

写入生产 `.env`：

```bash
APP_ENV=prod
JWT_SECRET=<上面生成的 64 位 hex>
```

### 其他必改的环境变量

| 变量 | dev 默认 | 生产必改 |
|---|---|---|
| `JWT_SECRET` | `change-me-in-prod` | `openssl rand -hex 32` |
| `DATABASE_URL` | `sqlite:///./youshu_ai.db` | PostgreSQL（生产推荐）|
| `WX_APP_ID` | 空 | 真实 AppID（从小程序后台拿）|
| `WX_APP_SECRET` | 空 | 真实 AppSecret |
| `DASHSCOPE_API_KEY` | 空（mock）| 阿里云百炼 API-KEY |
| `DEEPSEEK_API_KEY` | 空（mock）| DeepSeek API-KEY |

### 其他安全检查

- [ ] gitleaks pre-commit hook 安装并通过
- [ ] GitHub Secret Scanning 启用（公开仓库默认）
- [ ] 生产域名 HTTPS 证书有效
- [ ] 后端 `/health` 仅返回 `status: ok` 不暴露版本号
- [ ] 数据库不暴露公网（绑定 127.0.0.1 或内网）
- [ ] 日志中不打印 token / secret
