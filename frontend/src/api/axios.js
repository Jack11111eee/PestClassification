// frontend/src/api/axios.js

import axios from 'axios'

const instance = axios.create({
  // === 关键修改 #3：使用相对路径代理 ===
  // 旧的错误代码: baseURL: 'http://127.0.0.1:5000/api/',
  // 新的正确代码:
  baseURL: '/api',
  
  timeout: 5000
})

// 请求拦截器 (这部分代码很好，保持不变)
instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

export default instance
