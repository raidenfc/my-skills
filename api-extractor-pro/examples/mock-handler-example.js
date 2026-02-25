/**
 * MSW Handler 示例文件
 * 展示 api-extractor-pro 生成的标准 Mock handler 格式
 *
 * 技术栈：MSW v2.x
 * 特性：参数校验、延迟模拟、Token 校验、分页逻辑
 */

import { http, HttpResponse, delay } from 'msw'
import userData from '../data/user.json'

// =====================================================
// 用户模块 MSW Handlers
// =====================================================
export const userHandlers = [

  /**
   * POST /api/user/login — 用户登录
   * 无需 Token，参数校验
   */
  http.post('/api/user/login', async ({ request }) => {
    // 模拟网络延迟
    await delay(300)

    const body = await request.json()
    const { username, password } = body

    // 参数校验
    if (!username || !password) {
      return HttpResponse.json({
        code: 400,
        data: null,
        message: '用户名和密码不能为空',
      }, { status: 400 })
    }

    // 模拟登录验证
    const user = userData.users.find(u => u.username === username)
    if (!user || password !== '123456') {
      return HttpResponse.json({
        code: 401,
        data: null,
        message: '用户名或密码错误',
      }, { status: 401 })
    }

    // 登录成功
    return HttpResponse.json({
      code: 200,
      data: {
        token: `mock-token-${user.id}-${Date.now()}`,
        userInfo: user,
      },
      message: '登录成功',
    })
  }),

  /**
   * GET /api/user/:id — 获取用户信息
   * 需要 Token，路径参数
   */
  http.get('/api/user/:id', ({ params, request }) => {
    // Token 校验
    const authHeader = request.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json({
        code: 401,
        data: null,
        message: 'Token 无效或已过期，请重新登录',
      }, { status: 401 })
    }

    // 路径参数处理
    const id = parseInt(params.id)
    const user = userData.users.find(u => u.id === id)

    if (!user) {
      return HttpResponse.json({
        code: 404,
        data: null,
        message: '用户不存在',
      }, { status: 404 })
    }

    return HttpResponse.json({
      code: 200,
      data: user,
      message: 'success',
    })
  }),

  /**
   * GET /api/user/list — 用户列表（分页）
   * 需要 Token，分页逻辑
   */
  http.get('/api/user/list', ({ request }) => {
    // 分页参数
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') || '1')
    const pageSize = parseInt(url.searchParams.get('pageSize') || '10')

    // 分页计算
    const start = (page - 1) * pageSize
    const list = userData.users.slice(start, start + pageSize)

    return HttpResponse.json({
      code: 200,
      data: {
        list,
        total: userData.users.length,
        page,
        pageSize,
      },
      message: 'success',
    })
  }),

  /**
   * PUT /api/user/:id — 更新用户信息
   * 需要 Token，路径参数 + 请求体
   */
  http.put('/api/user/:id', async ({ params, request }) => {
    await delay(200)

    // Token 校验
    const authHeader = request.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json({
        code: 401,
        data: null,
        message: 'Token 无效或已过期',
      }, { status: 401 })
    }

    const id = parseInt(params.id)
    const body = await request.json()
    const userIndex = userData.users.findIndex(u => u.id === id)

    if (userIndex === -1) {
      return HttpResponse.json({
        code: 404,
        data: null,
        message: '用户不存在',
      }, { status: 404 })
    }

    // 合并更新
    userData.users[userIndex] = { ...userData.users[userIndex], ...body }

    return HttpResponse.json({
      code: 200,
      data: userData.users[userIndex],
      message: '更新成功',
    })
  }),
]
