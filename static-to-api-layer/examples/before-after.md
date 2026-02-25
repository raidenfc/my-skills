# 改造前后对比

本文档展示静态页面改造为 API 调用的完整前后对比，覆盖三大框架。

---

## 微信小程序示例

### 改造前：resources.js

```javascript
const { CATEGORIES, RESOURCES, getCategoryName } = require('../../utils/mock')

Page({
  data: {
    categories: CATEGORIES,
    selectedCategory: 'all',
    resources: [],
    allResources: []
  },
  onLoad() {
    const allResources = RESOURCES.map(item => ({
      ...item,
      categoryName: getCategoryName(item.category)
    }))
    this.setData({
      allResources,
      resources: allResources
    })
  },
  selectCategory(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ selectedCategory: id })
    this.filterResources(id)
  },
  filterResources(categoryId) {
    if (categoryId === 'all') {
      this.setData({ resources: this.data.allResources })
    } else {
      const filtered = this.data.allResources.filter(r => r.category === categoryId)
      this.setData({ resources: filtered })
    }
  }
})
```

### 改造后：resources.js

```javascript
const resourceApi = require('../../api/resource')
const configApi = require('../../api/config')

Page({
  data: {
    categories: [],
    selectedCategory: 'all',
    resources: [],
    loading: true
  },
  onLoad() {
    this.loadCategories()
    this.loadResources()
  },
  // 加载分类列表
  async loadCategories() {
    const res = await configApi.getCategories()
    this.setData({ categories: res.data })
  },
  // 加载资源列表
  async loadResources(category) {
    this.setData({ loading: true })
    try {
      const params = {}
      if (category && category !== 'all') {
        params.category = category
      }
      const res = await resourceApi.getList(params)
      this.setData({
        resources: res.data.list,
        loading: false
      })
    } catch (err) {
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },
  // 选择分类 → 调 API 重新筛选
  selectCategory(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ selectedCategory: id })
    this.loadResources(id)
  }
})
```

### 新建的 API 模块：api/resource.js

```javascript
const request = require('./request')

// 获取资源列表
function getList(params) {
  return request({ url: '/api/resources', method: 'GET', data: params })
}

// 获取资源详情
function getById(id) {
  return request({ url: `/api/resources/${id}`, method: 'GET' })
}

// 发布资源
function create(data) {
  return request({ url: '/api/resources', method: 'POST', data })
}

module.exports = { getList, getById, create }
```

---

## React 示例

### 改造前

```jsx
import { RESOURCES, getCategoryName } from '../mock'

function ResourcesPage() {
  const [resources] = useState(RESOURCES.map(item => ({
    ...item,
    categoryName: getCategoryName(item.category)
  })))
  const [selectedCategory, setSelectedCategory] = useState('all')

  const filtered = selectedCategory === 'all'
    ? resources
    : resources.filter(r => r.category === selectedCategory)

  return <ResourceList items={filtered} />
}
```

### 改造后

```jsx
import { useState, useEffect } from 'react'
import { getResourceList } from '../api/resource'

function ResourcesPage() {
  const [resources, setResources] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResources(selectedCategory)
  }, [selectedCategory])

  async function loadResources(category) {
    setLoading(true)
    try {
      const params = category !== 'all' ? { category } : {}
      const res = await getResourceList(params)
      setResources(res.data.list)
    } finally {
      setLoading(false)
    }
  }

  return loading ? <Loading /> : <ResourceList items={resources} />
}
```

---

## Vue 示例

### 改造前

```vue
<script>
import { RESOURCES, getCategoryName } from '../mock'

export default {
  data() {
    return {
      resources: RESOURCES.map(item => ({
        ...item,
        categoryName: getCategoryName(item.category)
      })),
      selectedCategory: 'all'
    }
  },
  computed: {
    filteredResources() {
      if (this.selectedCategory === 'all') return this.resources
      return this.resources.filter(r => r.category === this.selectedCategory)
    }
  }
}
</script>
```

### 改造后

```vue
<script>
import { getResourceList } from '../api/resource'

export default {
  data() {
    return {
      resources: [],
      selectedCategory: 'all',
      loading: true
    }
  },
  watch: {
    selectedCategory(val) {
      this.loadResources(val)
    }
  },
  mounted() {
    this.loadResources(this.selectedCategory)
  },
  methods: {
    async loadResources(category) {
      this.loading = true
      try {
        const params = category !== 'all' ? { category } : {}
        const res = await getResourceList(params)
        this.resources = res.data.list
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
```

---

## 关键变化总结

| 维度 | 改造前 | 改造后 |
|------|--------|--------|
| 数据来源 | `require('../../utils/mock')` | `require('../../api/resource')` |
| 初始数据 | 同步赋值硬编码数据 | 空数组 `[]`，异步请求填充 |
| 筛选逻辑 | 前端 `.filter()` 内存过滤 | API 参数传递，服务端筛选 |
| 加载状态 | 无 | 有 `loading` 状态 |
| 错误处理 | 无 | `catch` + Toast 提示 |
| 后续切换 | 无法切 | 改 `IS_MOCK` 即切到真实后端 |
