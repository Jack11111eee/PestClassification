<template>
  <div class="app-container">
    <header class="nav-bar">
      <div class="nav-logo">🌾 农医识别系统</div>
      <div class="nav-links">
        <button v-if="user" @click="router.push('/test')" class="nav-btn active">识别系统</button>
        <button v-if="user?.role === 'admin'" @click="router.push('/user_manage')" class="nav-btn">用户管理</button>
        <button v-if="user?.role === 'admin' || user?.role === 'operator'" @click="router.push('/audit')" class="nav-btn">审核模块</button>
        <button v-if="user" @click="router.push('/my_submission')" class="nav-btn">我的提交</button>
      </div>
      <div v-if="user" class="user-meta">
        <span class="welcome">你好, <strong>{{ user.username }}</strong></span>
        <button class="logout-btn" @click="logout">退出</button>
      </div>
    </header>

    <main class="main-content">
      <div class="page-header">
        <h2 class="title">病虫害 AI 智能识别</h2>
        <p class="subtitle">上传叶片照片，获取 AI 诊断建议与热力分析</p>
      </div>

      <section class="control-card card">
        <div class="upload-zone">
          <label class="file-label">
            <input type="file" multiple accept="image/*" @change="onFileChange" class="file-input" />
            <span class="upload-icon">📸</span>
            <span>{{ files.length > 0 ? `已选择 ${files.length} 张图片` : '点击上传叶片照片' }}</span>
          </label>
          <button class="submit-btn" @click="submit" :disabled="files.length === 0">
            开始 AI 识别
          </button>
        </div>
      </section>

      <section v-if="results.length > 0" class="result-section">
        <div class="result-grid">
          
          <div class="image-card card">
            <div class="image-container">
              <div class="img-wrapper">
                <span class="img-label">原始图片</span>
                <img :src="results[currentIndex].previewUrl" class="preview-img" />
              </div>
              <div class="img-wrapper" v-if="results[currentIndex].heatmap">
                <span class="img-label accent">热力分析图</span>
                <img :src="results[currentIndex].heatmap!" class="preview-img heatmap-img" />
              </div>
            </div>
            
            <div class="pager">
              <button @click="prev" :disabled="currentIndex === 0" class="page-btn">上一张</button>
              <span class="page-info">{{ currentIndex + 1 }} / {{ results.length }}</span>
              <button @click="next" :disabled="currentIndex === results.length - 1" class="page-btn">下一张</button>
            </div>
          </div>

          <div class="data-card card">
            <div class="ai-score">
              <div class="score-info">
                <span class="class-name">{{ results[currentIndex].className }}</span>
                <span class="conf-val" :class="getConfClass(results[currentIndex].confidence)">
                  置信度: {{ formatConf(results[currentIndex].confidence) }}
                </span>
              </div>
            </div>

            <div class="info-block" v-if="results[currentIndex].explanation?.message">
              <label>AI 诊断说明</label>
              <p>{{ results[currentIndex].explanation?.message }}</p>
            </div>

            <div class="info-block" v-if="results[currentIndex].advice.length">
              <label>防治建议</label>
              <ul class="advice-list">
                <li v-for="(a, i) in results[currentIndex].advice" :key="i">{{ a }}</li>
              </ul>
            </div>

            <div class="calibration-zone">
              <label class="zone-title">结果校准与保存</label>
              <div class="select-group">
                <select v-model="results[currentIndex].selectedCrop" @change="onCropChange(results[currentIndex])">
                  <option value="">请选择作物</option>
                  <option v-for="(crop, key) in cropDiseaseMap" :key="key" :value="key">{{ crop.name }}</option>
                </select>

                <select v-model="results[currentIndex].label" :disabled="!results[currentIndex].selectedCrop">
                  <option value="">请选择病害</option>
                  <option v-for="d in getDiseases(results[currentIndex].selectedCrop)" :key="d.value" :value="d.value">{{ d.text }}</option>
                </select>
              </div>
              <button class="save-btn" @click="saveRecord(results[currentIndex])">确认并保存</button>
            </div>
          </div>

        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { checkImage } from '../api/ai'

/* ================= 类型定义 (解决 TS 报错) ================= */
interface User {
  username: string;
  role: 'admin' | 'operator' | 'user';
}

interface ResultItem {
  file: File;
  fileName: string;
  previewUrl: string;
  className: string;
  confidence: number | string;
  explanation: any;
  heatmap: string | null;
  advice: string[];
  selectedCrop: string;
  label: string;
}

/* ================= 状态声明 ================= */
const router = useRouter()
const user = ref<User | null>(null)
const files = ref<File[]>([])
const results = ref<ResultItem[]>([])
const currentIndex = ref(0)

/* ================= 生命周期 ================= */
onMounted(() => {
  const u = localStorage.getItem('user')
  if (u) user.value = JSON.parse(u)
})

const logout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}

/* ================= 业务逻辑 ================= */
const cropDiseaseMap: Record<string, any> = {
  Apple: { name: '苹果', diseases: [
    { value: 'Apple_Black_Rot', text: '黑腐病' },
    { value: 'Apple_Cedar_Apple_Rust', text: '雪松苹果锈病' },
    { value: 'Apple_Scab', text: '黑星病' },
    { value: 'Apple_healthy', text: '健康' }
  ]},
  Corn: { name: '玉米', diseases: [
    { value: 'Corn_Common_Rust', text: '普通锈病' },
    { value: 'Corn_Gray_Leaf_Spot', text: '灰斑病' },
    { value: 'Corn_Northern_Leaf_Blight', text: '北方叶枯病' },
    { value: 'Corn_healthy', text: '健康' }
  ]},
  Tomato: { name: '番茄', diseases: [
    { value: 'Tomato_Bacterial_Spot', text: '细菌性斑点病' },
    { value: 'Tomato_Early_Blight', text: '早疫病' },
    { value: 'Tomato_Late_Blight', text: '晚疫病' },
    { value: 'Tomato_healthy', text: '健康' }
  ]}
}

