<template>
  <div class="container">

    <!-- ================= 顶部功能导航 ================= -->
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
      >
        审核模块
      </button>

      <button
        v-if="user"
        @click="router.push('/my_submission')"
        class="active">我的提交记录
      </button>

      <div v-if="user" class="user-info">
        <span>你好，{{ user.username }}</span>
        <button @click="logout">退出</button>
      </div>
    </div>

    
    <!-- ================= 标题 + 筛选按钮 ================= -->
    <h2 class="title">
      我的提交记录
      <button class="filter-btn" @click="showFilter = !showFilter">
        筛选 {{ showFilter ? '▲' : '▼' }}
      </button>
    </h2>

    <!-- ================= 筛选区 ================= -->
    <div v-if="showFilter" class="filter-panel">
      <select v-model="filters.status">
        <option value="">全部状态</option>
        <option value="PENDING">待审核</option>
        <option value="APPROVED">已上传</option>
        <option value="REJECTED">未上传</option>
      </select>

      <input v-model="filters.label" placeholder="标签关键词" />
      <input v-model="filters.className" placeholder="识别结果关键词" />

      <button @click="resetFilter">重置</button>
    </div>

    <!-- ================= 表格 ================= -->
    <table border="1" cellpadding="8">
      <thead>
        <tr>
          <th>ID</th>
          <th>图片</th>
          <th>标签</th>
          <th>识别结果</th>
          <th>置信度</th>
          <th>状态</th>
          <th>审核信息</th>
          <th>提交时间</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="item in filteredRecords" :key="item.id">
          <td>{{ item.id }}</td>

          <td>
            <img
              :src="getImageUrl(item.imagePath)"
              style="width:120px; border:1px solid #ccc"
            />
          </td>

          <td>{{ item.label }}</td>
          <td>{{ item.className }}</td>
          <td>{{ item.confidence }}</td>
          <td>{{ statusText(item.status) }}</td>
          <td>{{ item.information }}</td>
          <td>{{ formatTime(item.createdAt) }}</td>
        </tr>

        <tr v-if="filteredRecords.length === 0">
          <td colspan="8" style="text-align:center">
            无符合条件的记录
          </td>
        </tr>
      </tbody>
    </table>

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
  // 读取登录用户
  const u = localStorage.getItem('user')
  if (u) {
    user.value = JSON.parse(u)
  }

  loadMyRecords()
})

/* ================= 请求我的记录 ================= */
const loadMyRecords = async () => {
  const username = user.value?.username

  if (!username) {
    console.warn('未登录，无法加载提交记录')
    return
  }

  const res = await axios.get('http://10.61.190.21:9000/api/record/my', {
    params: { username }
  })

  records.value = res.data
}

/* ================= 计算属性：筛选 ================= */
const filteredRecords = computed(() => {
  return records.value.filter(item => {
    if (filters.value.status && item.status !== filters.value.status) {
      return false
    }
    if (
      filters.value.label &&
      !item.label?.includes(filters.value.label)
    ) {
      return false
    }
    if (
      filters.value.className &&
      !item.className?.includes(filters.value.className)
    ) {
      return false
    }
    return true
  })
})

const resetFilter = () => {
  filters.value = {
    status: '',
    label: '',
    className: ''
  }
}

/* ================= 工具函数 ================= */
const getImageUrl = (path) => {
  const filename = path.substring(path.lastIndexOf('/') + 1)
  return `http://10.61.190.21:9000/uploads/${filename}`
}

const statusText = (status) => {
  if (status === 'PENDING') return '待审核'
  if (status === 'APPROVED') return '已上传'
  if (status === 'REJECTED') return '未上传'
  return status
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
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

/* 标题 */
.title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 筛选 */
.filter-btn {
  font-size: 12px;
  padding: 4px 8px;
  cursor: pointer;
}

.filter-panel {
  margin: 10px 0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-panel input,
.filter-panel select {
  padding: 4px 6px;
}

.user-info {
  margin-left: auto;
}
</style>

