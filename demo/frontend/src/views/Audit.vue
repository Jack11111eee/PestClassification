<template>
  <div class="container">
    <h2>图片审核列表</h2>

    <table border="1" cellpadding="8">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户</th>
          <th>图片路径</th>
          <th>标签</th>
          <th>识别结果</th>
          <th>置信度</th>
          <th>状态</th>
          <th>上传时间</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="item in records" :key="item.id">
          <td>{{ item.id }}</td>
          <td>{{ item.username }}</td>
         <td>
            <img
                :src="getImageUrl(item.imagePath)"
                alt="图片"
                style="width:120px; border:1px solid #ccc"
            />
         </td>


          <td>{{ item.label }}</td>
          <td>{{ item.className }}</td>
          <td>{{ item.confidence }}</td>
          <td>{{ item.status }}</td>
          <td>{{ item.createdAt }}</td>
        </tr>

        <tr v-if="records.length === 0">
          <td colspan="8" style="text-align:center">
            暂无数据
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const records = ref([])

const loadRecords = async () => {
  const res = await axios.get('http://localhost:9000/api/record/all')
  console.log('审核数据：', res.data)
  records.value = res.data
}

const getImageUrl = (path) => {
  const filename = path.substring(path.lastIndexOf('/') + 1)
  return `http://localhost:9000/uploads/${filename}`
}

onMounted(loadRecords)
</script>

<style scoped>
.container {
  padding: 30px;
}
table {
  width: 100%;
  margin-top: 20px;
  border-collapse: collapse;
}
th, td {
  border: 1px solid #ccc;
}
</style>
