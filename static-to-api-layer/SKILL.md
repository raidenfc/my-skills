---
name: static-to-api-layer
description: 静态页面 API 化改造工具：自动发现页面中的隐式数据接口需求，改造页面为标准 API 调用并预留 Mock/真实接口切换层。不负责 contract/mock/docs 产物生成。
---

# Static to API Layer

从静态前端页面出发，聚焦 **发现隐式接口需求 → 页面 API 化改造 → 统一请求层 → 切换层预留**。

---

## 适用场景

- 前端先行开发，数据硬编码在 `mock.js` / 页面 `data` / `useState` / `constants` 中
- HTML Demo 转换而来的项目，需要正式化为接口驱动
- "先画页面再开发后端"的工作模式
- 作为 `api-extractor-pro` 的前置工程化改造

**支持框架**：React / Vue / 微信小程序

---

## 职责边界（强制）

本 skill **只做页面和调用层改造**，不生成接口治理产物：

- ✅ 做：隐式接口发现、API 封装层生成、页面改造、Mock/真实接口切换层
- ✅ 做（小程序例外）：小程序不支持 MSW，由本 skill 提供 `wx.request` 拦截式 Mock 方案
- ❌ 不做：`contract.json`、`openapi.yaml`、接口文档、一致性报告

> 接口治理产物（contract/OpenAPI/文档/校验）统一由 `api-extractor-pro` 生成。
> 小程序 Mock 数据由本 skill 的 `mock-interceptor-wx.js` 模板提供，因 MSW 在小程序中不可用。

---

## 四阶段工作流

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│1. Discover │───▶│2. Refactor │───▶│3. API Layer│───▶│4. Switch   │
│隐式接口发现  │    │页面改造      │    │统一请求封装   │    │切换层预留   │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
```

---

## 启动流程

收到用户请求后，按以下步骤启动：

1. **确认项目路径**：询问或确认前端项目根目录
2. **识别框架类型**：自动检测项目框架（React / Vue / 微信小程序）
   - React：`package.json` 含 `react`，目录结构含 `src/components` / `src/pages`
   - Vue：`package.json` 含 `vue`，目录结构含 `src/views` / `src/components`
   - 微信小程序：存在 `app.json` + `project.config.json`，页面为 `.wxml` + `.wxss` + `.js`
3. **扫描范围**：默认扫描所有页面和数据文件，用户可指定范围
4. **进入阶段 1**

---

### 阶段 1：隐式接口发现（Discover）

**目标**：扫描项目中所有页面和数据文件，识别隐式数据接口需求

#### 1.1 需要识别的 7 类接口模式

| # | 接口模式 | 识别特征 | 转化目标 |
|---|---------|---------|---------|
| 1 | **列表查询** | 硬编码数组 `const LIST = [...]`，页面 data 中直接赋值列表 | `GET /api/xxx/list` |
| 2 | **详情查询** | `getXxxById(id)`、`find(x => x.id === id)`、URL 参数取 id | `GET /api/xxx/:id` |
| 3 | **条件筛选** | `.filter()`、`selectedCategory`、条件分支渲染 | `GET /api/xxx/list?key=value` |
| 4 | **分页加载** | `.slice(0, n)`、`loadMore`、`page`/`pageSize` 变量 | `GET /api/xxx/list?page=1&pageSize=10` |
| 5 | **表单提交** | `handleSubmit()` 仅有 Toast/alert 无真实请求 | `POST /api/xxx` |
| 6 | **状态变更** | `handleApprove()`/`handleReject()`/`handleDelete()` 等操作 | `PUT /api/xxx/:id/action` |
| 7 | **聚合统计** | `STATS_*` 统计数据、图表数据源 | `GET /api/stats/xxx` |

#### 1.2 各框架识别特征

| 特征 | React | Vue | 微信小程序 |
|------|-------|-----|-----------|
| 数据声明 | `useState([...])` / `const data = [...]` | `data() { return { list: [...] } }` | `Page({ data: { list: [...] } })` |
| 数据加载 | `useEffect(() => {...}, [])` | `mounted()` / `onMounted()` | `onLoad()` / `onShow()` |
| 表单提交 | `onSubmit` / `handleSubmit` | `@submit` / `methods.submit` | `bindsubmit` / `handleSubmit` |
| 无效请求标志 | `alert('成功')` / `console.log` | `ElMessage.success` / `this.$message` | `wx.showToast({ title: '成功' })` |
| 数据文件 | `mock.js` / `data.ts` / `constants.ts` | `mock.js` / `data.js` | `mock.js` / 页面 js 内硬编码 |

#### 1.3 附加检测

- **字典/配置数据**：分类列表、枚举值、菜单配置 → `GET /api/config/xxx`
- **文件上传意图**：图片选择器、`wx.chooseImage`、`<input type="file">` → `POST /api/upload`
- **用户信息/鉴权意图**：用户数据硬编码、登录表单 → `GET /api/user/profile` / `POST /api/auth/login`

#### 1.4 输出

生成 `discovery_report.md`（参考 `templates/discovery-report.md`），包含：

- 项目概览（框架、目录结构、页面数量）
- 数据源清单（文件路径 + 数据名 + 数据结构摘要）
- 数据使用映射（哪些页面使用了哪些数据，使用方式）
- 隐式接口需求列表（模式分类 + 推断 endpoint）

---

### 阶段 2：页面改造（Refactor）

**目标**：将页面中的硬编码数据源替换为 API 调用

#### 2.1 页面改造规则

1. **移除所有 mock 数据导入**（`require('...mock')` / `import ... from '../mock'`）
2. **替换为 API 模块导入**
3. **data 初始值改为空**（`[]` / `null` / `{}`）
4. **添加 `loading` 状态**（为异步加载做准备）
5. **生命周期中改为 API 调用**（`onLoad` / `useEffect` / `mounted`）
6. **添加错误处理**（`catch` → 错误提示 Toast）
7. **表单提交改为 POST 请求**
8. **操作动作改为 PUT/DELETE 请求**
9. **确保改造后功能不变**（数据展示与交互行为保持一致）

---

### 阶段 3：统一 API 封装层（API Layer）

**目标**：生成统一请求基础层 + 模块 API 文件

#### 3.1 产物结构

```
api/                              （或 src/api/）
├── request.js                    ← 请求封装基础层（含 Mock 切换）
├── resource.js                   ← 资源模块 API
├── audit.js                      ← 审核模块 API
├── stats.js                      ← 统计模块 API
└── config.js                     ← 配置 API
```

#### 3.2 请求封装模板

- 微信小程序：`templates/request-wx.js`
- React/Vue (Axios)：`templates/request-axios.js`
- React (Fetch)：`templates/request-fetch.js`

---

### 阶段 4：Mock ↔ 正式接口切换层（Switch）

**目标**：预留一键切换机制，后续联调时无需改动页面代码

#### 4.1 切换架构

```
页面代码（不改动）
    ↓ 调用
