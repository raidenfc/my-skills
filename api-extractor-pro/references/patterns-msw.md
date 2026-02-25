# MSW 生成规范

## Handler 生成规则

- 每个接口生成一个 handler，使用 MSW v2.x 语法
- 使用 `http.<method>` 与 `HttpResponse.json(...)`
- 将 OpenAPI 路径参数从 `{id}` 转换为 `:id`（MSW 路由格式）
- 按模块分文件：`mock/handlers/[module].js`
- 汇总入口：`mock/handlers/index.js`
- Worker 入口：`mock/browser.js`

## Handler 增强逻辑

每个 Handler 应包含以下增强：

| 增强项 | 适用场景 | 说明 |
|--------|---------|------|
| 延迟模拟 | POST/PUT/PATCH/DELETE | `await delay(200-500)` |
| Token 校验 | 需要认证的接口 | 检查 `Authorization: Bearer` |
| 参数校验 | POST/PUT 请求体 | 检查必填字段 |
| 分页逻辑 | 列表接口 | 解析 `page`/`pageSize` |
| 路径参数 | 带 `:id` 的接口 | 根据 ID 查找数据 |

## mockStrategy 规则

| 策略 | 行为 |
|------|------|
| `success` | 始终返回 2xx 成功响应 |
| `error` | 始终返回第一个错误响应 |
| `random` | 50% 概率返回成功或错误 |

## 数据文件规范

- 输出到 `mock/data/[module].json`
- 每个模块包含 3-5 条 **贴合业务的中文数据**
- 时间字段使用 ISO 8601 格式
- ID 使用数字或 UUID，保持类型一致
- **禁止 lorem ipsum**，使用真实业务数据

## 默认模板

### 分页接口

- query 默认包含 `page`、`pageSize`
- 响应默认包含 `list`、`total`、`page`、`pageSize`

### 鉴权接口

- `auth_mode` 为 `bearer` 时，检查 `Authorization: Bearer <token>`
- 返回 401 错误：`Token 无效或已过期`

### 文件上传

- 请求体 `contentType` 为 `multipart/form-data`

### 列表查询

- 可选过滤字段标记为推断
