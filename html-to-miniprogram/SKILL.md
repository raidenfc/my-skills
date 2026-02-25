---
name: html-to-miniprogram
description: 将 HTML/React/Vue 等前端 Demo 页面转换为微信小程序原生开发项目。重点是转换前端页面和简单交互（页面跳转、提醒等），不涉及业务逻辑，数据集中在 mock.js 中管理。
---

# HTML Demo 转微信小程序 Skill

将任意前端 Demo（HTML/React/Vue 单文件或多文件）转换为**微信小程序原生开发**项目，精准还原 UI 和简单交互。

> [!IMPORTANT]
> **转换范围**：仅转换前端页面 UI 和简单交互（页面跳转、Tab 切换、Toast 提醒、弹窗等），**不实现业务逻辑**（如网络请求、用户认证、数据持久化等）。所有页面用到的数据统一整合在 `utils/mock.js` 中管理。

> [!IMPORTANT]
> **交互语言**：与用户的所有对话、确认、提问、说明必须使用**中文**。包括但不限于：任务描述、设计决策询问、进度汇报、问题反馈等。代码中的变量名、文件路径等技术标识符保留英文。

> [!CAUTION]
> **连续执行**：用户确认设计决策（阶段 1）后，阶段 2 ~ 5（生成蓝图、初始化骨架、逐页转换、验证）必须**一口气连续完成**，中间不得暂停等待用户确认。不要在完成几个页面后就停下来汇报进度或请求继续——**所有页面必须连续完成后再进入验证阶段**。只有在遇到**无法自主决策的问题**时才暂停询问用户。

---

## 一、转换流程（按顺序执行）

### 阶段 1：分析源文件 → 确认设计决策

1. **通读 Demo 源码**，提取以下信息：
   - **页面数量与路由结构**（识别所有"视图/路由/Tab"）
   - 组件层级关系
   - 样式体系（CSS 变量、设计系统、色板）
   - 图标方案（SVG / icon font / 图片），列出所有使用的图标名称和颜色
   - 交互逻辑（点击事件、Tab 切换、页面跳转、弹窗提醒等简单交互）
   - 数据模型（用于 Mock 数据的结构）

   > [!CAUTION]
   > **页面提取是最关键的步骤，遗漏页面会导致最终产物缺页。** 必须通过以下方式**交叉验证**，确保不遗漏任何页面：
   >
   > 1. **路由配置**：检查 Router 配置、hash 路由、Tab 定义等，提取所有注册的路由
   > 2. **导航链接**：搜索源码中所有 `href`、`to`、`router.push`、`navigate` 等跳转目标
   > 3. **JS 事件跳转**：搜索 `onClick`、`handleClick` 等事件处理函数中的页面跳转逻辑
   > 4. **条件渲染的视图**：检查 `v-if`、`v-show`、`{condition && <Component>}` 等条件渲染，识别隐藏的子视图/页面
   > 5. **HTML 页面结构**：如果是单 HTML 文件，搜索所有 `section`/`div` 中通过 CSS `display:none` 或 JS 切换显示的独立视图
   >
   > 分析完成后，**必须明确告知用户总页面数**（如"共发现 13 个页面：4 个 TabBar 页面 + 9 个子页面"），让用户确认是否有遗漏。

2. **在生成蓝图之前，必须先与用户确认以下设计决策**：

   > [!CAUTION]
   > 以下决策直接影响蓝图内容和后续实现方式，**必须在蓝图创建前完成确认**，避免蓝图与实际执行脱节。

   - **页面完整性**：告知用户发现的页面总数和清单，确认是否有遗漏（使用固定模板）
   - **TabBar 样式**：系统默认 or 自定义（浮动胶囊等特殊设计需自定义）
   - **导航栏样式**：默认 or 自定义
   - **图标方案**（向用户说明两种方案的优劣，让用户选择）：
     - **方案 A：Emoji 占位**（快速原型）— 无需额外资源，开发速度快，适合快速验证布局，后续可替换为真实图标
     - **方案 B：SVG 转 PNG 图片** — 视觉效果精准，需要生成图标资源文件，适合对图标质量有要求的项目

   页面完整性确认模板（必须原样输出结构）：

   ```markdown
   已识别页面总数：N（TabBar: X，子页面: Y）
   TabBar 页面：
   - pages/xxx/xxx
   - pages/xxx/xxx
   子页面：
   - pages/xxx/xxx
   - pages/xxx/xxx
   疑似遗漏页面（若无则写“无”）：
   - ...
   ```

