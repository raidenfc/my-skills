# OpenAPI 生成规范

## 版本与顶层字段

- 使用 OpenAPI `3.1.0`
- 顶层包含：`info`、`servers`、`paths`、`components`

## 接口映射规则

| 契约字段 | OpenAPI 字段 |
|---------|-------------|
| `method + path` | `paths[path][method]` |
| `endpoint` | `operationId` |
| `module` | `tags` |
| `responses` | 按状态码映射到 `responses` |
| `errors` | 作为非 2xx 响应追加 |

## 参数映射

| 契约字段 | OpenAPI 字段 |
|---------|-------------|
| `pathParams` | `parameters`（`in: path`） |
| `query` | `parameters`（`in: query`） |
| `headers` | `parameters`（`in: header`） |
| `requestBody` | `requestBody.content` |

## 请求体映射

- 默认 `application/json`
- 若声明 `multipart/form-data`，按文件上传输出
- `required` 根据 method 自动判断（POST/PUT/PATCH 为 true）

## 安全方案

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: "登录后获取的 JWT Token"
```

## 未知与推断字段

- 无法确认的 schema 补充 `description: "inferred from static analysis"`
- 扩展字段 `x-todo-confirm: true`

## Markdown 文档规范

`docs/api-docs.md` 应包含：

1. 项目信息（生成时间、接口总数、技术栈）
2. 通用规范（请求地址、认证、统一响应格式、分页格式）
3. 快速接入 MSW Mock 指南
4. 各模块接口详情：
   - 参数表（路径参数、查询参数、请求体）
   - 成功响应示例
   - 错误响应及错误码
   - 待人工确认项
5. 错误码总览
