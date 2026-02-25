/**
 * React/Vue - Axios 统一请求封装（含 Mock 切换）
 *
 * 使用说明：
 * 1. 将此文件放入 src/api/request.js
 * 2. Mock 模式：VITE_API_MODE=mock（.env.development）
 * 3. 正式模式：VITE_API_MODE=real + 填入 VITE_API_BASE_URL
 * 4. 需安装：npm install axios
 */

import axios from 'axios'

// ============ 环境变量切换 ============
// .env.development:  VITE_API_MODE=mock
// .env.production:   VITE_API_MODE=real
// .env.development:  VITE_API_BASE_URL=
// .env.production:   VITE_API_BASE_URL=https://api.example.com
const IS_MOCK = import.meta.env.VITE_API_MODE === 'mock'
const BASE_URL = IS_MOCK ? '' : (import.meta.env.VITE_API_BASE_URL || '')
// =====================================

const instance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：添加 Token
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
instance.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code === 200) {
      return data
    }
    // 业务错误
    console.error(`[API Error] ${data.message}`)
    return Promise.reject(data)
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        // 未登录，跳转登录页
        console.warn('未登录，请先登录')
        // router.push('/login')
      }
      return Promise.reject(data)
    }
    // 网络错误
    console.error('网络连接失败')
    return Promise.reject(error)
  }
)

export default instance
