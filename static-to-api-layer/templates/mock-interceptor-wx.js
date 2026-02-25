/**
 * 微信小程序 Mock 拦截器
 *
 * 原理：在 request.js 中当 IS_MOCK=true 时，
 * 不发起真实 wx.request，而是匹配本地路由表，直接返回 Mock 数据。
 *
 * 使用方式：
 * 1. 将此文件放入 mock/mock-server.js
 * 2. 按模块注册 handler（参考下方示例）
 * 3. 在 api/request.js 中 IS_MOCK=true 时调用 mockRequest()
 *
 * 注意：此方案仅用于小程序开发阶段，不需要安装任何依赖。
 * React/Vue 项目请使用 MSW（由 api-extractor-pro 生成）。
 */

// 模拟网络延迟
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// 统一成功响应
function success(data, message = 'success') {
  return { code: 200, message, data }
}

// 统一错误响应
function error(code, message) {
  return { code, message, data: null }
}

// ============================================================
// 路由表：按 "METHOD URL" 格式注册 handler
// 支持路径参数，如 /api/resources/:id
// ============================================================
const handlers = {
  // ======== 示例：资源模块 ========

  // 获取资源列表（支持筛选 + 分页）
  'GET /api/resources': async (params) => {
    await delay(300)
    const data = require('./data/resource.json')
    let list = [...data.list]

    // 条件筛选
    if (params.category && params.category !== 'all') {
      list = list.filter(item => item.category === params.category)
    }

    // 分页
    const page = parseInt(params.page) || 1
    const pageSize = parseInt(params.pageSize) || 10
    const total = list.length
    const start = (page - 1) * pageSize

    return success({
      list: list.slice(start, start + pageSize),
      total,
      page,
      pageSize,
    })
  },

  // 获取详情
  'GET /api/resources/:id': async (params) => {
    await delay(200)
    const data = require('./data/resource.json')
    const item = data.list.find(r => r.id === parseInt(params.id))
    if (!item) return error(404, '资源不存在')
    return success(item)
  },

  // 创建资源
  'POST /api/resources': async (params, body) => {
    await delay(500)
    if (!body.company) return error(400, '公司名称不能为空')
    return success({
      id: Date.now(),
      ...body,
      status: '待审核',
      createdAt: new Date().toISOString(),
    }, '发布成功')
  },
}

// ============================================================
// 路由匹配引擎
// ============================================================

/**
 * 匹配 URL 路径，支持 :param 路径参数
 * @param {string} pattern - 路由模式，如 /api/resources/:id
 * @param {string} url - 实际请求路径，如 /api/resources/123
 * @returns {Object|null} 匹配结果 { matched: true, params: { id: '123' } }
 */
function matchRoute(pattern, url) {
  // 去除 query string
  const cleanUrl = url.split('?')[0]
  const patternParts = pattern.split('/')
  const urlParts = cleanUrl.split('/')

  if (patternParts.length !== urlParts.length) return null

  const params = {}
  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i].startsWith(':')) {
      params[patternParts[i].slice(1)] = urlParts[i]
    } else if (patternParts[i] !== urlParts[i]) {
      return null
    }
  }
  return params
}

/**
 * 解析 URL 中的 query 参数
 */
function parseQuery(url) {
  const query = {}
  const idx = url.indexOf('?')
  if (idx === -1) return query
  url.slice(idx + 1).split('&').forEach(pair => {
    const [key, val] = pair.split('=')
    if (key) query[decodeURIComponent(key)] = decodeURIComponent(val || '')
  })
  return query
}

/**
 * Mock 请求主入口
 * 在 request.js 中 IS_MOCK=true 时调用此函数代替 wx.request
 *
 * @param {Object} options - 与 wx.request 相同的参数
 * @param {string} options.url - 请求路径
 * @param {string} options.method - 请求方法
 * @param {Object} options.data - 请求数据
 * @returns {Promise} 返回 Mock 响应
 */
async function mockRequest(options) {
  const { url, method = 'GET', data = {} } = options
  const upperMethod = method.toUpperCase()
  const queryParams = parseQuery(url)

  // 遍历路由表寻找匹配
  for (const [route, handler] of Object.entries(handlers)) {
    const [routeMethod, routePath] = route.split(' ')
    if (routeMethod !== upperMethod) continue

    const pathParams = matchRoute(routePath, url)
    if (pathParams !== null) {
      // 合并参数：路径参数 + query 参数（GET 参数约定拼在 URL）
      const params = { ...queryParams, ...pathParams }
      const body = upperMethod === 'GET' ? {} : data

      console.log(`[Mock] ${upperMethod} ${url}`)
      const result = await handler(params, body)
      return result
    }
  }

  // 未匹配到路由
  console.warn(`[Mock] 未匹配到路由: ${upperMethod} ${url}`)
  return error(404, `Mock 路由未定义: ${upperMethod} ${url}`)
}

module.exports = {
  mockRequest,
  handlers,
}
