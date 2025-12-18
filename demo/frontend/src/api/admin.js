import api from './request'

// 获取所有用户
export function getUsers() {
  return api.get('/api/admin/users')
}

// 创建用户
export function createUser(data) {
  return api.post('/api/admin/users', data)
}

// 重置密码
export function resetUserPassword(id, password) {
  return api.put(`/api/admin/users/${id}/password`, {
    password
  })
}

// 删除用户
export function deleteUser(id) {
  return api.delete(`/api/admin/users/${id}`)
}
