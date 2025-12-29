<template>
  <div class="app-container">
    <header class="nav-bar card">
      <div class="nav-brand">
        <span class="logo-text">用户中心</span>
      </div>
      
      <div class="nav-links">
        <button
          v-if="user"
          @click="router.push('/test')"
          class="nav-item"
        >
          识别系统
        </button>

        <button
          v-if="user && user.role === 'admin'"
          @click="router.push('/user_manage')"
          class="nav-item"
        >
          用户管理
        </button>

        <button
          v-if="user && (user.role === 'admin' || user.role === 'operator')"
          @click="router.push('/audit')"
          class="nav-item"
        >
          审核模块
        </button>

        <button
          v-if="user"
          @click="router.push('/my_submission')"
          class="nav-item active"
        >
          我的提交记录
        </button>
      </div>

      <div v-if="user" class="user-profile">
        <span class="username">Hi, {{ user.username }}</span>
        <button class="btn-logout" @click="logout">退出</button>
      </div>
    </header>

    <div class="main-content">
      <div class="toolbar">
        <div class="page-title">
          <h2>我的提交记录</h2>
          <span class="subtitle">查看您提交的所有图片识别与审核状态</span>
        </div>
        <button 
          class="btn btn-outline filter-toggle" 
          @click="showFilter = !showFilter"
          :class="{ 'is-active': showFilter }"
        >
          <span class="icon">🔍</span> {{ showFilter ? '收起筛选' : '展开筛选' }}
        </button>
      </div>

      <transition name="fade">
        <div v-if="showFilter" class="filter-card card">
          <div class="filter-grid">
            <div class="input-group">
              <label>审核状态</label>
              <select v-model="filters.status">
                <option value="">全部状态</option>
                <option value="PENDING">待审核</option>
                <option value="APPROVED">已上传</option>
                <option value="REJECTED">未上传</option>
              </select>
            </div>

            <div class="input-group">
              <label>标签关键词</label>
              <input v-model="filters.label" placeholder="例如：风景、人物" />
            </div>

            <div class="input-group">
              <label>识别结果</label>
              <input v-model="filters.className" placeholder="例如：Cat, Car" />
            </div>
            
            <div class="input-group align-bottom">
              <button class="btn btn-text" @click="resetFilter">重置条件</button>
            </div>
          </div>
        </div>
      </transition>

      <div class="card table-card">
        <div class="table-responsive">
          <table class="styled-table">
            <thead>
              <tr>
                <th width="80">ID</th>
                <th width="120">图片预览</th>
                <th>标签</th>
                <th>识别结果</th>
                <th>置信度</th>
                <th>当前状态</th>
                <th>审核反馈</th>
                <th>提交时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredRecords" :key="item.id">
                <td class="text-secondary">#{{ item.id }}</td>
                <td>
                  <div class="img-wrapper">
                    <img
                      :src="getImageUrl(item.imagePath)"
                      loading="lazy"
                    />
                  </div>
                </td>
                <td><span class="tag-pill">{{ item.label }}</span></td>
                <td class="font-medium">{{ item.className }}</td>
                <td :class="getConfidenceClass(item.confidence)">
                  {{ (item.confidence * 100).toFixed(1) }}%
                </td>
                <td>
                  <span :class="['status-badge', item.status.toLowerCase()]">
                    {{ statusText(item.status) }}
                  </span>
                </td>
                <td>
                  <span v-if="item.information" class="info-text">{{ item.information }}</span>
                  <span v-else class="text-placeholder">-</span>
                </td>
                <td class="time-text">{{ formatTime(item.createdAt) }}</td>
              </tr>

              <tr v-if="filteredRecords.length === 0">
                <td colspan="8" class="empty-state">
                  暂无符合条件的记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

/* ================= 路由 & 用户 ================= */
const router = useRouter()
const user = ref(null)

/* ================= 数据 ================= */
const records = ref([])
const showFilter = ref(false)

const filters = ref({
  status: '',
  label: '',
  className: ''
})

/* ================= 生命周期 ================= */
onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) {
    user.value = JSON.parse(u)
  }
  loadMyRecords()
})

const logout = () => {
  localStorage.removeItem('user')
  user.value = null
  router.push('/login') // 假设有登录页
}

/* ================= 请求我的记录 ================= */
const loadMyRecords = async () => {
  const username = user.value?.username
  if (!username) return

  try {
    const res = await axios.get('http://10.61.190.21:9000/api/record/my', {
      params: { username }
    })
    records.value = res.data
  } catch (error) {
    console.error("加载记录失败", error)
  }
}