### 阶段 2：生成转换蓝图

根据阶段 1 的分析结果和用户确认的设计决策，**创建转换蓝图文件** `conversion-blueprint.md`，置于项目根目录。

> [!IMPORTANT]
> 蓝图是整个转换过程的**单一事实来源**。蓝图内容必须与用户确认的设计决策一致。

蓝图包含以下内容：

```markdown
# [项目名] 转换蓝图

## 一、页面清单

| 序号 | 页面名称 | 路径 | 类型 |
|------|---------|------|------|
| 1 | 首页 | pages/home/home | TabBar |
| 2 | 详情页 | pages/detail/detail | 子页面 |
| ... | ... | ... | ... |

## 二、路由结构

- TabBar 页面：[列表]
- 子页面：[列表]
- 页面间跳转关系：[描述]

## 三、组件层级

- 全局组件：[列表]
- 页面私有组件：[列表]

## 四、样式体系

- CSS 变量/设计 Token：[列出关键变量]
- 色板：[主色、辅色、背景色等]
- 字体：[字号体系]

## 五、图标方案：[Emoji / PNG]

<!-- 根据用户选择的方案填写不同内容 -->

### 如果选择 Emoji 方案：

| 原图标名称 | Emoji 字符 | 使用位置 |
|-----------|-----------|--------|
| chevron-left | ‹ | 所有子页面返回按钮 |
| home | 🏠 | TabBar-首页 |
| ... | ... | ... |

### 如果选择 PNG 方案：

| 图标名称 | 颜色 (Hex) | 文件名 | 使用位置 |
|---------|-----------|--------|--------|
| house | #94a3b8 | house.png | TabBar |
| ... | ... | ... | ... |

## 六、交互逻辑

| 交互类型 | 描述 | 所在页面 |
|---------|------|--------|
| Tab 切换 | 底部 TabBar 导航 | 全局 |
| 页面跳转 | 点击卡片进入详情 | 首页 |
| Toast 提醒 | 点击按钮弹出提醒 | ... |
| ... | ... | ... |

## 七、Mock 数据结构

- [列出每个页面需要的 Mock 数据字段和结构]
```

### 阶段 3：初始化项目骨架

> [!IMPORTANT]
> 小程序项目必须生成在一个**单独的 `miniprogram` 文件夹**中，与源 Demo 文件分离，避免混淆。

按以下顺序创建文件：

```
miniprogram/
├── app.js            # 全局入口
├── app.json          # 页面注册 + TabBar + window 配置
├── app.wxss          # 全局样式（CSS 变量 + 工具类）
├── project.config.json
├── sitemap.json
├── custom-tab-bar/   # 如需自定义 TabBar
│   ├── index.js / index.json / index.wxml / index.wxss
├── assets/
│   └── icons/        # 图标资源
├── utils/
│   ├── mock.js       # 所有 Mock 数据集中管理
│   └── util.js       # 工具函数
└── pages/            # 每个页面 4 个文件
    ├── page-name/
    │   ├── page-name.js
    │   ├── page-name.json
    │   ├── page-name.wxml
    │   └── page-name.wxss
```

> [!IMPORTANT]
> `project.config.json` 必须配置 `"miniprogramRoot": "miniprogram/"`，确保微信开发者工具正确识别源码目录。

### 阶段 4：逐页转换（先 TabBar 页面，再子页面）

- 严格按照蓝图中的页面清单顺序逐页转换
- 所有页面数据从 `utils/mock.js` 引入
- 交互逻辑仅实现简单交互（跳转用 `wx.navigateTo` / `wx.switchTab`，提醒用 `wx.showToast` / `wx.showModal`）
- 业务逻辑部分用 `wx.showToast({ title: '功能开发中', icon: 'none' })` 占位

**单个页面的转换步骤：**

