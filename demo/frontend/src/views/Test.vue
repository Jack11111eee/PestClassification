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
        <option value="Apple_Black_Rot">Apple_Black_Rot</option>
        <option value="Apple_Cedar_Apple_Rust">Apple_Cedar_Apple_Rust</option>
        <option value="Apple_healthy">Apple_healthy</option>
        <option value="Apple_Scab">Apple_Scab</option>

        <option value="Blueberry_healthy">Blueberry_healthy</option>

        <option value="Cherry_healthy">Cherry_healthy</option>
        <option value="Cherry_Powdery_Mildew">Cherry_Powdery_Mildew</option>

        <option value="Corn_Common_Rust">Corn_Common_Rust</option>
        <option value="Corn_Gray_Leaf_Spot">Corn_Gray_Leaf_Spot</option>
        <option value="Corn_healthy">Corn_healthy</option>
        <option value="Corn_Northern_Leaf_Blight">Corn_Northern_Leaf_Blight</option>

        <option value="Grape_Black_Rot">Grape_Black_Rot</option>
        <option value="Grape_Esca_Black_Measles">Grape_Esca_Black_Measles</option>
        <option value="Grape_healthy">Grape_healthy</option>
        <option value="Grape_Leaf_Blight_Isariopsis">Grape_Leaf_Blight_Isariopsis</option>

        <option value="Orange_Haunglongbing_Citrus_Greening">
          Orange_Haunglongbing_Citrus_Greening
        </option>

        <option value="Peach_Bacterial_Spot">Peach_Bacterial_Spot</option>
        <option value="Peach_healthy">Peach_healthy</option>

        <option value="Pepper_Bell_Bacterial_Spot">Pepper_Bell_Bacterial_Spot</option>
        <option value="Pepper_Bell_healthy">Pepper_Bell_healthy</option>

        <option value="Potato_Early_Blight">Potato_Early_Blight</option>
        <option value="Potato_healthy">Potato_healthy</option>
        <option value="Potato_Late_Blight">Potato_Late_Blight</option>

        <option value="Raspberry_healthy">Raspberry_healthy</option>
        <option value="Soybean_healthy">Soybean_healthy</option>
        <option value="Squash_Powdery_Mildew">Squash_Powdery_Mildew</option>

        <option value="Strawberry_healthy">Strawberry_healthy</option>
        <option value="Strawberry_Leaf_Scorch">Strawberry_Leaf_Scorch</option>

        <option value="Tomato_Bacterial_Spot">Tomato_Bacterial_Spot</option>
        <option value="Tomato_Early_Blight">Tomato_Early_Blight</option>
        <option value="Tomato_healthy">Tomato_healthy</option>
        <option value="Tomato_Late_Blight">Tomato_Late_Blight</option>
        <option value="Tomato_Leaf_Mold">Tomato_Leaf_Mold</option>
        <option value="Tomato_Mosaic_Virus">Tomato_Mosaic_Virus</option>
        <option value="Tomato_Septoria_Leaf_Spot">Tomato_Septoria_Leaf_Spot</option>
        <option value="Tomato_Target_Spot">Tomato_Target_Spot</option>
        <option value="Tomato_Two_Spotted_Spider_Mite">
          Tomato_Two_Spotted_Spider_Mite
        </option>
        <option value="Tomato_Yellow_Leaf_Curl_Virus">
          Tomato_Yellow_Leaf_Curl_Virus
        </option>

        <option value="Wheat_Crown_and_Root_Rot">Wheat_Crown_and_Root_Rot</option>
        <option value="Wheat_healthy">Wheat_healthy</option>
        <option value="Wheat_Leaf_Rust">Wheat_Leaf_Rust</option>
        <option value="Wheat_Loose_Smut">Wheat_Loose_Smut</option>

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

