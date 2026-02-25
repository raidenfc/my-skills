---
name: api-extractor-pro
description: 前端 API 治理工作站：从项目中的真实 API 调用扫描接口，生成结构化契约（contract.json）、MSW Mock、标准接口文档（Markdown + OpenAPI 3.1 YAML），并执行一致性校验与变更追踪。
---

# API Extractor Pro

从前端代码出发，聚焦 **扫描接口 → 生成契约 → 产出 Mock → 输出文档 → 校验一致性 → 追踪变更**。

---

## 适用场景

- 前端项目已有 API 调用，但缺少接口文档
- 需要统一产出 `contract.json` / OpenAPI / MSW
- 需要 CI/CD 中自动化校验接口一致性
- 需要多次迭代间追踪接口变更

---

## 职责边界（强制）

本 skill **只做接口治理产物生成与校验**：

- ✅ 做：扫描 API 调用、生成 `contract.json`、生成 Mock、生成文档、校验一致性、生成 diff 报告
- ❌ 不做：页面业务逻辑改造、静态页面数据迁移、页面状态流重构

> 页面 API 化改造应由 `static-to-api-layer` 在前置阶段完成。

---

## 前置条件（推荐）

若项目是静态页面起步，建议先执行：

1. `static-to-api-layer`：完成页面 API 化
2. `api-extractor-pro`：统一生成治理产物

若项目本身已存在标准 API 调用，可直接使用本 skill。

---

## 七阶段工作流

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 1. Scan  │───▶│2. Contract│───▶│ 3. Confirm│───▶│ 4. Mock  │
│  扫描分析 │    │ 生成契约  │    │ 用户确认  │    │ MSW生成  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
┌──────────┐    ┌──────────┐    ┌──────────┐          │
│ 7. Report│◀───│ 6. Verify│◀───│ 5. Docs  │◀─────────┘
│ 变更报告  │    │ 一致性校验│    │ 文档生成  │
└──────────┘    └──────────┘    └──────────┘
```

---

### 阶段 1：扫描分析（Scan）

**目标**：收集项目中所有 API 调用

**执行方式**：

```bash
python3 scripts/scan.py --project-root <项目根目录> [--scope src/pages,src/views] [--entry-hints src/api,src/services]
```

支持 Axios / Fetch / request 封装 / React Query / SWR 等模式。

**输出**：`scan_result.json`

---

### 阶段 2：生成契约（Contract）

**目标**：将扫描结果转化为结构化接口契约

**执行方式**：

```bash
python3 scripts/build_contract.py --scan-result scan_result.json --auth-mode bearer --output contract.json
```

`contract.json` 是整个工作流唯一事实源（SSOT）。

---

### 阶段 3：用户确认（Confirm）

**目标**：整理接口清单并确认推断项，确认后更新 `contract.json`。

---

### 阶段 4：生成 MSW Mock（Mock）

**目标**：从 `contract.json` 生成 MSW handlers 和 mock 数据。

**执行方式**：

```bash
python3 scripts/generate_msw.py --contract contract.json --output-root <项目根目录>
```

---

### 阶段 5：生成接口文档（Docs）

**目标**：从 `contract.json` 生成 `docs/api-docs.md` 和 `docs/openapi.yaml`。

**执行方式**：

```bash
python3 scripts/generate_docs.py --contract contract.json --output-root <项目根目录> --project-name "项目名称"
```

---

### 阶段 6：一致性校验（Verify）

**目标**：交叉校验 contract ↔ OpenAPI ↔ MSW handlers。

**执行方式**：

```bash
python3 scripts/check_consistency.py \
  --contract contract.json \
  --openapi docs/openapi.yaml \
  --handlers mock/handlers/ \
  --report reports/consistency-report.md \
  [--strict-mode]
```

---

### 阶段 7：变更报告（Report）

**目标**：对比上次契约与当前契约，生成 `reports/api-diff.md`。

---

## 一键执行（全自动模式）

```bash
python3 scripts/run_workflow.py --config config.json
```

---

## 输出产物清单

| 产物 | 路径 | 说明 |
|------|------|------|
| 扫描结果 | `scan_result.json` | 原始 API 调用扫描数据 |
| 接口契约 | `contract.json` | 唯一事实源，结构化接口定义 |
| MSW Handler | `mock/handlers/[module].js` | 按模块分组的 Mock 拦截器 |
| MSW 数据 | `mock/data/[module].json` | 贴合业务的 Mock 数据 |
| MSW 入口 | `mock/browser.js` | Worker 启动入口 |
| 中文文档 | `docs/api-docs.md` | Markdown 格式接口文档 |
| OpenAPI | `docs/openapi.yaml` | OpenAPI 3.1 规范 |
| 一致性报告 | `reports/consistency-report.md` | 三方交叉校验结果 |
| 变更报告 | `reports/api-diff.md` | 接口变更追踪 |

---

## 强制规则

1. `contract.json` 是唯一事实源
2. 每个接口必须包含成功响应和至少一个错误响应
3. 不确定字段统一标记为 `x-todo-confirm`
4. 接口命名格式统一为 `domain.action`
5. 本 skill 不修改业务逻辑页面代码

---

## 注意事项

1. 若项目中有 `api/` / `services/` / `request/`，优先扫描这些目录
2. URL 模板变量统一转为路径参数（如 `/api/user/:id`）
3. 识别并输出 `baseURL` 与鉴权模式
4. 分页、上传等模式需在文档中明确标注
5. **微信小程序项目**：MSW（Service Worker）在小程序中不可用，Mock 方案由 `static-to-api-layer` 的 `mock-interceptor-wx.js` 提供。本 skill 生成的 MSW Mock 仅适用于 Web 项目（React / Vue）

---

## 参考资料

- 契约结构规范：`references/contract-schema.md`
- MSW 生成规范：`references/patterns-msw.md`
- OpenAPI 生成规范：`references/patterns-openapi.md`
- 文档模板：`templates/api-doc.md`
- OpenAPI 模板：`templates/openapi.yaml`
- Mock 示例：`examples/mock-handler-example.js`
- 文档示例：`examples/api-docs-example.md`