1. **`.json`（配置）**：设置页面标题、导航栏样式、引用的自定义组件等（组件声明是后续 WXML 中使用自定义组件的前提）
2. **`.wxml`（结构）**：对照 Demo 源码逐元素转换，按标签映射表替换标签
3. **`.wxss`（样式）**：迁移对应 CSS，按样式转换规则处理单位、选择器和布局
4. **`.js`（数据 + 交互）**：从 `mock.js` 引入数据，在 `onLoad` 中 `setData`，绑定简单交互事件

### 阶段 5：逐项验证

按照蓝图文件进行逐步验证（详见 **第七节 验证流程**）。

---

## 二、核心转换规则

### 2.1 标签映射

| HTML / React | 微信小程序 | 说明 |
|---|---|---|
| `<div>` | `<view>` | 通用容器 |
| `<span>` / `<p>` | `<text>` | 文本必须包在 text 中 |
| `<img>` | `<image>` | 必须设宽高；常用 mode：`aspectFill`（裁剪填充）、`aspectFit`（完整显示）、`widthFix`（宽度固定高度自适应）、`scaleToFill`（默认拉伸） |
| `<input>` | `<input>` | 保留，但事件名不同 |
| `<textarea>` | `<textarea>` | 原生组件，层级最高 |
| `<button>` | `<button>` / `<view>` | 视需求选择 |
| `<a href>` | `<navigator>` / 事件 | 小程序无 a 标签 |
| `<ul>` / `<li>` | `<view>` + `wx:for` | 列表渲染 |
| `<svg>` | ❌ 不支持 | 用 image 替代（见图标方案）|
| `<select>` | `<picker>` | 选择器组件 |
| `<form>` | `<form>` | 保留，事件名变化 |
| `<scroll-view>` | `<scroll-view>` | 必须设固定高度才能滚动 |
| 轮播图（JS 库） | `<swiper>` + `<swiper-item>` | 内置轮播组件，支持自动播放和循环 |
| `<video>` | `<video>` | 原生组件，需用 cover-view 覆盖 |
| `<audio>` | `<audio>` / `wx.createInnerAudioContext` | 推荐用 API 方式 |
| `<input type="radio">` | `<radio-group>` + `<radio>` | 单选框 |
| `<input type="checkbox">` | `<checkbox-group>` + `<checkbox>` | 多选框 |
| toggle / switch | `<switch>` | 开关组件 |
| `<input type="range">` | `<slider>` | 滑块组件 |
| 富文本 HTML 内容 | `<rich-text nodes="{{html}}">` | 支持部分 HTML 标签渲染 |
| 覆盖原生组件的浮层 | `<cover-view>` / `<cover-image>` | 用于覆盖 video 等原生组件 |

### 2.2 事件映射

| Web 事件 | 小程序事件 | 说明 |
|---|---|---|
| `onClick` | `bindtap` | 点击事件（冒泡） |
| `onClick`（阻止冒泡） | `catchtap` | 点击事件（阻止冒泡） |
| 长按 | `bindlongpress` | 超过 350ms 触发，推荐代替 longtap |
| `onTouchStart` | `bindtouchstart` | 手指触摸开始 |
| `onTouchMove` | `bindtouchmove` | 手指触摸后移动 |
| `onTouchEnd` | `bindtouchend` | 手指触摸结束 |
| `onChange`（input） | `bindinput` | 输入框内容变化 |
| `onChange`（picker/switch） | `bindchange` | picker、switch、slider 等值变化 |
| `onFocus` | `bindfocus` | 输入框获取焦点 |
| `onBlur` | `bindblur` | 输入框失去焦点 |
| `onSubmit` | `bindsubmit` | 表单提交 |
| `onScroll` | `bindscroll` | 滚动事件（scroll-view） |
| `onLoad`（img） | `bindload` | 图片/视频加载成功 |
| `onError`（img） | `binderror` | 图片/视频加载失败 |

**属性映射**（非事件，但转换时同样重要）：

| Web 属性 | 小程序属性 | 说明 |
|---|---|---|
| `className` | `class` | 类名属性 |
| `style={{}}` | `style=""` | 内联样式（字符串格式） |
| `dangerouslySetInnerHTML` | `<rich-text nodes>` | 富文本渲染 |
| `hidden` / `v-show` | `hidden="{{bool}}"` | 控制显隐（不销毁节点，比 `wx:if` 性能更好适合频繁切换） |
| `data-*` | `data-*` | 自定义数据属性，通过 `e.currentTarget.dataset` 获取 |

