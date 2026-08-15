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
- 用占位符（`__FIELD_NAME__` 或 `touristappid`）
- 在 commit message 显式声明："本配置含占位符，开发者需替换为真实值"
- 不写 README/setup 里包含真实值的示例