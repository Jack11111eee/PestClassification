<!-- frontend/src/views/MySubmissions.vue -->
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

  <div class="submissions-container">
    <h1>我的提交历史</h1>
    <div v-if="isLoading" class="loading-spinner">正在加载...</div>
    <div v-else-if="submissions.length === 0" class="no-data">
      您还没有提交过任何反馈。
    </div>
    <div v-else class="table-responsive">
      <table class="submissions-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>图片预览</th>
            <th>提交标签</th>
            <th>置信度</th>
            <th>状态</th>
            <th>提交时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="submission in submissions" :key="submission.id">
            <td>{{ submission.id }}</td>
            <td>
              <img :src="getImageUrl(submission.image_path)" alt="预览" class="preview-img">
            </td>
            <td>{{ submission.label }}</td>
            <td>{{ submission.confidence ? submission.confidence.toFixed(2) : 'N/A' }}</td>
            <td>
              <span :class="['status-badge', `status-${submission.upload_status}`]">
                {{ formatStatus(submission.upload_status) }}
              </span>
            </td>
            <td>{{ formatDateTime(submission.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '../api/axios.js'; 

const submissions = ref([]);
const isLoading = ref(true);
const backendUrl = 'http://127.0.0.1:5000';

import { useRouter } from "vue-router";
import { jwtDecode } from "jwt-decode";

const router = useRouter();

// ===================== 用户信息获取 =====================
const user = ref(null);
const token = localStorage.getItem("token");

onMounted(() => {
  if (!token) {
    // 如果没有token，根据你的路由设置，应该强制跳转到登录
    router.push("/login");
    return;
  };

  try {
    const decoded = jwtDecode(token);
    const expired = decoded.exp < Date.now() / 1000;
    if (!expired) {
      user.value = {
        id: decoded.sub,
        username: decoded.username,
        role: decoded.role,
      };
    } else {
      // token 过期也应登出
      logout();
    }
  } catch (e) {
    console.error("Token 解码失败", e);
    logout(); // 解码失败也登出
  }
});

// --- 生命周期钩子 ---
onMounted(() => {
  fetchMyDetections();
});

// --- 方法 ---
async function fetchMyDetections() {
  try {
    isLoading.value = true;
    // ++ 修改点 3: 直接使用导入的 axios 实例来发送请求 ++
    // 因为 baseURL 已配置，所以这里只需要写相对路径
    const response = await axios.get('/detection/my-detections');
    submissions.value = response.data;
  } catch (error) {
    console.error("加载提交历史失败:", error);
    // 根据实际情况，可以提供更友好的错误提示
    if (error.response && error.response.status === 401) {
      alert("登录已过期，请重新登录。");
      // 可以在这里触发登出或跳转到登录页
    } else {
      alert("加载失败，请稍后重试。");
    }
  } finally {
    isLoading.value = false;
  }
}

// 辅助函数：将后台返回的图片路径转换为可访问的完整 URL
function getImageUrl(imagePath) {
  if (!imagePath) return '';
  const cleanPath = imagePath.startsWith('/') ? imagePath.substring(1) : imagePath;
  return `${backendUrl}/${cleanPath}`;
}

// 辅助函数：格式化状态显示文本
function formatStatus(status) {
  const statusMap = {
    pending: '待处理',
    approved: '已采纳',
    rejected: '未采纳',
    uploaded: '已采纳', // 兼容旧数据
  };
  return statusMap[status] || status;
}

// 辅助函数：格式化日期时间
function formatDateTime(dateTimeString) {
  if (!dateTimeString) return 'N/A';
  return new Date(dateTimeString).toLocaleString('zh-CN');
}
</script>

<style scoped>
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
/* 样式代码与之前相同，保持不变 */
.submissions-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 2rem;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #333;
}

.loading-spinner, .no-data {
  text-align: center;
  padding: 3rem;
  font-size: 1.2rem;
  color: #666;
}

.table-responsive {
  overflow-x: auto;
}

.submissions-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.submissions-table th,
.submissions-table td {
  border: 1px solid #ddd;
  padding: 12px 15px;
  text-align: center;
  vertical-align: middle;
}

.submissions-table th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.preview-img {
  max-width: 100px;
  max-height: 100px;
  border-radius: 4px;
  object-fit: cover;
}

.status-badge {
  padding: 5px 10px;
  border-radius: 12px;
  color: #fff;
  font-size: 0.9rem;
  font-weight: bold;
}

.status-pending {
  background-color: #ffc107; /* 黄色 */
}
.status-approved, .status-uploaded {
  background-color: #28a745; /* 绿色 */
}
.status-rejected {
  background-color: #dc3545; /* 红色 */
}
</style>
