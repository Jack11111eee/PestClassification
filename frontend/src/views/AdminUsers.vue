<template>
  <div class="user-management">

    <!-- ====================== 导航栏 ====================== -->
    <header>
      <nav>
        <div class="nav-left">
          <router-link to="/home">主页</router-link>
          <router-link to="/my-submissions">我的提交</router-link>

          <!-- 管理员可见的菜单 -->
          <router-link v-if="user?.role === 'admin'" to="/admin/detections">管理检测记录</router-link>
          <router-link v-if="user?.role === 'admin'" to="/admin/users">用户管理</router-link>
        </div>

        <div class="nav-right">
          <p>当前用户：{{ user?.username || "未登录" }}</p>
          <button @click="logout">退出登录</button>
        </div>
      </nav>
    </header>
    <!-- ====================== 导航栏结束 ====================== -->

    
    <!-- 内容区域 -->
    <div class="content">
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
              <button @click="handleResetPassword(user)" class="action-btn reset-btn">
                重置密码
              </button>

              <button @click="handleDeleteUser(user)" class="action-btn delete-btn">
                注销
              </button>
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

  </div>
</template>

<script>
import axios from "axios";
import { useRouter } from "vue-router";
import { jwtDecode } from "jwt-decode";


export default {
  name: "AdminUsers",

  data() {
    return {
      user: null,
      users: [],
      isModalOpen: false,
      newUser: {
        username: "",
        password: "",
        role: "user",
      }
    };
  },

  created() {
    this.checkLogin();
    this.fetchUsers();
  },

  methods: {
    // ================================
    // 检查登录并获取用户信息
    // ================================
    checkLogin() {
      const token = localStorage.getItem("token");
      const router = useRouter();

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const decoded = jwtDecode(token);
        const expired = decoded.exp < Date.now() / 1000;

        if (expired) {
          this.logout();
          return;
        }

        this.user = {
          id: decoded.sub,
          username: decoded.username,
          role: decoded.role,
        };
      } catch (e) {
        console.error("Token 解码失败", e);
        this.logout();
      }
    },

    logout() {
      localStorage.removeItem("token");
      this.$router.push("/login");
    },

    getAuthHeaders() {
      const token = localStorage.getItem("token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    },

    // ================================
    // 加载用户列表
    // ================================
    async fetchUsers() {
      try {
        const response = await axios.get("/api/admin/users", {
          headers: this.getAuthHeaders(),
        });
        this.users = response.data;
      } catch (error) {
        console.error("获取用户列表失败:", error);
        alert("获取用户列表失败");
      }
    },

    // ================================
    // 添加用户
    // ================================
    openAddUserModal() {
      this.newUser = { username: "", password: "", role: "user" };
      this.isModalOpen = true;
    },

    closeAddUserModal() {
      this.isModalOpen = false;
    },

    async handleAddNewUser() {
      try {
        const response = await axios.post("/api/admin/users", this.newUser, {
          headers: this.getAuthHeaders(),
        });
        this.users.unshift(response.data);
        alert(`用户 "${response.data.username}" 添加成功！`);
        this.closeAddUserModal();
      } catch (error) {
        console.error("添加用户失败:", error);
        alert("添加用户失败");
      }
    },

    // ================================
    // 重置密码
    // ================================
    async handleResetPassword(user) {
      if (!confirm(`确认重置用户 "${user.username}" 的密码？`)) return;

      try {
        const response = await axios.post(
          `/api/admin/users/${user.id}/reset-password`,
          null,
          { headers: this.getAuthHeaders() }
        );

        alert(`新密码：${response.data.new_password}`);
      } catch (error) {
        console.error("重置密码失败:", error);
        alert("重置密码失败");
      }
    },

    // ================================
    // 删除用户
    // ================================
    async handleDeleteUser(user) {
      if (!confirm(`确认注销用户 "${user.username}"？`)) return;

      try {
        await axios.delete(`/api/admin/users/${user.id}`, {
          headers: this.getAuthHeaders(),
        });
        this.users = this.users.filter((u) => u.id !== user.id);
        alert(`用户 "${user.username}" 已被删除`);
      } catch (error) {
        console.error("删除用户失败:", error);
        alert("删除用户失败");
      }
    },

    formatDateTime(t) {
      return new Date(t).toLocaleString();
    },
  },
};
</script>

<style scoped>
  /* ========== 导航栏样式（从 home 复制） ========== */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #42b983;
  padding: 14px 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  z-index: 1000;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 28px;
}

.nav-left {
  display: flex;
  gap: 24px;
}

.nav-left a,
.nav-left .router-link-active {
  color: white;
  text-decoration: none;
  font-weight: 600;
  font-size: 17px;
  padding: 6px 10px;
  border-radius: 6px;
  transition: 0.2s;
}

.nav-left a:hover,
.nav-left .router-link-active:hover {
  background-color: rgba(255,255,255,0.18);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
}

.nav-right button {
  background-color: white;
  color: #42b983;
  border: none;
  padding: 0.45rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: 0.2s;
}

.nav-right button:hover {
  background-color: #e8f8f0;
}

.content {
  margin-top: 110px; /* 预留导航栏高度 */
}

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

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: 6px;
}

/* 黄色：重置密码 */
.reset-btn {
  background-color: #f0ad4e;
}
.reset-btn:hover {
  background-color: #ec971f;
  transform: translateY(-1px);
}

/* 红色：注销 */
.delete-btn {
  background-color: #d9534f;
}
.delete-btn:hover {
  background-color: #c9302c;
  transform: translateY(-1px);
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
