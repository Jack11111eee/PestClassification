这是一个基于你现有逻辑的重构版本。我没有引入 Element UI 或 Ant Design 等外部库，而是使用 **原生 CSS** 写了一套简洁、现代、扁平化（Flat Design）的样式。

**主要改进点：**

1. **卡片式布局**：将功能区（导航、表单、表格）封装在白底圆角的卡片中，更有层次感。
2. **现代配色**：使用经典的“主色蓝”配合柔和的灰色背景，视觉舒适。
3. **交互优化**：按钮添加了悬停（Hover）和点击效果；输入框添加了聚焦（Focus）光标颜色。
4. **表格美化**：去掉了老式的 `border="1"`，改为线条分割，增加了隔行变色和悬停高亮。

你可以直接复制替换你的整个 `.vue` 文件：

```html
<template>
  <div class="app-container">
    <header class="nav-bar card">
      <div class="nav-links">
        <div class="logo">系统后台</div>
        <button
          v-if="user"
          @click="$router.push('/test')"
          class="nav-btn"
        >
          识别系统
        </button>

        <button
          v-if="user && user.role === 'admin'"
          @click="$router.push('/user_manage')"
          class="nav-btn active"
        >
          用户管理
        </button>

        <button
          v-if="user && (user.role === 'admin' || user.role === 'operator')"
          @click="$router.push('/audit')"
          class="nav-btn"
        >
          审核模块
        </button>

        <button
          v-if="user"
          @click="$router.push('/my_submission')"
          class="nav-btn"
        >
          我的记录
        </button>
      </div>

      <div v-if="user" class="user-info">
        <span class="welcome-text">Hi, {{ user.username }}</span>
        <button class="btn btn-outline-danger btn-sm" @click="logout">退出</button>
      </div>
    </header>

    <div class="main-content">
      <div class="page-header">
        <h2>用户管理</h2>
        <p class="subtitle">管理系统内的用户权限与账号状态</p>
      </div>

      <div class="card create-section">
        <h3 class="card-title">添加新用户</h3>
        <div class="form-row">
          <input 
            v-model="newUser.username" 
            class="input-field" 
            placeholder="请输入用户名" 
          />
          <input
            v-model="newUser.password"
            type="password"
            class="input-field"
            placeholder="设置初始密码"
          />
          <select v-model="newUser.role" class="select-field">
            <option value="user">普通用户 (User)</option>
            <option value="operator">审核员 (Operator)</option>
            <option value="admin">管理员 (Admin)</option>
          </select>
          <button class="btn btn-primary" @click="submitCreateUser">
            <span class="icon">+</span> 创建用户
          </button>
        </div>
      </div>

      <div class="card table-section">
        <h3 class="card-title">用户列表</h3>
        <div class="table-wrapper">
          <table class="styled-table">
            <thead>
              <tr>
                <th width="80">序号</th>
                <th>用户名</th>
                <th>角色</th>
                <th width="200">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(u, index) in users" :key="u.id">
                <td>{{ index + 1 }}</td>
                <td class="font-bold">{{ u.username }}</td>
                <td>
                  <span :class="['role-badge', u.role]">{{ u.role }}</span>
                </td>
                <td>
                  <button class="btn btn-text" @click="resetPwd(u.id)">重置密码</button>
                  <button class="btn btn-text-danger" @click="removeUser(u.id)">注销</button>
                </td>
              </tr>
              <tr v-if="users.length === 0">
                <td colspan="4" class="empty-text">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
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
      user: null, 
      users: [],
      newUser: {
        username: '',
        password: '',
        role: 'user'
      }
    }
  },

  mounted() {
    const u = localStorage.getItem('user')
    if (u) {
      this.user = JSON.parse(u)
    }
    this.loadUsers()
  },

  methods: {
    // 模拟 logout 方法，防止报错 (如果你有 mixin 或全局方法可删除此占位)
    logout() {
      localStorage.removeItem('user')
      this.user = null
      this.$router.push('/login') // 假设有个 login 路由
    },

    async loadUsers() {
      try {
        const res = await getUsers()
        this.users = res.data
      } catch (e) {
        console.error('获取用户失败', e)
      }
    },

    async submitCreateUser() {
      if (!this.newUser.username || !this.newUser.password) {
        alert('请输入用户名和密码')
        return
      }
      try {
        await createUser(this.newUser)
        // alert('创建成功') // 建议用 toast 替代 alert，这里保持简洁
        this.newUser.username = ''
        this.newUser.password = ''
        this.newUser.role = 'user'
        this.loadUsers()
      } catch (e) {
        alert('创建失败')
      }
    },

    async resetPwd(id) {
      const pwd = prompt('请输入新密码')
      if (!pwd) return
      try {
        await resetUserPassword(id, pwd)
        alert('密码已重置')
      } catch (e) {
        alert('操作失败')
      }
    },

    async removeUser(id) {
      if (!confirm('确定要注销该用户吗？该操作不可恢复！')) return
      try {
        await deleteUser(id)
        this.loadUsers()
      } catch (e) {
        alert('删除失败')
      }
    }
  }
}
</script>

<style scoped>
/* ================= 全局变量与布局 ================= */
:root {
  --primary-color: #409eff;
  --primary-hover: #66b1ff;
  --danger-color: #f56c6c;
  --text-main: #303133;
  --text-regular: #606266;
  --border-color: #dcdfe6;
  --bg-color: #f5f7fa;
}

.app-container {
  min-height: 100vh;
  background-color: #f5f7fa; /* 浅灰背景 */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #333;
}

.main-content {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 20px;
}

/* ================= 卡片通用样式 ================= */
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 20px;
  margin-bottom: 20px;
}

.card-title {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}

/* ================= 导航栏 ================= */
.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  border-radius: 0; /* 顶部导航直角 */
  margin-bottom: 30px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo {
  font-weight: bold;
  font-size: 18px;
  color: #409eff;
  margin-right: 20px;
}

.nav-btn {
  background: none;
  border: none;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  padding: 8px 0;
  position: relative;
  transition: color 0.3s;
}

.nav-btn:hover, .nav-btn.active {
  color: #409eff;
  font-weight: 500;
}

.nav-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #409eff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.welcome-text {
  font-size: 14px;
  color: #606266;
}

/* ================= 标题区 ================= */
.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}
.page-header .subtitle {
  margin: 8px 0 20px;
  color: #909399;
  font-size: 13px;
}

/* ================= 表单区域 ================= */
.create-section {
  background-color: #fff;
}

.form-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.input-field, .select-field {
  padding: 10px 15px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  outline: none;
  font-size: 14px;
  transition: border-color 0.2s;
  flex: 1;
  min-width: 150px;
}

.select-field {
  background-color: white;
  cursor: pointer;
}

.input-field:focus, .select-field:focus {
  border-color: #409eff;
}

/* ================= 按钮样式 ================= */
.btn {
  padding: 9px 20px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
  outline: none;
}

.btn-sm {
  padding: 5px 12px;
  font-size: 12px;
}

/* Primary Button */
.btn-primary {
  background-color: #409eff;
  color: white;
}
.btn-primary:hover {
  background-color: #66b1ff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* Outline Danger */
.btn-outline-danger {
  background: white;
  border: 1px solid #f56c6c;
  color: #f56c6c;
}
.btn-outline-danger:hover {
  background: #fef0f0;
}

/* Text Buttons inside table */
.btn-text {
  background: none;
  color: #409eff;
  padding: 4px 8px;
}
.btn-text:hover {
  text-decoration: underline;
}

.btn-text-danger {
  background: none;
  color: #f56c6c;
  padding: 4px 8px;
}
.btn-text-danger:hover {
  text-decoration: underline;
}

/* ================= 表格样式 ================= */
.table-wrapper {
  overflow-x: auto;
}

.styled-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.styled-table th {
  background-color: #f5f7fa;
  color: #909399;
  font-weight: 600;
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.styled-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  color: #606266;
  vertical-align: middle;
}

.styled-table tr:hover {
  background-color: #f9fafc;
}

/* 角色标签 */
.role-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background-color: #ecf5ff;
  color: #409eff;
}
.role-badge.operator {
  background-color: #fdf6ec;
  color: #e6a23c;
}
.role-badge.user {
  background-color: #f4f4f5;
  color: #909399;
}

.font-bold {
  font-weight: 500;
  color: #303133;
}
.empty-text {
  text-align: center;
  padding: 30px;
  color: #909399;
}
</style>

```