> [!TIP]
> **事件冒泡机制**：`bind` 前缀允许事件冒泡，`catch` 前缀阻止冒泡。需要阻止父元素响应事件时用 `catch`（如弹窗遮罩的点击穿透问题）。

### 2.3 样式转换（CSS → WXSS）

**核心规则：**

1. **单位转换**：`px` → `rpx`（1px = 2rpx），除以下情况保留 `px`：
   - `border`：细边框保留 `1px`（避免在高分屏上过粗），粗边框正常按 1px=2rpx 换算
   - 与系统 API 返回值配合的尺寸（如 statusBarHeight）
   - `font-size` 可酌情使用 `rpx` 或 `px`
2. **选择器支持情况**：
   - ✅ 类选择器（`.class {}`）
   - ✅ ID 选择器（`#id {}`）
   - ✅ 后代选择器、子选择器（`>`）、兄弟选择器（`~`、`+`）
   - ✅ 伪类：`:active`、`:first-child`、`:last-child`、`:not`、`:nth-child`
   - ✅ 伪元素：`::before`、`::after`（仅这两个）
   - ❌ 标签选择器（`div {}`, `span {}`）
   - ❌ `*` 通配符选择器
   - ❌ 属性选择器（`[attr]`、`[type="text"]`）
3. **不支持或受限的布局属性**：
   - ⚠️ `float`：支持但在 Flex 容器内失效，**推荐用 Flex 布局替代**
   - ⚠️ `display: inline-block`：行为可能与 Web 不完全一致，**推荐用 Flex 布局替代**
   - ⚠️ `position: fixed`：支持，但父元素有 `transform` 时会失效；仅支持相对视口定位
   - ⚠️ `overflow: scroll`：支持不稳定且受渲染引擎影响，**推荐使用 `<scroll-view>` 组件**实现可靠滚动
   - ❌ WXSS 中不支持引入**本地字体文件和本地图片**，必须使用在线资源或 Base64 编码
4. **支持的现代 CSS**：
   - ✅ `display: flex` 全系列（**推荐首选布局方式**）
   - ✅ `display: grid` / `grid-template-columns`
   - ✅ `backdrop-filter: blur()`
   - ✅ `linear-gradient()`
   - ✅ `box-shadow`
   - ✅ CSS 变量 `var(--xxx)`（在 `page {}` 中定义，非 `:root`）
   - ✅ `border-radius`
   - ✅ `position: sticky`
   - ✅ `@import` 导入外部样式表
5. **Tailwind CSS 迁移**：将工具类转为等效 WXSS：
   - 提取颜色为 CSS 变量定义在 `app.wxss` 的 `page {}` 选择器中
   - 将 `flex`, `grid`, `gap`, `rounded` 等转为对应属性
   - `hover:` 伪类可用 `.active` 类 + `bindtouchstart/end` 模拟，或省略
6. **全局样式策略**：
   - CSS 变量定义在 `app.wxss` 的 `page {}` 中（**不是 `:root`**）
   - 通用工具类（flex 布局、文本截断等）定义在 `app.wxss`
   - 页面私有样式写在各自的 `.wxss` 文件中
   - 自定义组件默认启用**样式隔离**，组件内外样式互不影响

### 2.4 路由与导航

| Web 路由方式              | 小程序对应                   |
|--------------------------|------------------------------|
| React Router / hash 路由  | `app.json` 的 `pages` 注册   |
| Tab 切换                  | `wx.switchTab({ url })`     |
| 页面跳转                  | `wx.navigateTo({ url })`    |
| 页面重定向（替换当前页）    | `wx.redirectTo({ url })`    |
| 返回上一页                | `wx.navigateBack()`         |
| 参数传递（query string）   | `options` 参数 / `globalData` |

**路由类型判断：**

- 底部 Tab 对应的页面 → 注册为 TabBar 页面
- 其他页面 → 注册为普通页面
- Tab 间跳转必须用 `switchTab`，不能用 `navigateTo`

> [!WARNING]
> **页面栈限制**：小程序页面栈最多 **10 层**，超过后 `navigateTo` 会失败。深层级跳转考虑用 `redirectTo`（替换当前页，不增加栈）。

### 2.5 数据与逻辑

