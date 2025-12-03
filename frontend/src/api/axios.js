// src/api/axios.js

import axios from 'axios'

const instance = axios.create({
  // 错误的老写法：
  // baseURL: 'http://127.0.0.1:5000/api/',
  
  // 正确的新写法：
  // 这样，所有请求都会发往 Vite 开发服务器的 /api 路径下，
  // 然后被 Vite 代理转发到真正的后端地址。
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
})

export default instance
