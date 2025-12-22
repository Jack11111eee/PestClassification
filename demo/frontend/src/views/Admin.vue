<template>
  <div class="container">
    <h2>用户管理</h2>

    <!-- 创建用户 -->
    <div class="create-box">
      <input v-model="newUser.username" placeholder="用户名" />
      <input v-model="newUser.password" type="password" placeholder="密码" />
      <select v-model="newUser.role">
        <option value="user">user</option>
        <option value="operator">operator</option>
        <option value="admin">admin</option>
      </select>
      <button @click="submitCreateUser">创建用户</button>
    </div>

    <!-- 用户列表 -->
    <table border="1" cellspacing="0">
      <thead>
        <tr>
          <th>序号</th>
          <th>用户名</th>
          <th>角色</th>
          <th>操作</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(user, index) in users" :key="user.id">
          <td>{{ index + 1 }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.role }}</td>
          <td>
            <button @click="resetPwd(user.id)">重置密码</button>
            <button class="danger" @click="removeUser(user.id)">
              注销
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import {
  getUsers,
  createUser,
  resetUserPassword,
  deleteUser
} from '@/api/admin'

export default {
  name: 'UserManage',

  data() {
    return {
      users: [],
      newUser: {
        username: '',
        password: '',
        role: 'user'
      }
    }
  },

  mounted() {
    this.loadUsers()
  },

  methods: {
    // 获取用户列表
    async loadUsers() {
      const res = await getUsers()
      this.users = res.data
    },

    // 创建用户（注意：不和 API 同名）
    async submitCreateUser() {
      if (!this.newUser.username || !this.newUser.password) {
        alert('请输入用户名和密码')
        return
      }

      await createUser(this.newUser)
      alert('创建成功')

      this.newUser.username = ''
      this.newUser.password = ''
      this.newUser.role = 'user'

      this.loadUsers()
    },

    // 重置密码
    async resetPwd(id) {
      const pwd = prompt('输入新密码')
      if (!pwd) return

      await resetUserPassword(id, pwd)
      alert('密码已重置')
    },

    // 删除用户
    async removeUser(id) {
      if (!confirm('确定要注销该用户吗？该操作不可恢复！')) return

      await deleteUser(id)
      alert('用户已删除')
      this.loadUsers()
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20px;
}

.create-box {
  margin-bottom: 20px;
}

.create-box input,
.create-box select {
  margin-right: 8px;
}

table {
  width: 100%;
}

th,
td {
  padding: 8px;
  text-align: center;
}

.danger {
  margin-left: 8px;
  background-color: #e74c3c;
  color: white;
}
</style>

