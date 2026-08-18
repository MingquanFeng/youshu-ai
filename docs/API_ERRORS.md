# API 错误码规范

后端 API 返回格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- **业务成功**：`code == 0`，HTTP 200
- **业务失败**：`code != 0`，HTTP 仍是 200（业务校验不通过）；或 HTTP 4xx/5xx
- **后端会自动序列化 `BizException(code, message)` → `{code, message, data}`**

## 业务码清单

| code | 含义 | HTTP | 触发场景 | 前端处理 |
|---|---|---|---|---|
| **0** | 成功 | 200 | 任何正常请求 | 读取 `data` |
| **40000** | 业务参数错误 | 200 | 日期格式错、文件类型不支持、上传 > 10MB、更新 body 空、微信接口异常 | toast 提示，message 可直接展示给用户 |
| **40100** | 未登录 / token 无效 | 401 | 缺 token / token 过期 / token sub 不合法 | **强制跳登录**，清除本地 token |
| **40400** | 资源不存在 | 200 | 账单不存在、图片不存在、列表为空 | `bill/detail` 页面展示 "此条记录不存在或已删除" 状态 |
| **42200** | 参数校验失败 | 422 | Pydantic 校验：amount ≤ 0、days > 365、path 参数非 int 等 | **`data` 是 `{field: msg}` 字典**，渲染到对应 input 旁红字 |
| **50000** | 服务内部错误 | 200 | AI 推理失败、Qwen-VL 返回非 JSON、微信接口 500、未捕获异常 | toast 提示，message 可展示；保留数据让用户重试 |

## HTTP 状态码

| HTTP | 含义 | 触发 | 前端处理 |
|---|---|---|---|
| 200 | 任何业务成功 / 失败都包 200 | BizException 默认 | 看 `code` 字段 |
| 401 | 未鉴权 | token 缺失/无效 | 跳登录 |
| 404 | 资源路径不存在 | ocr service 图片文件不在 | 弹错误条 |
| 422 | 请求体/参数 schema 错 | Pydantic ValidationError | 同 42200 |
| 500 | 未捕获异常 | 代码 bug / 依赖宕机 | toast 报错 + 留数据可重试 |

> **HTTP 状态码与业务码不一定一致**：40100 返回 HTTP 401，其他业务异常（40000/40400/50000）返回 HTTP 200。前端应**优先看 `body.code`**，HTTP 状态只用来判断"网络是否通"。

## 前端处理模板

`utils/request.js` 已封装：

```js
wx.request({
  // ...
  success(res) {
    const body = res.data || {}
    if (body.code === 0) {
      resolve(body.data)
    } else if (body.code === 40100) {
      clearToken()
      wx.showToast({ title: '请重新登录', icon: 'none' })
      reject(body)
    } else if (body.code === 42200 && body.data) {
      // body.data = { field: msg }
      reject(body)
    } else {
      wx.showToast({ title: body.message || '请求失败', icon: 'none' })
      reject(body)
    }
  },
  fail(err) {
    wx.showToast({ title: '网络异常', icon: 'none' })
    reject(err)
  }
})
```

## 42200 错误格式

```json
{
  "code": 42200,
  "message": "请求参数校验失败",
  "data": {
    "amount": "Input should be greater than 0",
    "category": "请字段 is空"
  }
}
```

`data` 是 `{field: msg}` 字典（每字段取首条错误），前端按字段名渲染到对应 input 旁。

## 调用方约定

- 后端抛 `BizException(code, message, status_code=200)`：默认 status_code=200，业务码 + message 在 body
- 鉴权失败 (`40100`) 用 `status_code=401`，HTTP 层就能拦下未授权请求
- 资源不存在用 `40400`，HTTP 仍 200 — 因为接口本身有效，只是数据没了
- 参数错用 Pydantic 自动 42200 + `data: {field: msg}`，**不要手动 `BizException(40000, ...)`**，让前端按字段渲染

## 测试

错误码变更必须同步更新：
1. `tests/test_*.py` 里的 `assert body["code"] == ...`
2. 前端 `utils/request.js` 的处理分支
3. 本文档

CI 已经能保证：改 BizException → pytest fail → 提示同步。