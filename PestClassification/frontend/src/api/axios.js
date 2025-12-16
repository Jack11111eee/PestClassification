import axios from 'axios'

const instance = axios.create({
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