/* ================= 计算属性：筛选 ================= */
const filteredRecords = computed(() => {
  return records.value.filter(item => {
    if (filters.value.status && item.status !== filters.value.status) return false
    if (filters.value.label && !item.label?.includes(filters.value.label)) return false
    if (filters.value.className && !item.className?.includes(filters.value.className)) return false
    return true
  })
})

const resetFilter = () => {
  filters.value = { status: '', label: '', className: '' }
}

/* ================= 工具函数 ================= */
const getImageUrl = (path) => {
  if (!path) return ''
  const filename = path.substring(path.lastIndexOf('/') + 1)
  return `http://10.61.190.21:9000/uploads/${filename}`
}

const statusText = (status) => {
  const map = {
    'PENDING': '待审核',
    'APPROVED': '已上传',
    'REJECTED': '未上传'
  }
  return map[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const getConfidenceClass = (conf) => {
  if (conf >= 0.9) return 'text-success'
  if (conf >= 0.7) return 'text-warning'
  return 'text-danger'
}
</script>

<style scoped>
/* ================= 全局变量 & 布局 ================= */
:root {
  --primary: #409eff;
  --success: #67c23a;
  --warning: #e6a23c;
  --danger: #f56c6c;
  --text-main: #303133;
  --text-sub: #909399;
  --bg-color: #f5f7fa;
  --border: #ebeef5;
}

.app-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #303133;
}

.main-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

/* ================= 卡片通用样式 ================= */
.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

/* ================= 导航栏 (Header) ================= */
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  position: sticky;
  top: 0;
  z-index: 100;
  border-radius: 0; /* 顶部无圆角 */
}

.nav-brand .logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-item {
  background: none;
  border: none;
  font-size: 15px;
  color: #606266;
  cursor: pointer;
  padding: 20px 0;
  position: relative;
  transition: all 0.3s;
}

.nav-item:hover, .nav-item.active {
  color: #409eff;
  font-weight: 500;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: #409eff;
  border-radius: 2px 2px 0 0;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.btn-logout {
  border: 1px solid #dcdfe6;
  background: #fff;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  color: #909399;
  font-size: 12px;
}
.btn-logout:hover { color: #f56c6c; border-color: #f56c6c; }

/* ================= 工具栏 ================= */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title h2 { margin: 0; font-size: 22px; color: #303133; }
.page-title .subtitle { color: #909399; font-size: 13px; margin-top: 4px; display: block; }

/* ================= 筛选区 ================= */
.filter-card {
  padding: 20px;
  border-left: 4px solid #409eff;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  align-items: end;
}

.input-group label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.input-group input, .input-group select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  outline: none;
  font-size: 13px;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.input-group input:focus, .input-group select:focus {
  border-color: #409eff;
}

/* ================= 表格样式 ================= */
.table-responsive { overflow-x: auto; }

.styled-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.styled-table th {
  background: #f5f7fa;
  color: #909399;
  font-weight: 600;
  text-align: left;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.styled-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  vertical-align: middle;
  color: #606266;
}

.styled-table tr:hover { background: #fafafa; }

/* 图片 */
.img-wrapper img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

/* 标签与胶囊 */
.tag-pill {
  background: #f4f4f5;
  color: #909399;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
  min-width: 50px;
  text-align: center;
}
.status-badge.pending { background: #fdf6ec; color: #e6a23c; }
.status-badge.approved { background: #f0f9eb; color: #67c23a; }
.status-badge.rejected { background: #fef0f0; color: #f56c6c; }

/* 辅助文本 */
.font-medium { font-weight: 500; color: #303133; }
.text-secondary { color: #909399; font-family: monospace; }
.text-placeholder { color: #dcdfe6; }
.time-text { font-size: 12px; color: #909399; width: 90px; }
.text-success { color: #67c23a; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }

/* ================= 按钮 ================= */
.btn {
  border-radius: 4px;
  cursor: pointer;
  padding: 8px 16px;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-outline {
  background: white;
  border: 1px solid #dcdfe6;
  color: #606266;
}
.btn-outline:hover, .btn-outline.is-active {
  color: #409eff;
  border-color: #c6e2ff;
  background: #ecf5ff;
}

.btn-text {
  background: none;
  border: none;
  color: #909399;
  padding: 0;
}
.btn-text:hover { color: #409eff; text-decoration: underline; }

/* ================= 动画 ================= */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-10px); }

.empty-state { text-align: center; padding: 40px; color: #909399; }
</style>