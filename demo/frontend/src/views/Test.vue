<template>
  <div class="container">

    <!-- ================= 顶部导航 ================= -->
    <div class="nav-bar">
      <button v-if="user" @click="router.push('/test')" class="active">
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

      <button v-if="user" @click="router.push('/my_submission')">
        我的提交记录
      </button>

      <div v-if="user" class="user-info">
        <span>你好，{{ user.username }}</span>
        <button @click="logout">退出</button>
      </div>
    </div>

    <!-- ================= 页面标题 ================= -->
    <h2 class="page-title">病虫害识别</h2>

    <!-- ================= 功能区 ================= -->
    <div class="control-panel">
      <input type="file" multiple accept="image/*" @change="onFileChange" />
      <button @click="submit" :disabled="files.length === 0">
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

      <!-- ================= 二级联动选择 ================= -->

      <!-- 一级：作物 -->
      <select
        v-model="pagedResults[currentIndex].selectedCrop"
        @change="onCropChange(pagedResults[currentIndex])"
      >
        <option disabled value="">请选择作物</option>
        <option
          v-for="(crop, key) in cropDiseaseMap"
          :key="key"
          :value="key"
        >
          {{ crop.name }}
        </option>
      </select>

      <!-- 二级：病害 -->
      <select
        v-model="pagedResults[currentIndex].label"
        :disabled="!pagedResults[currentIndex].selectedCrop"
      >
        <option disabled value="">请选择病害</option>
        <option
          v-for="d in getDiseases(pagedResults[currentIndex].selectedCrop)"
          :key="d.value"
          :value="d.value"
        >
          {{ d.text }}
        </option>
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

/* ================= 作物 → 病害映射 ================= */
const cropDiseaseMap = {
  Apple: {
    name: '苹果',
    diseases: [
      { value: 'Apple_Black_Rot', text: '黑腐病' },
      { value: 'Apple_Cedar_Apple_Rust', text: '雪松苹果锈病' },
      { value: 'Apple_Scab', text: '黑星病' },
      { value: 'Apple_healthy', text: '健康' }
    ]
  },
  Corn: {
    name: '玉米',
    diseases: [
      { value: 'Corn_Common_Rust', text: '普通锈病' },
      { value: 'Corn_Gray_Leaf_Spot', text: '灰斑病' },
      { value: 'Corn_Northern_Leaf_Blight', text: '北方叶枯病' },
      { value: 'Corn_healthy', text: '健康' }
    ]
  },
  Tomato: {
    name: '番茄',
    diseases: [
      { value: 'Tomato_Bacterial_Spot', text: '细菌性斑点病' },
      { value: 'Tomato_Early_Blight', text: '早疫病' },
      { value: 'Tomato_Late_Blight', text: '晚疫病' },
      { value: 'Tomato_healthy', text: '健康' }
    ]
  },
  Peach: {
    name: '桃',
    diseases: [
      { value: 'Peach_Bacterial_Spot', text: '细菌性斑点病' },
      { value: 'Peach_healthy', text: '健康' }
    ]
  }
}

const getDiseases = (cropKey) => {
  return cropDiseaseMap[cropKey]?.diseases || []
}

const onCropChange = (item) => {
  item.label = '' // 切换作物时清空病害
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
    const res = await checkImage(file)
    const prediction = res.data?.prediction

    results.value.push({
      file,
      fileName: file.name,
      previewUrl: URL.createObjectURL(file),
      className: prediction?.class_name || '未知',
      confidence: prediction?.confidence || '-',
      selectedCrop: '',
      label: ''
    })
  }
}

const prev = () => currentIndex.value--
const next = () => currentIndex.value++

/* ================= 保存 ================= */
const saveRecord = async (item) => {
  if (!item.label) {
    alert('请选择病害标签')
    return
  }

  const formData = new FormData()
  formData.append('file', item.file)
  formData.append('label', item.label)
  formData.append('className', item.className)
  formData.append('confidence', item.confidence)
  formData.append('username', user.value.username)

  await axios.post('http://10.61.190.21:9000/api/record/save', formData)
  alert('保存成功')
}
</script>

<style scoped>
.container {
  padding: 20px;
}
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
.user-info {
  margin-left: auto;
}
.preview {
  width: 300px;
  border: 1px solid #ccc;
}
.pager {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}
</style>
