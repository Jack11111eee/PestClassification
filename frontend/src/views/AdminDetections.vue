<template>
  <header>
      <nav>
        <div class="nav-left">
          <!-- 为了单页应用体验，将 a href 改为 router-link to -->
          <router-link to="/home">主页</router-link>
          
          <!-- ++ 1. 在这里添加新链接 ++ -->
          <router-link to="/my-submissions">我的提交</router-link>

          <!-- 管理员链接保持不变 -->
          <router-link v-if="user?.role === 'admin'" to="/admin/detections">管理检测记录</router-link>

          <router-link v-if="user?.role === 'admin'" to="/admin/users">用户管理</router-link>
        </div>

        <div class="nav-right">
          <p>当前用户：{{ user?.username || "未登录" }}</p>
          <button @click="logout">退出登录</button>
        </div>
      </nav>
    </header>

  <div class="admin-page">
    <h2>检测记录管理</h2>

    <!-- =================== 筛选按钮 =================== -->
    <div class="filters">
      <button :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</button>
      <button :class="{ active: filter === 'processed' }" @click="filter = 'processed'">已处理</button>
      <button :class="{ active: filter === 'unprocessed' }" @click="filter = 'unprocessed'">未处理</button>
    </div>

    <!-- =================== 数据表格 =================== -->
    <table class="data-table" v-if="filteredRecords.length">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户</th>
          <th>图片</th>
          <th>标签</th>
          <th>置信度</th>
          <th>上传时间</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="r in filteredRecords" :key="r.id">
          <td>{{ r.id }}</td>
          <td>{{ r.username }}</td>

          <td>
            <img :src="backendUrl + r.image_path" class="preview" />
          </td>

          <td>{{ r.label }}</td>

          <td>{{ (r.confidence * 100).toFixed(1) }}%</td>

          <!-- ++ 3. 在模板中调用新创建的格式化函数，而不是直接显示 r.created_at ++ -->
          <td>{{ formatBeijingTime(r.created_at) }}</td>

          <!-- =================== 状态显示 =================== -->
          <td>
            <span v-if="r.is_processed && r.upload_status === 'uploaded'" class="status uploaded">
              已上传
            </span>
            <span v-if="r.is_processed && r.upload_status === 'skipped'" class="status skipped">
              已跳过
            </span>
            <span v-if="!r.is_processed" class="status not">
              未处理
            </span>
          </td>

          <!-- =================== 操作按钮 =================== -->
          <td>
            <button
              class="btn-upload"
              @click="process(r.id, 'upload')"
              :disabled="r.is_processed"
            >
              上传
            </button>

            <button
              class="btn-skip"
              @click="process(r.id, 'skip')"
              :disabled="r.is_processed"
            >
              不上传
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else>暂无数据</p>
  </div>
</template>