const getDiseases = (cropKey: string) => cropDiseaseMap[cropKey]?.diseases || []
const onCropChange = (item: ResultItem) => { item.label = '' }

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    files.value = Array.from(target.files)
    results.value = []
    currentIndex.value = 0
  }
}

const submit = async () => {
  results.value = []
  for (const file of files.value) {
    try {
      const res = await checkImage(file)
      const prediction = res.data?.prediction
      const explanation = res.data?.explanation

      results.value.push({
        file,
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        className: prediction?.class_name || '未知',
        confidence: prediction?.confidence ?? 0,
        explanation,
        heatmap: (explanation?.heatmap_image && explanation.heatmap_image !== 'fault') ? explanation.heatmap_image : null,
        advice: explanation?.suggested_actions || [],
        selectedCrop: '',
        label: ''
      })
    } catch (err) {
      console.error("识别失败", err)
    }
  }
}

const saveRecord = async (item: ResultItem) => {
  if (!item.label || !user.value) return alert('请先选择病害标签')
  
  const formData = new FormData()
  formData.append('file', item.file)
  formData.append('label', item.label)
  formData.append('className', item.className)
  formData.append('confidence', String(item.confidence))
  formData.append('username', user.value.username)

  await axios.post('http://10.61.190.21:9000/api/record/save', formData)
  alert('记录保存成功')
}

const prev = () => currentIndex.value--
const next = () => currentIndex.value++

/* ================= 格式化工具 ================= */
const formatConf = (val: number | string) => {
  const n = Number(val)
  return isNaN(n) ? '0%' : (n * 100).toFixed(2) + '%'
}

const getConfClass = (val: number | string) => {
  const n = Number(val)
  if (n > 0.8) return 'text-success'
  if (n > 0.5) return 'text-warning'
  return 'text-danger'
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: #f8fafc;
  color: #1e293b;
  font-family: -apple-system, sans-serif;
}

/* 导航 */
.nav-bar {
  background: #ffffff;
  padding: 0 40px;
  height: 64px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  position: sticky;
  top: 0; z-index: 100;
}
.nav-logo { font-weight: 800; color: #10b981; font-size: 1.2rem; margin-right: 40px; }
.nav-links { display: flex; gap: 10px; flex: 1; }
.nav-btn {
  background: none; border: none; padding: 8px 16px; 
  cursor: pointer; color: #64748b; font-weight: 500;
}
.nav-btn.active { color: #10b981; border-bottom: 2px solid #10b981; }
.user-meta { display: flex; align-items: center; gap: 15px; font-size: 14px; }
.logout-btn { border: 1px solid #e2e8f0; background: #fff; padding: 4px 12px; border-radius: 4px; cursor: pointer; }

/* 布局 */
.main-content { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
.page-header { text-align: center; margin-bottom: 40px; }
.subtitle { color: #94a3b8; margin-top: 8px; }

.card { background: #fff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 24px; }

/* 上传区 */
.upload-zone { display: flex; justify-content: space-between; align-items: center; }
.file-label { 
  flex: 1; border: 2px dashed #e2e8f0; border-radius: 8px; 
  padding: 20px; text-align: center; cursor: pointer; transition: 0.3s;
}
.file-label:hover { border-color: #10b981; background: #f0fdf4; }
.file-input { display: none; }
.submit-btn { 
  margin-left: 20px; background: #10b981; color: #fff; border: none;
  padding: 16px 32px; border-radius: 8px; font-weight: bold; cursor: pointer;
}
.submit-btn:disabled { background: #cbd5e1; cursor: not-allowed; }

/* 结果区 */
.result-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; margin-top: 30px; }
.image-container { display: flex; gap: 15px; }
.img-wrapper { flex: 1; }
.img-label { font-size: 12px; color: #94a3b8; margin-bottom: 8px; display: block; }
.img-label.accent { color: #f59e0b; font-weight: bold; }
.preview-img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 8px; background: #f1f5f9; }

.ai-score { margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #f1f5f9; }
.class-name { font-size: 28px; font-weight: 800; display: block; }
.conf-val { font-size: 14px; font-weight: 600; }

.info-block { margin-bottom: 20px; }
.info-block label { font-size: 12px; color: #94a3b8; font-weight: bold; text-transform: uppercase; }
.info-block p { line-height: 1.6; margin-top: 5px; }
.advice-list { padding-left: 20px; margin-top: 8px; color: #475569; }

.calibration-zone { background: #f8fafc; padding: 20px; border-radius: 8px; margin-top: 30px; }
.select-group { display: flex; gap: 10px; margin: 15px 0; }
select { flex: 1; padding: 10px; border: 1px solid #e2e8f0; border-radius: 6px; outline: none; }
.save-btn { width: 100%; background: #3b82f6; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; }

/* 辅助 */
.text-success { color: #10b981; }
.text-warning { color: #f59e0b; }
.text-danger { color: #ef4444; }
.pager { display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }
.page-btn { padding: 8px 16px; border: 1px solid #e2e8f0; background: #fff; border-radius: 6px; cursor: pointer; }
</style>