| Web 概念                    | 小程序对应                        |
|----------------------------|-----------------------------------|
| `useState` / `data()`     | `Page({ data: {} })`             |
| `setState` / 赋值          | `this.setData({ key: value })`   |
| `useEffect` / `mounted`   | `onLoad()` / `onShow()`          |
| `props`                    | 组件的 `properties`               |
| `context` / `provide`     | `getApp().globalData`             |
| `fetch` / `axios`         | Mock 数据直接引入（不实现真实请求）|
| `localStorage`            | `wx.setStorageSync()` / `getStorageSync()` |
| 条件渲染 `{cond && <X/>}` | `wx:if="{{cond}}"`               |
| 列表渲染 `.map()`          | `wx:for="{{list}}" wx:key="id"` |
| 模板字符串                  | `{{}}` 数据绑定                   |

> [!TIP]
> **`wx:key` 用法**：值为列表项的**属性名字符串**（不加 `item.` 前缀），如 `wx:key="id"`。如果列表项本身是唯一字符串/数字，可用 `wx:key="*this"`。不设 `wx:key` 会触发警告且影响渲染性能。

**Mock 数据策略：**

> [!NOTE]
> 所有页面数据统一在 `utils/mock.js` 中定义和导出，页面 JS 通过 `const mock = require('../../utils/mock.js')` 引入，在 `onLoad` 中 `setData`。**不实现 `wx.request` 等网络请求**。

### 2.6 图标处理方案

微信小程序**不支持 SVG 标签**，需要替换方案。图标方案应在**阶段 1 中与用户确认**，蓝图内容根据用户选择适配。

#### 方案 A：Emoji 占位（快速原型）

使用 Emoji 字符代替图标，无需额外资源文件，适合快速验证布局。

**实施规范：**

1. **全局样式**：在 `app.wxss` 中定义通用 Emoji 图标类：

   ```css
   /* Emoji 图标通用样式 */
   .emoji-icon {
     display: inline-flex;
     align-items: center;
     justify-content: center;
     text-align: center;
     line-height: 1;
   }
   ```

2. **WXML 写法**：使用 `<text>` 标签包裹 Emoji，同时添加 `emoji-icon` 基础类和具体图标类：

   ```html
   <!-- 返回按钮（使用 Unicode 字符） -->
   <text class="emoji-icon back-icon">‹</text>

   <!-- 普通 Emoji 图标 -->
   <text class="emoji-icon phone-icon">📞</text>

   <!-- 右箭头 -->
   <text class="emoji-icon arrow-icon">›</text>
   ```

3. **WXSS 规则**：图标样式使用 `font-size` 控制大小（**不是** `width`/`height`）：

   ```css
   /* ✅ 正确：用 font-size 控制 Emoji 大小 */
   .back-icon {
     font-size: 56rpx;
     color: var(--slate-800);
   }

   /* ❌ 错误：width/height 对文本无效 */
   .back-icon {
     width: 52rpx;
     height: 52rpx;
   }
   ```

4. **常用 Emoji 映射参考**：

   | 原图标用途 | 推荐 Emoji / 字符 | 说明 |
   |-----------|------------------|------|
   | 返回按钮 | `‹`（U+2039） | Unicode 单左尖括号，比 `<` 更美观 |
   | 右箭头 | `›`（U+203A） | Unicode 单右尖括号 |
   | 首页 | 🏠 | |
   | 搜索 | 🔍 | |
   | 用户/头像 | 👤 | |
   | 设置 | ⚙️ | |
   | 电话 | 📞 | |
   | 编辑 | ✏️ | |
   | 删除 | 🗑️ | |
   | 添加 | ➕ | |
   | 已认证/通过 | ✅ | |
   | 禁止/下架 | 🚫 | |
   | 文档 | 📄 | |
   | 日历 | 📅 | |
   | 位置 | 📍 | |
   | 图表 | 📊 | |

> [!TIP]
> 蓝图中应包含完整的**图标名称 → Emoji 字符映射表**，确保全项目一致性。

#### 方案 B：SVG 转 PNG 图片

如果用户选择精准视觉还原，使用以下工具将 SVG 图标转换为 PNG：

**工具 1：Shell 脚本方式（`generate_icons.sh`）**

从 Lucide 等图标库下载 SVG，替换颜色后用 `sips` 转为 PNG：

