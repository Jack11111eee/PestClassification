<template>
  <div class="app-container">
    <header class="nav-bar card">
      <div class="nav-brand">
        <span class="logo-text">图片审核系统</span>
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
          class="nav-item active"
        >
          审核模块
        </button>

        <button
          v-if="user"
          @click="router.push('/my_submission')"
          class="nav-item"
        >
          我的记录
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
          <h2>审核列表</h2>
          <span class="subtitle">管理并审核用户上传的识别记录</span>
        </div>
        <button 
          class="btn btn-primary filter-toggle" 
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
              <label>ID</label>
              <input v-model="filters.id" placeholder="输入ID" />
            </div>
            <div class="input-group">
              <label>用户名</label>
              <input v-model="filters.username" placeholder="输入用户名" />
            </div>
            <div class="input-group">
              <label>标签</label>
              <input v-model="filters.label" placeholder="输入标签" />
            </div>
            <div class="input-group">
              <label>识别结果</label>
              <input v-model="filters.className" placeholder="输入结果名称" />
            </div>
            <div class="input-group">
              <label>置信度 (Min)</label>
              <input
                v-model="filters.confidence"
                type="number"
                step="0.01"
                placeholder="例如 0.85"
              />
            </div>
            <div class="input-group">
              <label>状态</label>
              <select v-model="filters.status">
                <option value="">全部状态</option>
                <option value="PENDING">待审核</option>
                <option value="APPROVED">已上传</option>
                <option value="REJECTED">未上传</option>
              </select>
            </div>
            <div class="input-group">
              <label>日期</label>
              <input v-model="filters.date" type="date" />
            </div>
            <div class="input-group">
              <label>审核信息</label>
              <input v-model="filters.information" placeholder="关键词..." />
            </div>
          </div>

          <div class="filter-footer">
            <button class="btn btn-text" @click="resetFilter">重置条件</button>
            <button class="btn btn-primary" @click="applyFilter">应用筛选</button>
          </div>
        </div>
      </transition>

      <div class="card table-card">
        <div class="table-responsive">
          <table class="styled-table">
            <thead>
              <tr>
                <th width="60">ID</th>
                <th>用户</th>
                <th width="140">图片预览</th>
                <th>标签 / 结果</th>
                <th>置信度</th>
                <th>状态</th>
                <th>时间 / 备注</th>
                <th width="180">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredRecords" :key="item.id">
                <td class="text-secondary">#{{ item.id }}</td>
                <td class="font-bold">{{ item.username }}</td>
                <td>
                  <div class="img-wrapper">
                    <img
                      :src="getImageUrl(item.imagePath)"
                      alt="preview"
                      loading="lazy"
                    />
                  </div>
                </td>
                <td>
                  <div class="info-stack">
                    <span class="tag-label">标签: {{ item.label }}</span>
                    <span class="result-label">结果: {{ item.className }}</span>
                  </div>
                </td>
                <td :class="getConfidenceClass(item.confidence)">
                  {{ (item.confidence * 100).toFixed(1) }}%
                </td>
                <td>
                  <span :class="['status-badge', item.status.toLowerCase()]">
                    {{ statusText(item.status) }}
                  </span>
                </td>
                <td>
                  <div class="meta-info">
                    <small>{{ formatTime(item.createdAt) }}</small>
                    <small v-if="item.information" class="audit-note">{{ item.information }}</small>
                  </div>
                </td>
                <td>
                  <div class="action-buttons" v-if="item.status === 'PENDING'">
                    <button class="btn btn-success btn-sm" @click="approve(item)">✓ 通过</button>
                    <button class="btn btn-danger btn-sm" @click="openReject(item)">✕ 拒绝</button>
                  </div>
                  <span v-else class="text-disabled">已归档</span>
                </td>
              </tr>

              <tr v-if="filteredRecords.length === 0">
                <td colspan="8" class="empty-state">
                  暂无相关数据
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div v-if="showReject" class="modal-overlay" @click.self="showReject = false">
        <div class="modal-box">
          <div class="modal-header">
            <h3>拒绝上传</h3>
            <button class="close-btn" @click="showReject = false">×</button>
          </div>
          <div class="modal-body">
            <p class="modal-tip">请填写拒绝该图片上传的原因：</p>
            <textarea
              v-model="rejectReason"
              rows="4"
              placeholder="例如：图片模糊、无法识别..."
              class="modal-input"
            ></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn btn-default" @click="showReject = false">取消</button>
            <button class="btn btn-danger" @click="submitReject">确认拒绝</button>
          </div>
        </div>
      </div>
    </transition>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

/* ================= 基础配置 & 路由 ================= */
const router = useRouter()
const user = ref(null)
const records = ref([])
const showFilter = ref(false)

// 为了演示注销，添加一个简单的 logout 逻辑
const logout = () => {
  localStorage.removeItem('user')
  user.value = null
  // router.push('/login') // 如果有登录页请解开注释
}

/* ================= 生命周期 ================= */
onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) user.value = JSON.parse(u)
  loadRecords()
})

/* ================= 数据交互 ================= */
const loadRecords = async () => {
  try {
    const res = await axios.get('http://10.61.190.21:9000/api/record/all')
    records.value = res.data
  } catch (error) {
    console.error("加载失败", error)
  }
}

const getImageUrl = (path) => {
  if (!path) return ''
  const filename = path.substring(path.lastIndexOf('/') + 1)
  return `http://localhost:9000/uploads/${filename}`
}

/* ================= 辅助函数 ================= */
const statusText = (status) => {
  const map = {
    'PENDING': '待审核',
    'APPROVED': '已上传', // 这里根据你的业务逻辑，Approved对应已上传
    'REJECTED': '未上传'
  }
  return map[status] || status
}

