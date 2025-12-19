<template>
  <div class="container">

    <!-- ================= 顶部导航 ================= -->
    <div class="nav-bar">
      <button
        v-if="user"
        @click="router.push('/test')"
        class="active"
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
      >
        我的提交记录
      </button>

      <!-- 右侧用户信息 -->
      <div v-if="user" class="user-info">
        <span>你好，{{ user.username }}</span>
        <button @click="logout">退出</button>
      </div>
    </div>

    <!-- ================= 页面标题 ================= -->
    <h2 class="page-title">病虫害识别</h2>

    <!-- ================= 功能区 ================= -->
    <div class="control-panel">
      <input
        type="file"
        multiple
        accept="image/*"
        @change="onFileChange"
      />

      <button
        @click="submit"
        :disabled="files.length === 0"
      >
        开始识别
      </button>
    </div>

    <!-- ================= 结果展示 ================= -->
    <div v-if="pagedResults.length" class="result">

      <img
        :src="pagedResults[currentIndex].previewUrl"
        class="preview"
      />

      <p>文件名：{{ pagedResults[currentIndex].fileName }}</p>
      <p>识别结果：{{ pagedResults[currentIndex].className }}</p>
      <p>置信度：{{ pagedResults[currentIndex].confidence }}</p>

      <select v-model="pagedResults[currentIndex].label">
        <option disabled value="">请选择标签</option>
        <option value="健康">健康</option>
        <option value="轻度病害">轻度病害</option>
        <option value="严重病害">严重病害</option>
      </select>

      <button @click="saveRecord(pagedResults[currentIndex])">
        确认保存
      </button>

      <!-- 分页 -->
      <div class="pager">
        <button @click="prev" :disabled="currentIndex === 0">
          上一张
        </button>

        <span>
          {{ currentIndex + 1 }} / {{ pagedResults.length }}
        </span>

        <button
          @click="next"
          :disabled="currentIndex === pagedResults.length - 1"
        >
          下一张
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { checkImage } from '@/api/ai'

/* ================= 路由 & 用户 ================= */
const router = useRouter()
const user = ref(null)

onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) user.value = JSON.parse(u)
})

const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}

/* ================= 识别逻辑 ================= */
const files = ref([])
const results = ref([])
const currentIndex = ref(0)
const pagedResults = results

const onFileChange = (e) => {
  files.value = Array.from(e.target.files)
  results.value = []
  currentIndex.value = 0
}

const submit = async () => {
  results.value = []
  currentIndex.value = 0

  for (const file of files.value) {
    try {
      const res = await checkImage(file)

      const prediction =
        res.data?.prediction ||
        res.prediction ||
        res.data?.data?.prediction

      if (!prediction) throw new Error('prediction 不存在')

      results.value.push({
        file,
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        className: prediction.class_name,
        confidence: prediction.confidence,
        label: ''
      })
    } catch (e) {
      console.error('识别失败:', e)

      results.value.push({
        file,
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        className: '识别失败',
        confidence: '-',
        label: ''
      })
    }
  }
}

const prev = () => {
  if (currentIndex.value > 0) currentIndex.value--
}

const next = () => {
  if (currentIndex.value < results.value.length - 1)
    currentIndex.value++
}

/* ================= 保存记录 ================= */
const saveRecord = async (item) => {
  if (!item.label) {
    alert('请选择标签')
    return
  }

  const formData = new FormData()
  formData.append('file', item.file)
  formData.append('label', item.label)
  formData.append('className', item.className)
  formData.append('confidence', item.confidence)
  formData.append('username', user.value.username)

  await axios.post(
    'http://localhost:9000/api/record/save',
    formData
  )

  alert('保存成功')
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
  align-items: center;
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

.user-info {
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 页面标题 */
.page-title {
  margin-bottom: 15px;
}

/* 控制区 */
.control-panel {
  margin-bottom: 20px;
}

.preview {
  width: 300px;
  border: 1px solid #ccc;
  margin-bottom: 10px;
}

/* 分页 */
.pager {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
