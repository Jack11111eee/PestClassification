import axios from 'axios'

const api = axios.create({
  baseURL: 'http://10.61.190.21:9000',
  timeout: 5000
})

// 请求拦截器：自动带 token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = 'Bearer ' + token
  }
  return config
})

export default api

