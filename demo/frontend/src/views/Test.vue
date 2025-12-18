<template>
  <div class="container">
    <!-- ===== 顶部栏 ===== -->
    <div class="top-bar">
      <h2>病虫害识别</h2>

      <!-- 只有 admin 才显示 -->
    <button
      v-if="user && user.role === 'admin'"
      @click="$router.push('/user_manage')"
    >
      用户管理
    </button>
    
    <button
      v-if="user && user.role === 'admin'"
      @click="$router.push('/audit')"
    >
      审核模块
    </button>

      <!-- 右上角用户信息 -->
      <div v-if="user" class="user-info">
        <span>你好，{{ user.username }}</span>
        <button @click="logout">退出登录</button>
      </div>
    </div>

    <!-- ===== 功能区 ===== -->

    <!-- 文件选择 -->
    <input type="file" multiple accept="image/*" @change="onFileChange" />

    <button @click="submit" :disabled="files.length === 0">
      开始识别
    </button>

    

    <!-- ===== 结果展示 ===== -->
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
        <span>{{ currentIndex + 1 }} / {{ pagedResults.length }}</span>
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
import { checkImage } from '@/api/ai'

const router = useRouter()

/* ===== 登录用户 ===== */
const user = ref(null)

onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) {
    user.value = JSON.parse(u)
  }
})

const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}

/* ===== 原有病虫害识别逻辑（未改） ===== */
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

      console.log('🔥 后端返回:', res)

      const prediction =
        res.data?.prediction ||
        res.prediction ||
        res.data?.data?.prediction

      if (!prediction) {
        throw new Error('找不到 prediction')
      }

      results.value.push({
        file,
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        className: prediction.class_name,
        confidence: prediction.confidence,
        label: ''
      })

    } catch (e) {
      console.error('❌ 识别失败:', e)

      results.value.push({
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        className: '识别失败',
        confidence: '-'
      })
    }
  }
}

const prev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

const next = () => {
  if (currentIndex.value < results.value.length - 1) {
    currentIndex.value++
  }
}
import axios from 'axios'

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
  formData.append('username', JSON.parse(localStorage.getItem('user')).username)

  await axios.post('http://localhost:9000/api/record/save', formData)

  alert('保存成功')
}

</script>

<style scoped>
.container {
  padding: 30px;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

button {
  margin: 10px 0;
}

.preview {
  width: 300px;
  border: 1px solid #ccc;
  margin-bottom: 10px;
}

.pager {
  margin-top: 10px;
}
</style>
