/**
 * React - 原生 Fetch 统一请求封装（含 Mock 切换）
 *
 * 使用说明：
 * 1. 将此文件放入 src/api/request.js
 * 2. Mock 模式：VITE_API_MODE=mock（.env.development），配合 MSW 使用
 * 3. 正式模式：VITE_API_MODE=real + 填入 VITE_API_BASE_URL
 * 4. 无需安装额外依赖
 */

// ============ 环境变量切换 ============
const IS_MOCK = import.meta.env.VITE_API_MODE === 'mock'
const BASE_URL = IS_MOCK ? '' : (import.meta.env.VITE_API_BASE_URL || '')
// =====================================

// 获取 Token
function getToken() {
  return localStorage.getItem('token') || ''
}

/**
 * 统一请求方法
 * @param {string} url - 接口路径（如 /api/resources）
 * @param {Object} [options] - 请求配置
 * @param {string} [options.method='GET'] - 请求方法
 * @param {Object} [options.data] - 请求参数
 * @param {Object} [options.headers] - 额外 headers
 * @returns {Promise}
 */
async function request(url, options = {}) {
  const { method = 'GET', data, headers = {} } = options

  const config = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  }

  // 添加鉴权 Token
  const token = getToken()
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }

  // GET 请求参数拼接到 URL
  let fullUrl = BASE_URL + url
  if (method === 'GET' && data) {
    const params = new URLSearchParams(data).toString()
    if (params) {
      const connector = fullUrl.includes('?') ? '&' : '?'
      fullUrl += `${connector}${params}`
    }
  }

  // 非 GET 请求放入 body
  if (method !== 'GET' && data) {
    config.body = JSON.stringify(data)
  }

  try {
    const response = await fetch(fullUrl, config)

    if (!response.ok) {
      if (response.status === 401) {
        console.warn('未登录，请先登录')
        // 跳转登录页
      }
      const errorData = await response.json().catch(() => ({}))
      throw errorData
    }

    const result = await response.json()

    if (result.code === 200) {
      return result
    }

    // 业务错误
    console.error(`[API Error] ${result.message}`)
    throw result
  } catch (error) {
    if (error.code !== undefined) throw error // 已处理的业务错误
    console.error('网络连接失败', error)
    throw error
  }
}

// 便捷方法
request.get = (url, data) => request(url, { method: 'GET', data })
request.post = (url, data) => request(url, { method: 'POST', data })
request.put = (url, data) => request(url, { method: 'PUT', data })
request.delete = (url, data) => request(url, { method: 'DELETE', data })

export default request