```bash
#!/bin/bash
set -euo pipefail
# 定义图标数组，格式："图标名:颜色:文件名"
ICONS=(
    "house:#94a3b8:house.png"
    "house:#ffffff:house-active.png"
    # ... 按蓝图中的图标清单填写
)

mkdir -p miniprogram/assets/icons

for item in "${ICONS[@]}"; do
    IFS=':' read -r name color filename <<< "$item"
    if ! curl -s -L -f "https://unpkg.com/lucide-static@latest/icons/$name.svg" -o temp.svg; then
        echo "下载失败: $name" >&2
        continue
    fi
    sed "s/currentColor/$color/g" temp.svg > colored.svg
    sips -s format png colored.svg --out "miniprogram/assets/icons/$filename" -z 64 64 > /dev/null
    rm temp.svg colored.svg
done
```

> [!NOTE]
> 上述脚本依赖 `sips`（macOS）。非 macOS 环境可改用 `magick colored.svg "miniprogram/assets/icons/$filename"` 生成 PNG。

**工具 2：HTML 页面方式（`icon_generator.html`）**

在浏览器中用 Lucide JS 库渲染 SVG 到 Canvas，导出 PNG 的 base64 数据：

```javascript
const ICONS_TO_GENERATE = [
    { name: 'house', color: '#94a3b8', filename: 'house.png' },
    // ... 按蓝图中的图标清单填写
];
// 通过 Canvas 绘制 SVG 并导出 base64 PNG
```

> [!TIP]
> 两种工具可按需在项目的 `tools/` 目录下创建，根据蓝图中的图标清单填充具体的图标列表。

---

## 三、自定义 TabBar 实现要点

当 Demo 的 TabBar 不是标准样式时（如浮动胶囊、异形底栏），需使用自定义 TabBar：

1. `app.json` 中设置 `"tabBar": { "custom": true, ... }`
2. 在项目根目录创建 `custom-tab-bar/` 组件（固定路径名）
3. 每个 TabBar 页面的 `onShow` 中更新选中态：

   ```javascript
   onShow() {
     if (typeof this.getTabBar === 'function' && this.getTabBar()) {
       this.getTabBar().setData({ selected: 0 }) // 当前页索引
     }
   }
   ```

4. **注意**：即使 `custom: true`，`app.json` 的 `tabBar.list` 仍需完整配置（框架要求）

---

## 四、自定义导航栏实现要点

当页面需要自定义顶部导航栏（渐变背景、大标题等）：

1. 页面 JSON 设置 `"navigationStyle": "custom"`
2. `app.js` 的 `onLaunch` 中获取系统信息：

   ```javascript
   const systemInfo = wx.getWindowInfo()
   this.globalData.statusBarHeight = systemInfo.statusBarHeight
   const menuButton = wx.getMenuButtonBoundingClientRect()
   this.globalData.navBarHeight = (menuButton.top - systemInfo.statusBarHeight) * 2 + menuButton.height
   ```

3. 页面顶部避让状态栏时，使用数据绑定到 `style`（不要把 `{{}}` 写进 `.wxss`）：

   ```html
   <view class="nav-wrap" style="padding-top: {{statusBarHeight}}px;">
     ...
   </view>
   ```

   ```javascript
   const app = getApp()
   Page({
     data: { statusBarHeight: 0 },
     onLoad() {
       this.setData({ statusBarHeight: app.globalData.statusBarHeight || 0 })
     }
   })
   ```

---

## 五、Mock 数据管理

所有页面数据集中在 `utils/mock.js` 中管理：

```javascript
// utils/mock.js

// 首页数据
const homeData = {
  banners: [ /* ... */ ],
  categories: [ /* ... */ ],
  hotItems: [ /* ... */ ],
};

// 其他页面数据...
const profileData = { /* ... */ };

module.exports = {
  homeData,
  profileData,
  // ...
};
```

**页面中引用方式：**

