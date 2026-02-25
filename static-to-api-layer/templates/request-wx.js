/**
 * 微信小程序 - 统一请求封装（含 Mock 切换）
 * 
 * 使用说明：
 * 1. 将此文件放入 api/request.js
 * 2. Mock 模式：IS_MOCK = true，配合 mock/mock-server.js 使用
 *    - 不发起真实网络请求，由本地 Mock 拦截器返回数据
 *    - 小程序不支持 MSW（Service Worker），采用请求层拦截方案
 * 3. 正式模式：IS_MOCK = false，填入真实 baseURL
 */

const config = {
  // ============ 切换点 ============
  IS_MOCK: true,                    // 切换为 false 即连接真实后端
  baseURL: '',                      // Mock 模式留空
  // baseURL: 'https://api.example.com',  // 正式模式填真实地址
  // ================================
  timeout: 10000,
}

// Mock 拦截器（仅在 IS_MOCK=true 时使用）
let mockServer = null
if (config.IS_MOCK) {
  mockServer = require('../mock/mock-server')
}

// 获取 Token（根据项目实际情况调整）
function getToken() {
  return wx.getStorageSync('token') || ''
}

function buildGetUrl(url, data = {}) {
  const entries = Object.entries(data).filter(([, value]) => value !== undefined && value !== null)
  if (!entries.length) return url
  const query = entries
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&')
  const connector = url.includes('?') ? '&' : '?'
  return `${url}${connector}${query}`
}

/**
 * 统一请求方法
 * @param {Object} options - 请求配置
 * @param {string} options.url - 接口路径（如 /api/resources）
 * @param {string} [options.method='GET'] - 请求方法
 * @param {Object} [options.data] - 请求参数
 * @param {Object} [options.header] - 额外 header
 * @returns {Promise}
 */
function request(options) {
  const method = (options.method || 'GET').toUpperCase()
  const rawData = options.data || {}
  const requestUrl = method === 'GET' ? buildGetUrl(options.url, rawData) : options.url
  const requestData = method === 'GET' ? {} : rawData

  // ============ Mock 模式：本地拦截 ============
  if (config.IS_MOCK && mockServer) {
    return mockServer.mockRequest({
      url: requestUrl,
      method,
      data: requestData,
    })
  }

  // ============ 正式模式：真实请求 ============
  return new Promise((resolve, reject) => {
    const header = {
      'Content-Type': 'application/json',
      ...options.header,
    }

    // 添加鉴权 Token
    const token = getToken()
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: config.baseURL + requestUrl,
      method,
      data: requestData,
      header,
      timeout: config.timeout,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // 未登录，跳转登录页
          wx.showToast({ title: '请先登录', icon: 'none' })
          reject(res.data)
        } else {
          wx.showToast({ title: res.data.message || '请求失败', icon: 'none' })
          reject(res.data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络连接失败', icon: 'none' })
        reject(err)
      }
    })
  })
}

// 便捷方法
request.get = (url, data) => request({ url, method: 'GET', data })
request.post = (url, data) => request({ url, method: 'POST', data })
request.put = (url, data) => request({ url, method: 'PUT', data })
request.delete = (url, data) => request({ url, method: 'DELETE', data })

module.exports = request
