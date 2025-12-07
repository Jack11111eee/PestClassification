<template>
  <div class="user-management">
    <h1>用户管理</h1>

    <!-- 添加用户按钮 -->
    <div class="actions">
      <button @click="openAddUserModal">添加新用户</button>
    </div>

    <!-- 用户列表表格 -->
    <table class="user-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户名 (Username)</th>
          <th>角色 (Role)</th>
          <th>创建时间 (Create At)</th>
          <th>操作 (Actions)</th>
        </tr>
      </thead>
      <tbody v-if="users.length > 0">
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>
            <span :class="['role-tag', user.role]">{{ user.role }}</span>
          </td>
          <td>{{ formatDateTime(user.create_at) }}</td>
          <td>
            <button @click="handleResetPassword(user)" class="reset-btn">重置密码</button>
          </td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr>
          <td colspan="5" class="no-data">正在加载或暂无数据...</td>
        </tr>
      </tbody>
    </table>

    <!-- 添加用户弹窗 -->
    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeAddUserModal">
      <div class="modal-content">
        <h2>添加新用户</h2>
        <form @submit.prevent="handleAddNewUser">
          <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" v-model="newUser.username" required>
          </div>
          <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" v-model="newUser.password" required>
          </div>
          <div class="form-group">
            <label for="role">角色</label>
            <select id="role" v-model="newUser.role">
              <option value="user">普通用户 (user)</option>
              <option value="admin">管理员 (admin)</option>
            </select>
          </div>
          <div class="form-actions">
            <button type="button" @click="closeAddUserModal">取消</button>
            <button type="submit">确认添加</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
// --- 变化点 1: 直接导入 axios ---
import axios from 'axios';

export default {
  name: 'AdminUsers',
  data() {
    return {
      users: [],
      isModalOpen: false,
      newUser: {
        username: '',
        password: '',
        role: 'user',
      },
    };
  },
  methods: {
    // --- 变化点 2: 封装获取认证头的方法，方便复用 ---
    getAuthHeaders() {
      const token = localStorage.getItem('token');
      // 如果有 token，返回包含 Authorization 的 header 对象，否则返回空对象
      return token ? { Authorization: `Bearer ${token}` } : {};
    },

    // --- 变化点 3: fetchUsers 直接使用 axios ---
    async fetchUsers() {
      try {
        const response = await axios.get('/api/admin/users', {
          headers: this.getAuthHeaders()
        });
        this.users = response.data;
      } catch (error) {
        console.error("获取用户列表失败:", error);
        alert('获取用户列表失败: ' + (error.response?.data?.message || error.message));
      }
    },
    
    openAddUserModal() {
      this.newUser = { username: '', password: '', role: 'user' };
      this.isModalOpen = true;
    },

    closeAddUserModal() {
      this.isModalOpen = false;
    },

    // --- 变化点 4: handleAddNewUser 直接使用 axios ---
    async handleAddNewUser() {
      try {
        const response = await axios.post('/api/admin/users', this.newUser, {
          headers: this.getAuthHeaders()
        });
        this.users.unshift(response.data);
        alert(`用户 "${response.data.username}" 添加成功!`);
        this.closeAddUserModal();
      } catch (error) {
        console.error("添加用户失败:", error);
        alert('添加用户失败: ' + (error.response?.data?.message || error.message));
      }
    },

    // --- 变化点 5: handleResetPassword 直接使用 axios ---
    async handleResetPassword(user) {
      if (!confirm(`确定要重置用户 "${user.username}" 的密码吗？`)) {
        return;
      }
      try {
        // 对于 POST 请求，如果不需要发送数据体，第二个参数可以是 null 或 {}
        const response = await axios.post(`/api/admin/users/${user.id}/reset-password`, null, {
          headers: this.getAuthHeaders()
        });
        alert(
          `密码重置成功！\n\n` +
          `用户: ${user.username}\n` +
          `新密码: ${response.data.new_password}\n\n` +
          `请妥善告知用户。`
        );
      } catch (error) {
        console.error("重置密码失败:", error);
        alert('重置密码失败: ' + (error.response?.data?.message || error.message));
      }
    },

    formatDateTime(dateTimeString) {
      if (!dateTimeString) return 'N/A';
      const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' };
      return new Date(dateTimeString).toLocaleString('zh-CN', options);
    }
  },
  created() {
    this.fetchUsers();
  }
};
</script>

<style scoped>
/* 样式部分和之前完全一样，这里省略以保持简洁，你可以直接使用之前的样式代码 */
.user-management {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 1rem;
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
}

.actions {
  margin-bottom: 1rem;
  text-align: right;
}

.actions button {
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.user-table th, .user-table td {
  border: 1px solid #ddd;
  padding: 0.75rem;
  text-align: left;
}

.user-table th {
  background-color: #f8f9fa;
}

.no-data {
  text-align: center;
  color: #888;
  padding: 2rem;
}

.role-tag {
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  color: white;
  font-size: 0.8em;
}

.role-tag.admin {
  background-color: #dc3545; /* 红色 */
}

.role-tag.user {
  background-color: #28a745; /* 绿色 */
}

.reset-btn {
  padding: 0.3rem 0.6rem;
  background-color: #ffc107;
  color: #212529;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 400px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.modal-content h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
}

.form-group input, .form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.form-actions button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #ccc;
}

.form-actions button[type="submit"] {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}
</style>
