import axios from 'axios'

const api = axios.create({
  baseURL: 'http://10.61.190.21:9000',
  headers: {
    'Content-Type': 'application/json'
  }
})

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
