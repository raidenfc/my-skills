# 数据发现报告

> 生成时间：YYYY-MM-DD HH:mm
> 项目路径：`/path/to/project`
> 框架类型：React / Vue / 微信小程序

---

## 一、项目概览

| 项目 | 值 |
|------|-----|
| 框架 | |
| 页面数量 | |
| 数据文件 | |
| 总数据源数 | |
| 识别的隐式接口数 | |

---

## 二、数据源清单

### 2.1 集中式数据文件

| # | 文件路径 | 数据名 | 类型 | 条目数 | 字段概要 |
|---|---------|--------|------|-------|---------|
| 1 | `utils/mock.js` | `RESOURCES` | Array | 7 | id, company, service, category, ... |
| 2 | `utils/mock.js` | `CATEGORIES` | Array | 5 | id, name, icon, bgColor, ... |

### 2.2 页面内硬编码数据

| # | 页面 | 数据名 | 类型 | 说明 |
|---|------|--------|------|------|
| 1 | `home.js` | `CATEGORIES` | Array | 与 mock.js 重复定义 |

---

## 三、数据使用映射

| # | 页面 | 引用数据 | 使用方式 | 隐式接口模式 |
|---|------|---------|---------|-------------|
| 1 | `home.js` | `RESOURCES` | `.slice(0,3)` 取前3条 | 列表查询 + 分页 |
| 2 | `resources.js` | `RESOURCES` | `.filter()` 按分类筛选 | 列表查询 + 条件筛选 |
| 3 | `detail.js` | `getResourceById` | 按 ID 查找 | 详情查询 |
| 4 | `publish.js` | `CATEGORIES` | 表单选项 | 配置/字典数据 |
| 5 | `publish.js` | — | `handleSubmit()` 仅 Toast | 表单提交 |
| 6 | `admin-audit.js` | `AUDIT_QUEUE` | 直接赋值列表 | 列表查询 |
| 7 | `admin-audit.js` | — | `handleApprove()` 仅 Toast | 状态变更 |

---

## 四、隐式接口需求列表

| # | 模块 | 接口描述 | Method | URL | 来源 | 模式 | 状态 |
|---|------|---------|--------|-----|------|------|------|
| 1 | 资源 | 获取资源列表 | GET | /api/resources | RESOURCES | 列表+筛选+分页 | ✅ |
| 2 | 资源 | 获取资源详情 | GET | /api/resources/:id | getResourceById | 详情查询 | ✅ |
| 3 | 资源 | 发布资源 | POST | /api/resources | handleSubmit | 表单提交 | ⚠️ |
| 4 | 审核 | 获取审核队列 | GET | /api/audit/pending | AUDIT_QUEUE | 列表查询 | ✅ |
| 5 | 审核 | 审核通过 | PUT | /api/audit/:id/approve | handleApprove | 状态变更 | ⚠️ |
| 6 | 配置 | 获取分类列表 | GET | /api/config/categories | CATEGORIES | 字典数据 | ✅ |

### 状态说明

- ✅ **明确**：数据结构和使用方式清晰，可直接转化
- ⚠️ **需确认**：部分字段或逻辑需要用户确认
- ❓ **推断**：完全通过代码推断，可能不准确

---

## 五、发现的问题

1. **数据重复定义**：`CATEGORIES` 在 `mock.js` 和 `home.js` 中各定义了一份
2. **缺少用户模块**：页面有用户信息展示但无对应数据源
3. ...（根据实际情况列出）
