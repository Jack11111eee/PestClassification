<template>
  <div class="container">

    <!-- ================= 顶部导航 ================= -->
    <div class="nav-bar">
      <button
        v-if="user"
        @click="router.push('/test')"
      >
        识别系统
      </button>

      <button
        v-if="user && user.role === 'admin'"
        @click="router.push('/user_manage')"
      >
        用户管理
      </button>

      <button
        v-if="user && (user.role === 'admin' || user.role === 'operator')"
        @click="router.push('/audit')"
        class="active"
      >
        审核模块
      </button>

      <button
        v-if="user"
        @click="router.push('/my_submission')"
      >
        我的提交记录
      </button>

      <div v-if="user" class="user-info">
        <span>你好，{{ user.username }}</span>
        <button @click="logout">退出</button>
      </div>
    </div>

    <!-- ================= 工具栏 ================= -->
    <div class="toolbar">
      <h2>图片审核列表</h2>
      <button class="filter-btn" @click="showFilter = !showFilter">
        🔍 筛选
      </button>
    </div>

    <!-- ================= 筛选面板 ================= -->
    <div v-if="showFilter" class="filter-panel">
      <div class="filter-grid">
        <input v-model="filters.id" placeholder="ID" />
        <input v-model="filters.username" placeholder="用户" />
        <input v-model="filters.label" placeholder="标签" />
        <input v-model="filters.className" placeholder="识别结果" />

        <input
          v-model="filters.confidence"
          type="number"
          step="0.01"
          placeholder="最小置信度"
        />

        <select v-model="filters.status">
          <option value="">全部状态</option>
          <option value="PENDING">待审核</option>
          <option value="APPROVED">已上传</option>
          <option value="REJECTED">未上传</option>
        </select>

        <input v-model="filters.date" type="date" />
        <input v-model="filters.information" placeholder="审核信息" />
      </div>

      <div class="filter-actions">
        <button @click="applyFilter">应用</button>
        <button @click="resetFilter">重置</button>
      </div>
    </div>

    <!-- ================= 表格 ================= -->
    <table border="1" cellpadding="8">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户</th>
          <th>图片</th>
          <th>标签</th>
          <th>识别结果</th>
          <th>置信度</th>
          <th>状态</th>
          <th>上传时间</th>
          <th>审核结果</th>
          <th>操作</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="item in filteredRecords" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.username }}</td>

          <td>
            <img
              :src="getImageUrl(item.imagePath)"
              style="width:120px; border:1px solid #ccc"
            />
          </td>

          <td>{{ item.label }}</td>
          <td>{{ item.className }}</td>
          <td>{{ item.confidence }}</td>

          <td>
            <span :class="item.status.toLowerCase()">
              {{ statusText(item.status) }}
            </span>
          </td>

          <td>{{ formatTime(item.createdAt) }}</td>
          <td>{{ item.information }}</td>

          <td>
            <template v-if="item.status === 'PENDING'">
              <button @click="approve(item)">上传</button>
              <button @click="openReject(item)">不上传</button>
            </template>
            <span v-else>已处理</span>
          </td>
        </tr>

        <tr v-if="filteredRecords.length === 0">
          <td colspan="10" style="text-align:center">
            暂无数据
          </td>
        </tr>
      </tbody>
    </table>

    <!-- ================= 不上传弹窗 ================= -->
    <div v-if="showReject" class="modal-mask">
      <div class="modal-box">
        <h3>请输入不上传原因</h3>

        <textarea
          v-model="rejectReason"
          rows="4"
          placeholder="请输入原因"
        ></textarea>

        <div class="modal-actions">
          <button @click="submitReject">提交</button>
          <button @click="showReject = false">取消</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

/* ================= 用户 & 路由 ================= */
const router = useRouter()
const user = ref(null)

/* ================= 数据 ================= */
const records = ref([])
const showFilter = ref(false)

/* ================= 生命周期 ================= */
onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) user.value = JSON.parse(u)

  loadRecords()
})

/* ================= 加载数据 ================= */
const loadRecords = async () => {
  const res = await axios.get('http://10.61.190.21:9000/api/record/all')
  records.value = res.data
}

/* ================= 图片路径 ================= */
const getImageUrl = (path) => {
  const filename = path.substring(path.lastIndexOf('/') + 1)
  return `http://localhost:9000/uploads/${filename}`
}

/* ================= 状态文本 ================= */
const statusText = (status) => {
  if (status === 'PENDING') return '待审核'
  if (status === 'APPROVED') return '同意'
  if (status === 'REJECTED') return '拒绝'
  return status
}

/* ================= 筛选 ================= */
const filters = ref({
  id: '',
  username: '',
  label: '',
  className: '',
  confidence: '',
  status: '',
  date: '',
  information: ''
})

const activeFilters = ref({})

const applyFilter = () => {
  activeFilters.value = { ...filters.value }
}

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
    if (f.information &&
        (!item.information || !item.information.includes(f.information)))
      return false
    if (f.date && !item.createdAt.startsWith(f.date)) return false

    return true
  })
})

/* ================= 审核逻辑 ================= */
const showReject = ref(false)
const rejectReason = ref('')
const currentItem = ref(null)

const approve = async (item) => {
  await axios.put(`http://10.61.190.21:9000/api/record/audit/${item.id}`, {
    status: 'APPROVED',
    information: '同意'
  })
  loadRecords()
}

const openReject = (item) => {
  currentItem.value = item
  rejectReason.value = ''
  showReject.value = true
}

const submitReject = async () => {
  if (!rejectReason.value.trim()) return

  await axios.put(
    `http://10.61.190.21:9000/api/record/audit/${currentItem.value.id}`,
    {
      status: 'REJECTED',
      information: rejectReason.value
    }
  )

  showReject.value = false
  loadRecords()
}

/* ================= 时间格式 ================= */
const formatTime = (time) => {
  if (!time) return ''

  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}
          ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.container {
  padding: 20px;
}

/* 顶部导航 */
.nav-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.nav-bar button {
  padding: 6px 12px;
  cursor: pointer;
}

.nav-bar .active {
  background: #409eff;
  color: #fff;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-btn {
  padding: 6px 12px;
  cursor: pointer;
}

/* 筛选 */
.filter-panel {
  background: #fff;
  border: 1px solid #ddd;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 6px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.filter-actions {
  text-align: right;
  margin-top: 10px;
}

/* 表格 */
table {
  width: 100%;
  border-collapse: collapse;
}

/* 状态颜色 */
.pending {
  color: orange;
}
.approved {
  color: green;
}
.rejected {
  color: red;
}

/* 弹窗 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-box {
  background: #fff;
  padding: 20px;
  width: 360px;
  border-radius: 6px;
}

.modal-box textarea {
  width: 100%;
  margin-top: 10px;
}

.modal-actions {
  text-align: right;
  margin-top: 10px;
}
.user-info {
  margin-left: auto;
}
</style>

