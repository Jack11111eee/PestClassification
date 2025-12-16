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

<script setup>
  import { ref, reactive, onMounted } from "vue";
  import { useRouter } from "vue-router";
  import { jwtDecode } from "jwt-decode";
  import dayjs from "dayjs"; // 推荐使用 dayjs 来格式化时间，更专业
  
  import request from "../api/axios";
  
  // --- 响应式状态定义 ---
  const user = ref(null); // 当前登录的用户信息
  const users = ref([]); // 用户列表
  const isModalOpen = ref(false); // 控制添加用户模态框的显示
  const newUser = reactive({ // 使用 reactive 来处理对象，更方便
    username: "",
    password: "",
    role: "user",
  });
  const isLoading = ref(true); // 加载状态
  const router = useRouter(); // 获取 router 实例
  
  // --- 生命周期函数 ---
  onMounted(() => {
    // checkLogin(); // 检查登录状态的逻辑通常在路由守卫中做，这里暂时保留
    fetchUsers(); // 组件挂载后，获取用户列表
  });
  
  // --- 方法定义 ---
  
  // 2. 【重要】不再需要 getAuthHeaders，request 拦截器会自动处理
  
  // ================================
  // 加载用户列表
  // ================================
  async function fetchUsers() {
    isLoading.value = true;
    try {
      // 【修改】使用 request 实例，并移除 headers
      const response = await request.get("/admin/users");
      console.log("【用户管理】成功获取用户列表:", response.data);
      users.value = response.data || [];
    } catch (error) {
      console.error("获取用户列表失败:", error);
      alert(error.response?.data?.msg || "获取用户列表失败");
    } finally {
      isLoading.value = false;
    }
  }
  
  // ================================
  // 添加用户
  // ================================
  function openAddUserModal() {
    // 重置 newUser 对象
    Object.assign(newUser, { username: "", password: "", role: "user" });
    isModalOpen.value = true;
  }
  
  function closeAddUserModal() {
    isModalOpen.value = false;
  }
  
  async function handleAddNewUser() {
    if (!newUser.username || !newUser.password) {
      alert("用户名和密码不能为空！");
      return;
    }
    try {
      // 【修改】使用 request 实例，并移除 headers
      const response = await request.post("/admin/users", newUser);
      // 【修改】所有 this.xxx 都变成了 xxx.value
      users.value.unshift(response.data);
      alert(`用户 "${response.data.username}" 添加成功！`);
      closeAddUserModal();
    } catch (error) {
      console.error("添加用户失败:", error);
      alert(error.response?.data?.msg || "添加用户失败");
    }
  }
  
  // ================================
  // 重置密码
  // ================================
  async function handleResetPassword(userToReset) {
    if (!confirm(`确认重置用户 "${userToReset.username}" 的密码？`)) return;
  
    try {
      // 【修改】使用 request 实例，并移除 headers
      const response = await request.post(
        `/admin/users/${userToReset.id}/reset-password`
      );
  
      // 把新密码复制到剪贴板，方便管理员使用
      navigator.clipboard.writeText(response.data.new_password);
      alert(`用户 "${userToReset.username}" 的新密码已重置并复制到剪贴板！\n新密码：${response.data.new_password}`);
  
    } catch (error) {
      console.error("重置密码失败:", error);
      alert(error.response?.data?.msg || "重置密码失败");
    }
  }
  
  // ================================
  // 删除用户
  // ================================
  async function handleDeleteUser(userToDelete) {
    if (!confirm(`确认注销用户 "${userToDelete.username}"？`)) return;
  
    try {
      // 【修改】使用 request 实例，并移除 headers
      await request.delete(`/api/admin/users/${userToDelete.id}`);
      users.value = users.value.filter((u) => u.id !== userToDelete.id);
      alert(`用户 "${userToDelete.username}" 已被删除`);
    } catch (error) {
      console.error("删除用户失败:", error);
      alert(error.response?.data?.msg || "删除用户失败");
    }
  }
  
  // ================================
  // 工具函数 - 格式化时间
  // ================================
  function formatDateTime(t) {
    if (!t) return "N/A";
    return dayjs(t).format("YYYY-MM-DD HH:mm:ss");
  }
  
  // 登录检查和登出的逻辑可以保留，但通常这些全局逻辑会放在路由守卫或 Pinia store 中
  function checkLogin() {
  // 1. 从 localStorage 获取 token
  const token = localStorage.getItem("token");
  // 2. 如果没有 token，直接跳转到登录页
  if (!token) {
    alert("您尚未登录，请先登录！");
    router.push("/login");
    return false; // 返回 false 表示校验未通过
  }
  try {
    // 3. 解码 token
    const decoded = jwtDecode(token);
    // 4. 检查 token 是否过期
    // decoded.exp 是秒级时间戳，Date.now() 是毫秒，所以要除以 1000
    const isExpired = decoded.exp < Date.now() / 1000;
    if (isExpired) {
      alert("登录已过期，请重新登录！");
      logout(); // 调用登出函数，清空 token 并跳转
      return false; // 返回 false 表示校验未通过
    }
    // 5. 校验通过，将解码后的用户信息存入 ref
    user.value = {
      id: decoded.sub, // 通常 'sub' 代表 user id
      username: decoded.username,
      role: decoded.role,
    };
    
    // 6. 【重要】检查用户角色权限
    if (user.value.role !== 'admin') {
      alert("权限不足，您不是管理员！");
      router.push("/"); // 跳转到主页或其他无权限页面
      return false;
    }
    return true; // 返回 true 表示校验通过
    } catch (e) {
      console.error("Token 解码或校验失败", e);
      alert("无效的登录状态，请重新登录！");
      logout();
      return false; // 返回 false 表示校验未通过
    }
  }
  function logout() {
      localStorage.removeItem("token");
      router.push("/login"); // this.$router 变成了 router
  }
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
