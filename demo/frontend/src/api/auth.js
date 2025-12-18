import api from './request'

// 注册
export function register(username, password) {
  return api.post('/api/auth/register', {
    username,
    password
  })
}

// 登录
export function login(username, password) {
  return api.post('/api/auth/login', {
    username,
    password
  })
}
