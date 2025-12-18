import axios from 'axios'

const api = axios.create({
  baseURL: 'http://10.61.190.21:8080'
})

export function checkImage(file) {
  const formData = new FormData()
  formData.append('image', file)

  return api.post('/api/ai/check', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