```javascript
// pages/home/home.js
const mock = require('../../utils/mock.js')

Page({
  data: {},
  onLoad() {
    this.setData(mock.homeData)
  },
  // 简单交互
  onItemTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` })
  },
  onButtonTap() {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  }
})
```

---

## 六、常见陷阱与注意事项

1. **文本必须包裹在 `<text>` 中**，裸文本在某些场景样式不生效
2. **`wx:for` 的默认变量**是 `item` 和 `index`，可通过 `wx:for-item` / `wx:for-index` 重命名
3. **`image` 组件必须设宽高**，否则默认 320×240
4. **WXSS 不支持标签选择器**，所有样式必须用类选择器
5. **`scroll-view` 必须设固定高度**才能触发滚动
6. **页面文件名与文件夹名必须一致**：`pages/home/home.js`
7. **小程序包体积限制 2MB**（主包），大图片应使用网络地址
8. **`textarea` 是原生组件**，层级最高，样式覆盖需注意
9. **CSS 动画支持有限**，复杂动画推荐使用关键帧动画 `this.animate()` 或 WXS 响应事件（`wx.createAnimation()` 已不推荐使用）
10. **数据绑定是单向的**，表单双向绑定需手动 `bindinput` + `setData`
11. **`setData` 性能**：单次 `setData` 数据量不宜过大，避免传入整个大对象；尽量只更新变化的字段
12. **`wx:if` vs `hidden`**：`wx:if` 会销毁/重建节点，`hidden` 仅控制显隐不销毁。频繁切换时用 `hidden` 性能更好
13. **`onLoad` vs `onShow`**：`onLoad` 仅在页面首次加载时执行一次，`onShow` 每次页面显示都执行（TabBar 页面切换回来时也会触发 `onShow`）

---

## 七、验证流程

完成所有页面转换后，结合蓝图文件 `conversion-blueprint.md` 进行逐项验证：

### 7.1 页面完整性验证

逐一核对蓝图中的**页面清单**，确认：

- [ ] 每个页面的 4 个文件（.js / .json / .wxml / .wxss）是否齐全
- [ ] `app.json` 中页面注册是否完整
- [ ] TabBar 配置是否正确

### 7.2 路由验证

核对蓝图中的**路由结构**，确认：

- [ ] TabBar 页面间切换正常（`switchTab`）
- [ ] 子页面跳转正常（`navigateTo`）
- [ ] 页面返回正常（`navigateBack`）
- [ ] 参数传递正确

### 7.3 样式验证

核对蓝图中的**样式体系**，确认：

- [ ] CSS 变量定义完整（对照色板和设计 Token）
- [ ] 全局工具类齐全
- [ ] 各页面视觉还原度与 Demo 一致

### 7.4 图标验证

核对蓝图中的**图标清单**，根据所选方案进行验证：

**Emoji 方案验证项：**

- [ ] `app.wxss` 中已定义 `.emoji-icon` 全局样式
- [ ] 所有**图标类** `<image>` 标签已替换为 `<text class="emoji-icon ...">` 标签（非图标的图片如 banner、头像等仍使用 `<image>`）
- [ ] Emoji 字符与蓝图映射表一致
- [ ] WXSS 中图标样式使用 `font-size`（非 `width`/`height`）
- [ ] 各页面 Emoji 显示正常、对齐无偏移

**PNG 方案验证项：**

- [ ] 所有图标资源文件存在于 `assets/icons/`
- [ ] 图标颜色和尺寸正确
- [ ] 各页面中图标引用路径正确

### 7.5 交互验证

核对蓝图中的**交互逻辑**，确认：

- [ ] 所有简单交互（跳转、切换、提醒）正常工作
- [ ] 业务逻辑部分已用 Toast 占位
- [ ] Mock 数据正确显示

### 7.6 数据验证

核对蓝图中的 **Mock 数据结构**，确认：

- [ ] `utils/mock.js` 包含所有页面的数据
- [ ] 各页面数据引用和渲染正确

> [!TIP]
> 验证过程中每完成一项，仅在 `conversion-blueprint.md` 的验证清单中标记 `[x]`。发现问题立即修复后再继续。

---

## 八、执行优先级

转换时按以下优先级推进：

1. **先蓝图后编码**：先完成阶段 1 的分析蓝图，确认后再开始编码
2. **先骨架后血肉**：先创建项目配置和全局样式，再逐页转换
3. **先 TabBar 后子页面**：TabBar 页面是主入口，优先实现
4. **先 UI 后交互**：先精准还原 UI 和样式，再接入简单交互和 Mock 数据
5. **先整体后细节**：先保证页面结构正确，再微调间距、颜色、阴影等
