# 契约结构规范

`contract.json` 是整个工作流的 **唯一事实源（Single Source of Truth）**。

## 顶层结构

```json
{
  "meta": { ... },
  "endpoints": [ ... ]
}
```

## meta 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `generatedAt` | string | 生成时间（ISO 8601） |
| `projectRoot` | string | 项目根目录 |
| `framework` | string | 框架类型 |
| `baseURL` | string | BaseURL 配置 |
| `authMode` | string | 认证方式：`bearer` / `cookie` / `custom` |
| `strictMode` | boolean | 是否严格模式 |
| `totalEndpoints` | integer | 接口总数 |

## endpoint 字段

```json
{
  "module": "user",
  "endpoint": "user.login",
  "method": "POST",
  "path": "/api/user/login",
  "pathParams": [
    { "name": "id", "type": "string", "required": true }
  ],
  "query": [
    { "name": "page", "type": "integer", "required": false, "default": 1, "description": "页码" }
  ],
  "headers": [
    { "name": "Authorization", "type": "string", "required": false, "example": "Bearer <token>" }
  ],
  "requestBody": {
    "contentType": "application/json",
    "schema": { "type": "object", "properties": {} }
  },
  "responses": [
    {
      "status": 200,
      "description": "成功",
      "schema": { "type": "object", "properties": {} },
      "example": { "code": 200, "data": {}, "message": "success" }
    }
  ],
  "errors": [
    {
      "status": 400,
      "code": "BAD_REQUEST",
      "message": "请求参数错误",
      "example": { "code": 400, "data": null, "message": "请求参数错误" }
    }
  ],
  "mockStrategy": "success",
  "x-todo-confirm": [
    "请求/响应 schema 为静态分析推断，需人工确认"
  ],
  "source": {
    "file": "src/api/user.ts",
    "line": 12,
    "pattern": "axios.post",
    "context": "export function login(data) { ... }"
  }
}
```

## 必填字段

- `module` — 业务模块名
- `endpoint` — 接口标识（`domain.action` 格式）
- `method` — HTTP Method
- `path` — 接口路径
- `responses` — 至少一个 2xx 响应
- `errors` — 至少一个 4xx/5xx 错误
- `mockStrategy` — Mock 策略

## 质量检查规则

1. 接口唯一键（`method + path`）不重复
2. `responses` 至少包含一个 2xx 状态码
3. `errors` 至少包含一个 4xx/5xx 状态码
4. `endpoint` 遵循 `domain.action` 命名规范
5. 无法确认的信息写入 `x-todo-confirm`