const getConfidenceClass = (conf) => {
  if (conf >= 0.9) return 'text-success'
  if (conf >= 0.7) return 'text-warning'
  return 'text-danger'
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

/* ================= 筛选逻辑 ================= */
const filters = ref({
  id: '', username: '', label: '', className: '',
  confidence: '', status: '', date: '', information: ''
})
const activeFilters = ref({})

const applyFilter = () => { activeFilters.value = { ...filters.value } }
const resetFilter = () => {
  Object.keys(filters.value).forEach(k => (filters.value[k] = ''))
  activeFilters.value = {}
}

const filteredRecords = computed(() => {
  return records.value.filter(item => {
    const f = activeFilters.value
    if (f.id && !String(item.id).includes(f.id)) return false
    if (f.username && !item.username.includes(f.username)) return false
    if (f.label && !item.label.includes(f.label)) return false
    if (f.className && !item.className.includes(f.className)) return false
    if (f.status && item.status !== f.status) return false
    if (f.confidence && item.confidence < Number(f.confidence)) return false
    if (f.information && (!item.information || !item.information.includes(f.information))) return false
    if (f.date && !item.createdAt.startsWith(f.date)) return false
    return true
  })
})

/* ================= 审核逻辑 ================= */
const showReject = ref(false)
const rejectReason = ref('')
const currentItem = ref(null)

const approve = async (item) => {
  try {
    await axios.put(`http://10.61.190.21:9000/api/record/audit/${item.id}`, {
      status: 'APPROVED',
      information: '审核通过'
    })
    loadRecords()
  } catch (e) { alert('操作失败') }
}

const openReject = (item) => {
  currentItem.value = item
  rejectReason.value = ''
  showReject.value = true
}

const submitReject = async () => {
  if (!rejectReason.value.trim()) return alert('请输入拒绝原因')
  try {
    await axios.put(`http://10.61.190.21:9000/api/record/audit/${currentItem.value.id}`, {
      status: 'REJECTED',
      information: rejectReason.value
    })
    showReject.value = false
    loadRecords()
  } catch (e) { alert('操作失败') }
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
  max-width: 1200px;
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
  border-radius: 0;
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
}
.btn-logout:hover { color: #f56c6c; border-color: #f56c6c; }

/* ================= 工具栏 ================= */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title h2 { margin: 0; font-size: 22px; }
.page-title .subtitle { color: #909399; font-size: 13px; }

/* ================= 筛选区 ================= */
.filter-card {
  padding: 24px;
  border-top: 3px solid #409eff;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
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

.filter-footer {
  margin-top: 20px;
  text-align: right;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
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
  width: 100px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  transition: transform 0.2s;
  cursor: zoom-in;
}
.img-wrapper img:hover { transform: scale(1.5); box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 10; position: relative; }

/* 信息堆叠 */
.info-stack { display: flex; flex-direction: column; gap: 4px; }
.tag-label { font-size: 12px; color: #909399; }
.result-label { font-weight: 500; color: #303133; }

/* 状态徽章 */
.status-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.pending { background: #fdf6ec; color: #e6a23c; }
.status-badge.approved { background: #f0f9eb; color: #67c23a; }
.status-badge.rejected { background: #fef0f0; color: #f56c6c; }

/* 辅助文本 */
.meta-info { display: flex; flex-direction: column; font-size: 12px; color: #909399; }
.audit-note { color: #303133; margin-top: 4px; }
.text-success { color: #67c23a; font-weight: bold; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }

/* ================= 按钮 ================= */
.btn {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  padding: 8px 16px;
  font-size: 13px;
  transition: all 0.3s;
}

.btn-primary { background: #409eff; color: white; }
.btn-primary:hover { background: #66b1ff; }

.btn-text { background: none; color: #606266; }
.btn-text:hover { color: #409eff; }

.btn-sm { padding: 5px 10px; font-size: 12px; margin-right: 6px; }

.btn-success { background: #f0f9eb; color: #67c23a; border: 1px solid #c2e7b0; }
.btn-success:hover { background: #67c23a; color: white; }

.btn-danger { background: #fef0f0; color: #f56c6c; border: 1px solid #fbc4c4; }
.btn-danger:hover { background: #f56c6c; color: white; }

/* ================= 弹窗 (Modal) ================= */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(2px);
  display: flex; justify-content: center; align-items: center;
  z-index: 999;
}

.modal-box {
  background: white;
  width: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  overflow: hidden;
  animation: slideDown 0.3s ease;
}

.modal-header {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex; justify-content: space-between; align-items: center;
}
.modal-header h3 { margin: 0; font-size: 16px; }
.close-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #909399; }

.modal-body { padding: 20px; }
.modal-tip { margin: 0 0 10px; font-size: 13px; color: #606266; }

.modal-input {
  width: 100%; box-sizing: border-box;
  padding: 10px; border: 1px solid #dcdfe6;
  border-radius: 4px; resize: vertical;
  outline: none; font-family: inherit;
}
.modal-input:focus { border-color: #f56c6c; }

.modal-footer {
  padding: 15px 20px;
  background: #f9fafc;
  text-align: right;
  display: flex; justify-content: flex-end; gap: 10px;
}

.btn-default { background: white; border: 1px solid #dcdfe6; color: #606266; }
.btn-default:hover { color: #409eff; border-color: #c6e2ff; background: #ecf5ff; }

/* ================= 动画 ================= */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@keyframes slideDown {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.empty-state { text-align: center; padding: 40px; color: #909399; }
</style>