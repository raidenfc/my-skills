# my-skills

> **关键词**：软著申请自动化、计算机软件著作权、AI Agent Skill、Claude Skill、前端接口治理、API 文档生成、HTML 转微信小程序、静态页面 API 化

[![GitHub](https://img.shields.io/badge/GitHub-raidenfc%2Fmy--skills-blue?logo=github)](https://github.com/raidenfc/my-skills)

本仓库包含的 Skill 覆盖以下开发场景：

- **API 治理**：扫描前端代码生成接口契约、Mock、文档
- **页面 API 化改造**：将静态示例页面改造为标准 API 驱动
- **小程序转换**：将 HTML/React/Vue Demo 直接转为微信小程序
- **软著申请**：自动生成计算机软件著作权申请所需的三类文档

## 技能总览

| Skill | 核心功能 | 适合场景 | 文档 |
|---|---|---|---|
| [`api-extractor-pro`](#api-extractor-pro) | 前端 API 治理：扫描→契约→Mock→文档→校验 | 已有 API 调用，需统一文档和 Mock | [SKILL.md](./api-extractor-pro/SKILL.md) |
| [`static-to-api-layer`](#static-to-api-layer) | 静态页面 API 化：发现隐式接口→生成请求层→切换开关 | 静态 Demo 需正式接入后端 | [SKILL.md](./static-to-api-layer/SKILL.md) |
| [`html-to-miniprogram`](#html-to-miniprogram) | HTML/React/Vue Demo → 微信小程序原生项目 | 前端原型转小程序 | [SKILL.md](./html-to-miniprogram/SKILL.md) |
| [`software-copyright`](#software-copyright) | 自动生成软著申请三类材料 | 申请中国软件著作权证书材料 | [SKILL.md](./software-copyright/SKILL.md) |

## 快速安装

```bash
git clone https://github.com/raidenfc/my-skills.git
cd my-skills
bash scripts/sync-to-agents.sh
```

> 你也可以手动复制单个 skill 目录到你的 Agent skills 文件夹。

## 各 Skill 功能详解

### 🌟 api-extractor-pro

**前端 API 治理工作站**

从前端项目中的真实 API 调用出发，自动完成 **扫描 → 生成契约 → 确认 → Mock → 文档 → 校验 → 变更报告** 的完整链路。

**适用场景**

- 前端项目已发起 API 调用，但缺少接口文档
- 需要统一生成 `contract.json` / OpenAPI 3.1 / MSW Mock
- 需要在 CI/CD 中自动化校验接口一致性
- 多次迭代间追踪接口变更

**核心工作流（7 个阶段）**

```
1. Scan（扫描分析）       支持 Axios / Fetch / wx.request / React Query / SWR 等
2. Contract（生成契约）   唯一事实源 contract.json
3. Confirm（用户确认）    确认推断字段
4. Mock（生成 MSW）       按模块分组的 MSW handlers + mock 数据
5. Docs（生成文档）       Markdown 接口文档 + OpenAPI 3.1 YAML
6. Verify（一致性校验）   contract ↔ OpenAPI ↔ MSW 三方交叉校验
7. Report（变更报告）     对比上一版本生成 api-diff.md
```

**输出产物**

| 产物 | 文件 |
|------|------|
| 接口契约 | `contract.json` |
| MSW Mock | `mock/handlers/[module].js` + `mock/data/[module].json` |
| 接口文档 | `docs/api-docs.md` |
| OpenAPI | `docs/openapi.yaml` |
| 校验报告 | `reports/consistency-report.md` |
| 变更报告 | `reports/api-diff.md` |

> ⚠️ 微信小程序不支持 MSW，Mock 方案由 `static-to-api-layer` 提供的 `mock-interceptor-wx.js` 实现。

### 🌟 static-to-api-layer

**静态页面 API 化改造工具**

针对"前端先行"的开发模式：页面数据硬编码在 `mock.js` / `useState` / `data()` 中，需要正式 API 化接入后端。

**适用场景**

- HTML Demo 转换而来的项目需正式化
- 数据写死在页面 `data` / `constants` 中，未来需联调后端
- "先画页面再开发后端"的工作流
- 作为 `api-extractor-pro` 的前置工程化改造步骤

支持框架：React / Vue / 微信小程序

**核心工作流（4 个阶段）**

```
1. Discover（隐式接口发现）  扫描 7 类接口模式：列表/详情/筛选/分页/表单/状态变更/统计
2. Refactor（页面改造）      移除硬编码导入 → 替换为 API 调用 → 添加 loading 状态
3. API Layer（统一请求层）   生成 request.js 基础层 + 各模块 api/*.js
4. Switch（切换层预留）      IS_MOCK=true/false 一键切换 Mock 与真实接口
```

**输出产物**

| 产物 | 文件 |
|------|------|
| 发现报告 | `discovery_report.md` |
| 请求封装层 | `api/request.js` |
| API 模块文件 | `api/[module].js` |
| 改造后页面 | 原页面文件（替换为 API 调用） |

### 🌟 html-to-miniprogram

**HTML Demo → 微信小程序转换工具**

将任意前端 Demo（HTML / React / Vue 单文件或多文件）精准转换为**微信小程序原生开发**项目，还原 UI 和简单交互。

**转换范围**

- ✅ 页面 UI 还原（包含 Flex/Grid 布局、CSS 变量、动画）
- ✅ 简单交互（页面跳转、Tab 切换、Toast 提醒、弹窗）
- ✅ 数据展示（Mock 数据集中在 `utils/mock.js` 统一管理）
- ❌ 不实现业务逻辑（网络请求、用户认证、数据持久化）

**核心工作流（5 个阶段）**

```
1. 分析源文件       确认 TabBar/导航栏/图标方案等设计决策
2. 生成转换蓝图     conversion-blueprint.md（单一事实来源）
3. 初始化项目骨架   在 miniprogram/ 目录下初始化
4. 逐页转换         TabBar 页面优先，再转换子页面
5. 逐项验证         对照蓝图核查页面完整性、路由、样式、交互
```

**核心转换规则**

- **标签映射**：`div → view`、`span/p → text`、`img → image`、`a → navigator`、`ul/li → wx:for` 等
- **事件映射**：`onClick → bindtap`、`onChange → bindinput/bindchange` 等
- **样式转换**：`px → rpx`、选择器限制、Flex/Grid 完整支持、CSS 变量定义在 `page {}` 中
- **图标方案**：Emoji 占位（快速原型）或 SVG 转 PNG（精准还原）
- **路由导航**：`switchTab` / `navigateTo` / `navigateBack` 完整映射

### 🌟 software-copyright

**计算机软件著作权申请资料自动生成工具**

自动分析项目代码与文档，生成申请中国计算机软件著作权（软著）所需的三类正式材料。

**适用场景**

- 公司或个人需要申请软件著作权登记
- 项目代码已开发完成，需快速生成申报材料
- 支持 React / Vue / 小程序 / Go / Java / Python 等主流技术栈项目

**生成的三类材料**

| 材料 | 说明 |
|------|------|
| **软著主文档** | 包含硬件/软件环境、源程序量、开发目的、主要功能、技术特点等 |
| **代码文档（60页）** | 格式化代码材料，前 30 页 + 后 30 页，满足 ≥3180 行的申报要求 |
| **使用说明书** | 按用户端/管理端分章，逐功能模块详细描述操作步骤和系统响应（截图需要自己粘贴） |

**核心工作流（8 个步骤）**

```
1. 收集基本信息（软件名称、版本号、编制单位等）
2. 扫描项目结构（技术栈识别、代码行数统计）
3. 读取文档（README、context.md 等）
4. 生成软著规划书 → 用户确认后进入执行阶段
5. 生成软著主文档
6. 生成代码文档（≥60页，含强制行数校验门禁）
7. 生成使用说明书（含像素级 UI 还原 + 业务逻辑串联）
8. 输出并可选用 Pandoc 转 Word（.docx）
```

**智能功能**

- **深度功能挖掘**：从依赖库推断技术功能（Redis → 缓存、JWT → 认证等）
- **代码清洗**：自动过滤版权信息、TODO、调试语句、密钥等敏感信息
- **行数达标机制**：强制循环至代码行数满足申报要求，自动补充文件
- **Monorepo 支持**：可指定子项目或合并扫描全部子项目

## 推荐工作流

### 工作流 A：静态页面 → 完整 API 治理

```
1. static-to-api-layer
   发现隐式接口需求，完成页面 API 化改造，预留 Mock/真实接口切换层

2. api-extractor-pro
   从改造后的 API 调用生成 contract.json、MSW、OpenAPI、文档和一致性报告
```

### 工作流 B：HTML Demo → 微信小程序

```
1. html-to-miniprogram
   分析 Demo → 确认设计决策 → 生成蓝图 → 逐页转换 → 验证

（如需 API 化：后续运行 static-to-api-layer + api-extractor-pro）
```

### 工作流 C：软著申请

```
1. software-copyright
   收集信息 → 分析项目 → 生成规划书（用户确认）→ 生成三类材料 → 导出 Word
```

## 仓库结构

```text
my-skills/
├── README.md
├── scripts/
│   └── sync-to-agents.sh          # 同步到本地 Agent 环境
├── api-extractor-pro/
│   ├── SKILL.md
│   ├── scripts/                   # Python 脚本（scan/contract/mock/docs/verify）
│   ├── templates/                 # 文档模板
│   ├── references/                # 契约/OpenAPI/MSW 规范参考
│   └── examples/                  # Mock 和文档示例
├── static-to-api-layer/
│   ├── SKILL.md
│   ├── templates/                 # request.js 封装模板（wx/axios/fetch）
│   └── examples/                  # 改造前后对比示例
├── html-to-miniprogram/
│   └── SKILL.md
└── software-copyright/
    ├── SKILL.md
    └── templates/                 # 规划书/主文档/代码文档/使用说明书模板
```
