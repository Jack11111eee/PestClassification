<template>
  <div class="container">
    <h2>病虫害识别</h2>

    <!-- 文件选择 -->
    <input type="file" multiple accept="image/*" @change="onFileChange" />

    <button @click="submit" :disabled="files.length === 0">
      开始识别
    </button>

    <!-- 结果展示 -->
    <div v-if="pagedResults.length" class="result">
      <img
        :src="pagedResults[currentIndex].previewUrl"
        class="preview"
      />

      <p>文件名：{{ pagedResults[currentIndex].fileName }}</p>
      <p>识别结果：{{ pagedResults[currentIndex].className }}</p>
      <p>置信度：{{ pagedResults[currentIndex].confidence }}</p>

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
import { ref } from 'vue'
import { checkImage } from '@/api/ai'

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
      
      // 🚩【调试关键点 1】看看到底返回了什么！
      console.log('🔥 后端返回的完整数据:', res)

      // ⚠️ 原来的代码可能在这里报错了，跳到了 catch
      const prediction = res.data?.prediction || res.prediction || res.data?.data?.prediction
      
      if (!prediction) {
          throw new Error('找不到 prediction 字段')
      }

      results.value.push({
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        // 这里的取值逻辑我们根据 console.log 的结果来修，暂时先试图兼容一下
        className: prediction.class_name,
        confidence: prediction.confidence
      })
      
    } catch (e) {
      // 🚩【调试关键点 2】打印出真正的错误原因！
      console.error('❌ 解析失败，具体错误是:', e)
      
      results.value.push({
        fileName: file.name,
        previewUrl: URL.createObjectURL(file),
        className: '识别失败', 
        confidence: '-' // 暂时显示短横线
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
</script>

<style scoped>
.container {
  padding: 30px;
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
