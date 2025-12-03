<template>
  <header>
    <nav>
      <div class="nav">
        <a href="/home">返回用户主页</a>
        <a href="/admin/detections">刷新</a>
      </div>
    </nav>
  </header>

  <div class="admin-page">
    <h2>检测记录管理</h2>

    <!-- =================== 筛选按钮 =================== -->
    <div class="filters">
      <button :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</button>
      <button :class="{ active: filter === 'processed' }" @click="filter = 'processed'">已处理</button>
      <button :class="{ active: filter === 'unprocessed' }" @click="filter = 'unprocessed'">未处理</button>
    </div>

    <!-- =================== 数据表格 =================== -->
    <table class="data-table" v-if="filteredRecords.length">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户</th>
          <th>图片</th>
          <th>标签</th>
          <th>置信度</th>
          <th>上传时间</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="r in filteredRecords" :key="r.id">
          <td>{{ r.id }}</td>
          <td>{{ r.username }}</td>

          <td>
            <img :src="backendUrl + r.image_path" class="preview" />
          </td>

          <td>{{ r.label }}</td>

          <td>{{ (r.confidence * 100).toFixed(1) }}%</td>

          <!-- ++ 3. 在模板中调用新创建的格式化函数，而不是直接显示 r.created_at ++ -->
          <td>{{ formatBeijingTime(r.created_at) }}</td>

          <!-- =================== 状态显示 =================== -->
          <td>
            <span v-if="r.is_processed && r.upload_status === 'uploaded'" class="status uploaded">
              已上传
            </span>
            <span v-if="r.is_processed && r.upload_status === 'skipped'" class="status skipped">
              已跳过
            </span>
            <span v-if="!r.is_processed" class="status not">
              未处理
            </span>
          </td>

          <!-- =================== 操作按钮 =================== -->
          <td>
            <button
              class="btn-upload"
              @click="process(r.id, 'upload')"
              :disabled="r.is_processed"
            >
              上传
            </button>

            <button
              class="btn-skip"
              @click="process(r.id, 'skip')"
              :disabled="r.is_processed"
            >
              不上传
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else>暂无数据</p>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import axios from "../api/axios";

// 你已经导入了 dayjs，非常好！
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

// ++ 1. 启用 day.js 插件 (这是关键步骤，必须要有) ++
dayjs.extend(utc);
dayjs.extend(timezone);

const backendUrl = "http://127.0.0.1:5000";
const records = ref([]);
const filter = ref("all"); // all / processed / unprocessed

// ++ 2. 创建一个将 GMT 时间转换为北京时间并格式化的函数 ++
const formatBeijingTime = (gmtDate) => {
  // 如果日期数据不存在或为空，返回一个占位符，防止程序报错
  if (!gmtDate) return 'N/A';
  return dayjs(gmtDate).tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
};


// ========== 加载数据 ==========
onMounted(async () => {
  const token = localStorage.getItem("token");

  try {
    const res = await axios.get(`${backendUrl}/api/admin/detections`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    records.value = res.data;
  } catch (err) {
    alert(err.response?.data?.msg || "加载失败");
  }
});

// ========== 根据筛选过滤数据 ==========
const filteredRecords = computed(() => {
  if (filter.value === "processed")
    return records.value.filter((r) => r.is_processed);
  if (filter.value === "unprocessed")
    return records.value.filter((r) => !r.is_processed);
  return records.value;
});

// ========== 处理记录的函数（你已有的代码，保持不变）==========
async function process(id, action) {
  const token = localStorage.getItem("token");

  try {
    const payload = {
      ids: [id],
      action: action,
    };

    const res = await axios.post(
      `${backendUrl}/api/admin/process_detection`,
      payload,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    alert(res.data.msg || "处理成功");

    const recordToUpdate = records.value.find(r => r.id === id);
    if (recordToUpdate) {
      recordToUpdate.is_processed = true;
      recordToUpdate.upload_status = action === 'upload' ? 'uploaded' : 'skipped';
    }

  } catch (error) {
    console.error("处理失败:", error.response?.data || error.message);
    alert(`操作失败: ${error.response?.data?.msg || '请检查网络或联系管理员'}`);
  }
}
</script>



<style scoped>
/* 顶部导航栏 */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #42b983;
  padding: 15px 0;
  z-index: 1000;
}

nav {
  display: flex;
  justify-content: flex-start;
  padding-left: 20px;
}

.nav {
  display: flex;
  gap: 20px;
}

.nav a {
  color: white;
  text-decoration: none;
  font-weight: bold;
  font-size: 16px;
}

.nav a:hover {
  text-decoration: underline;
}

/* 页面主体 */
.admin-page {
  padding: 20px;
  margin-top: 100px;
  text-align: center;
}

/* 筛选 */
.filters {
  margin: 15px 0;
}

.filters button {
  margin: 0 10px;
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid #42b983;
  background: white;
  cursor: pointer;
  transition: 0.2s;
}

.filters button.active,
.filters button:hover {
  background-color: #42b983;
  color: white;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.data-table th,
.data-table td {
  border: 1px solid #ddd;
  padding: 8px;
}

.preview {
  width: 100px;
  border-radius: 5px;
}

/* 状态标签 */
.status {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 13px;
}

.status.uploaded {
  background: #d4f8d4;
  color: #0b8a0b;
}

.status.skipped {
  background: #fff3cd;
  color: #b8860b;
}

.status.not {
  background: #f8d7da;
  color: #a30015;
}

/* 操作按钮 */
.btn-upload,
.btn-skip {
  margin: 3px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: white;
}

.btn-upload {
  background-color: #42b983;
}

.btn-skip {
  background-color: #888;
}

.btn-upload:disabled,
.btn-skip:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