api/resource.js（不改动）
    ↓ 调用
api/request.js（改这里）
    ↓ 根据配置
   ┌────────────────┐
   │  IS_MOCK=true  │──→ 项目现有 Mock 方案
   │  IS_MOCK=false │──→ 真实 HTTP 请求
   └────────────────┘
```

#### 4.2 request.js 中的切换点

**微信小程序**：

```javascript
const config = {
  IS_MOCK: true,
  baseURL: '',
}
```

**React/Vue**：

```javascript
const IS_MOCK = import.meta.env.VITE_API_MODE === 'mock'
```

---

## 输出产物清单

| 产物 | 路径 | 说明 |
|------|------|------|
| 数据发现报告 | `discovery_report.md` | 隐式接口需求分析结果 |
| 请求封装 | `api/request.js` | 统一请求层，含 Mock 切换 |
| API 模块 | `api/[module].js` | 按模块分组的 API 函数 |
| 改造后页面 | 原页面文件 | 替换为 API 调用 |

---

## 与 api-extractor-pro 的衔接（顺序固定）

```
1) static-to-api-layer
   - 完成页面 API 化改造
   - 不生成 contract/mock/docs

2) api-extractor-pro
   - 从改造后的 API 调用中扫描并生成 contract
   - 统一生成 Mock、OpenAPI、文档、校验和变更报告
```

---

## 强制规则

1. 仅做页面 API 化改造，不生成接口治理产物
2. 改造后页面行为必须与改造前一致
3. API 函数命名语义化（`getList` / `getById` / `create` / `update` / `delete`）
4. 不确定字段标记为 `x-todo-confirm`
5. 改造前建议先提交版本，支持渐进式按模块改造

---

## 参考资料

- 请求封装模板（微信小程序）：`templates/request-wx.js`
- 请求封装模板（Axios）：`templates/request-axios.js`
- 请求封装模板（Fetch）：`templates/request-fetch.js`
- 小程序 Mock 拦截器模板：`templates/mock-interceptor-wx.js`
- 数据发现报告模板：`templates/discovery-report.md`
- 改造前后对比示例：`examples/before-after.md`