<script setup>
  import { ref, onMounted, computed } from "vue";
  // 1. 导入你封装好的 axios 实例，而不是原始的 axios。
  //    文件名是 `request.js` 或 `axios.js` 取决于你的项目。
  import request from "../api/axios"; // <-- 【修改点 1】
  import { useRouter } from "vue-router";
  import { jwtDecode } from "jwt-decode";
  import dayjs from 'dayjs';
  import utc from 'dayjs/plugin/utc';
  import timezone from 'dayjs/plugin/timezone';
  
  // ===================== 响应式状态 =====================
  const records = ref([]);
  const isLoading = ref(true);
  const user = ref(null);
  const filter = ref("all");
  const router = useRouter();
  
  // ===================== 插件初始化 =====================
  dayjs.extend(utc);
  dayjs.extend(timezone);
  
  // ===================== 核心方法 =====================
  
  async function fetchAdminDetections() {
    try {
      isLoading.value = true;
      const response = await request.get('/admin/detections');

      
      // 1. 先打印出来看看后端到底返回了什么，这是最佳调试手段！
      // console.log("【管理员模块】后端返回的原始数据:", response.data);

      // 2. 根据实际情况赋值。报错信息表明，后端直接返回了数组。
      //    所以我们应该直接使用 response.data
      records.value = response.data || []; // 使用 || [] 来防止后端返回 null 或 undefined

    } catch (error) {
      console.error("加载管理检测记录失败:", error);
      records.value = []; // 出错时，确保 records 是个空数组，防止页面崩溃
      alert(error.response?.data?.msg || "加载管理检测记录失败，请稍后重试。");
    } finally {
      isLoading.value = false;
    }
  }

  
  /**
   * 处理记录（上传或跳过）
   * @param {number} id - 记录的ID
   * @param {string} action - 'upload' 或 'skip'
   */
  async function process(id, action) {
    try {
      const payload = {
        ids: [id],
        action: action,
      };
  
      // 【修改点 3】: 使用封装好的 request 实例，并只使用相对路径
      const res = await request.post('/admin/process_detection', payload);
  
      alert(res.data.msg || "处理成功");
  
      // 更新前端UI状态，提供即时反馈
      const recordToUpdate = records.value.find(r => r.id === id);
      if (recordToUpdate) {
        recordToUpdate.is_processed = true;
        recordToUpdate.upload_status = action === 'upload' ? 'uploaded' : 'skipped';
      }
  
    } catch (error) {
      console.error("处理失败:", error);
      alert(`操作失败: ${error.response?.data?.msg || '请检查网络或联系管理员'}`);
    }
  }
  
  /**
   * 格式化 GMT 时间为北京时间
   */
  const formatBeijingTime = (gmtDate) => {
    if (!gmtDate) return 'N/A';
    return dayjs(gmtDate).tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
  };
  
  /**
   * 登出并跳转到登录页
   */
  function logout() {
    localStorage.removeItem("token");
    router.push("/login");
  }
  
  // ===================== 计算属性 =====================
  const filteredRecords = computed(() => {
    if (filter.value === "processed")
      return records.value.filter((r) => r.is_processed);
    if (filter.value === "unprocessed")
      return records.value.filter((r) => !r.is_processed);
    return records.value;
  });
  
  // ===================== 生命周期钩子 =====================
  onMounted(() => {
    // 【修改点 4】: 合并 onMounted 逻辑，代码更清晰
    const token = localStorage.getItem("token");
  
    if (!token) {
      logout();
      return;
    }
  
    try {
      const decoded = jwtDecode(token);
      const isExpired = decoded.exp < Date.now() / 1000;
      
      if (isExpired) {
        alert("登录已过期，请重新登录。");
        logout();
        return;
      }
  
      // Token 有效，设置用户信息并加载数据
      user.value = {
        id: decoded.sub,
        username: decoded.username,
        role: decoded.role,
      };
  
      // 确认是管理员角色才加载数据
      if (user.value.role === 'admin') {
        fetchAdminDetections();
      } else {
          alert("权限不足，无法访问此页面。");
          router.push('/'); // 或者跳转到用户自己的页面
      }
  
    } catch (e) {
      console.error("Token 解码或处理失败:", e);
      logout();
    }
  });
  </script>
  



<style scoped>
/* 顶部导航栏 */
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

/* 页面主体 */
.admin-page {
  padding: 20px;
  margin-top: 100px;
  text-align: center;
}

/* 筛选 */
.filters {
  margin: 15px 0;
}

.filters button {
  margin: 0 10px;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #42b983;
  background: white;
  cursor: pointer;
  transition: 0.2s;
}

.filters button.active,
.filters button:hover {
  background-color: #42b983;
  color: white;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.data-table th,
.data-table td {
  border: 1px solid #ddd;
  padding: 8px;
}

.preview {
  width: 100px;
  border-radius: 5px;
}

/* 状态标签 */
.status {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
}

.status.uploaded {
  background: #d4f8d4;
  color: #0b8a0b;
}

.status.skipped {
  background: #fff3cd;
  color: #b8860b;
}

.status.not {
  background: #f8d7da;
  color: #a30015;
}

/* 操作按钮 */
.btn-upload,
.btn-skip {
  margin: 3px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: white;
}

.btn-upload {
  background-color: #42b983;
}

.btn-skip {
  background-color: #888;
}

.btn-upload:disabled,
.btn-skip:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
