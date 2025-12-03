<!-- src/views/AdminUsers.vue -->
<template>
  <header>
    <nav>
      <div class="nav">
        <a href="/home">返回用户主页</a>
        <a href="/admin/detections">管理检测记录</a>
        <a href="/admin/users">刷新用户列表</a>
      </div>
    </nav>
  </header>

  <div class="admin-page">
    <!-- =================== 添加新用户模块 =================== -->
    <div class="add-user-form">
      <h3>添加新用户/管理员</h3>
      <form @submit.prevent="addUser">
        <input v-model="newUser.username" type="text" placeholder="用户名" required />
        <input v-model="newUser.password" type="password" placeholder="密码" required />
        <select v-model="newUser.role" required>
          <option value="user">普通用户</option>
          <option value="admin">管理员</option>
        </select>
        <button type="submit">创建用户</button>
      </form>
    </div>

    <!-- =================== 用户列表模块 =================== -->
    <h2>用户管理</h2>
    <table class="data-table" v-if="users.length">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户名</th>
          <th>角色</th>
          <th>注册时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>
            <span :class="['role-tag', user.role]">{{ user.role === 'admin' ? '管理员' : '普通用户' }}</span>
          </td>
          <td>{{ formatBeijingTime(user.created_at) }}</td>
          <td>
            <button class="btn-reset" @click="resetPassword(user.id, user.username)">重置密码</button>
            <button class="btn-delete" @click="deleteUser(user.id, user.username)">删除用户</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>正在加载用户数据...</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '../api/axios'; // 确保你使用了封装的axios实例
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

dayjs.extend(utc);
dayjs.extend(timezone);

const backendUrl = "http://127.0.0.1:5000"; // 你的后端地址
const users = ref([]);
const newUser = ref({
  username: '',
  password: '',
  role: 'user' // 默认创建普通用户
});

// 时间格式化函数 (与AdminDetections.vue中的一样)
const formatBeijingTime = (gmtDate) => {
  if (!gmtDate) return 'N/A';
  return dayjs(gmtDate).tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
};

// ========== 1. 获取所有用户数据 ==========
const fetchUsers = async () => {
  const token = localStorage.getItem("token");
  try {
    const res = await axios.get(`${backendUrl}/api/admin/users`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    users.value = res.data;
  } catch (err) {
    alert('加载用户列表失败: ' + (err.response?.data?.msg || err.message));
  }
};

// 组件挂载时自动加载用户
onMounted(fetchUsers);

// ========== 2. 添加新用户 ==========
const addUser = async () => {
  if (!newUser.value.username || !newUser.value.password) {
    alert('用户名和密码不能为空！');
    return;
  }
  const token = localStorage.getItem("token");
  try {
    const res = await axios.post(`${backendUrl}/api/admin/users`, newUser.value, {
      headers: { Authorization: `Bearer ${token}` }
    });
    alert('用户创建成功！');
    // 清空表单
    newUser.value.username = '';
    newUser.value.password = '';
    newUser.value.role = 'user';
    // 重新加载用户列表以显示新用户
    fetchUsers(); 
  } catch (err) {
    alert('创建用户失败: ' + (err.response?.data?.msg || err.message));
  }
};

// ========== 3. 重置密码 ==========
const resetPassword = async (userId, username) => {
  const newPassword = prompt(`请输入为用户 "${username}" 设置的新密码:`);
  if (!newPassword) {
    alert('操作已取消。');
    return;
  }
  
  const token = localStorage.getItem("token");
  try {
    const res = await axios.put(`${backendUrl}/api/admin/users/${userId}/reset-password`, 
      { password: newPassword }, 
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
    alert(res.data.msg || '密码重置成功！');
  } catch (err) {
    alert('重置密码失败: ' + (err.response?.data?.msg || err.message));
  }
};

// ========== 4. 删除用户 ==========
const deleteUser = async (userId, username) => {
  if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复！`)) {
    return;
  }
  
  const token = localStorage.getItem("token");
  try {
    const res = await axios.delete(`${backendUrl}/api/admin/users/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    alert(res.data.msg || '用户删除成功！');
    // 重新加载用户列表
    fetchUsers();
  } catch (err) {
    alert('删除用户失败: ' + (err.response?.data?.msg || err.message));
  }
};
</script>

<style scoped>
/* 使用和 AdminDetections.vue 类似的样式 */
.admin-page {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.add-user-form {
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
  border: 1px solid #e0e0e0;
}

.add-user-form h3 {
  margin-top: 0;
}

.add-user-form form {
  display: flex;
  gap: 15px;
  align-items: center;
}

.add-user-form input,
.add-user-form select {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.add-user-form button {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
}
.add-user-form button:hover {
  background-color: #218838;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th, .data-table td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
}
.data-table th {
  background-color: #f2f2f2;
}

.role-tag {
  padding: 3px 8px;
  border-radius: 12px;
  color: white;
  font-size: 0.8em;
}
.role-tag.admin {
  background-color: #dc3545;
}
.role-tag.user {
  background-color: #007bff;
}

.btn-reset, .btn-delete {
  padding: 5px 10px;
  border-radius: 4px;
  border: none;
  color: white;
  cursor: pointer;
  margin-right: 5px;
}
.btn-reset {
  background-color: #ffc107;
}
.btn-delete {
  background-color: #dc3545;
}
</style>
