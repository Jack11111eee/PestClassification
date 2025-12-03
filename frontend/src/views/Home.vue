<!-- frontend/src/views/Home.vue (最终版) -->
<template>
  <div class="home">
    <!-- 顶部导航栏 -->
    <header>
      <nav>
        <div class="nav-left">
          <!-- 为了单页应用体验，将 a href 改为 router-link to -->
          <router-link to="/home">主页</router-link>
          
          <!-- ++ 1. 在这里添加新链接 ++ -->
          <router-link to="/my-submissions">我的提交</router-link>

          <!-- 管理员链接保持不变 -->
          <router-link v-if="user?.role === 'admin'" to="/admin/detections">管理检测记录</router-link>

          <router-link v-if="user?.role === 'admin'" to="/admin/users">用户管理</router-link>
        </div>

        <div class="nav-right">
          <p>当前用户：{{ user?.username || "未登录" }}</p>
          <button @click="logout">退出登录</button>
        </div>
      </nav>
    </header>

    <!-- 页面主体 (这部分内容保持不变) -->
    <div class="content">
      <h2>欢迎来到主页</h2>
      <p>这里是主页的主要内容</p>

      <hr />

      <!-- 上传与识别 -->
      <div class="upload-section">
        <h3>图片识别</h3>
        <input type="file" multiple accept="image/*" @change="handleFiles" />
        <button @click="uploadImages" :disabled="!selectedFiles.length">
          上传并识别
        </button>
      </div>

      <!-- 识别结果 -->
      <div v-if="results.length" class="results-section">
        <h3>识别结果</h3>

        <div v-if="results.length > 1" class="pagination">
          <button @click="prev" :disabled="currentIndex === 0">上一张</button>
          <span>{{ currentIndex + 1 }} / {{ results.length }}</span>
          <button @click="next" :disabled="currentIndex === results.length - 1">
            下一张
          </button>
        </div>

        <div class="result-display">
          <img
            :src="backendUrl + results[currentIndex].image_url"
            class="preview-image"
          />
          <p class="result-text">
            识别结果：{{ results[currentIndex].class_name }}（置信度：
            {{ (results[currentIndex].confidence * 100).toFixed(2) }}%）
          </p>

          <div class="label-selection">
            <select v-model="selectedLabel">
              <option disabled value="">请选择标签</option>
              <option v-for="l in availableLabels" :key="l">{{ l }}</option>
            </select>
            <button @click="saveLabel" :disabled="!selectedLabel">
              保存标签
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 你的 <script setup> 部分完全正确，无需任何修改！
// 所以我们直接保持原样。
import { ref, onMounted } from "vue";
import axios from "../api/axios";
import { useRouter } from "vue-router";
import { jwtDecode } from "jwt-decode";

const router = useRouter();

// ===================== 用户信息获取 =====================
const user = ref(null);
const token = localStorage.getItem("token");

onMounted(() => {
  if (!token) {
    // 如果没有token，根据你的路由设置，应该强制跳转到登录
    router.push("/login");
    return;
  };

  try {
    const decoded = jwtDecode(token);
    const expired = decoded.exp < Date.now() / 1000;
    if (!expired) {
      user.value = {
        id: decoded.sub,
        username: decoded.username,
        role: decoded.role,
      };
    } else {
      // token 过期也应登出
      logout();
    }
  } catch (e) {
    console.error("Token 解码失败", e);
    logout(); // 解码失败也登出
  }
});

// ===================== 退出登录 =====================
function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user"); // 以防万一，也删除user
  router.push("/login");
}

// ===================== 上传图片并识别 =====================
const backendUrl = "http://127.0.0.1:5000";
const selectedFiles = ref([]);
const results = ref([]);
const currentIndex = ref(0);

function handleFiles(e) {
  selectedFiles.value = Array.from(e.target.files);
}

async function uploadImages() {
  const form = new FormData();
  selectedFiles.value.forEach((file) => form.append("images", file));

  try {
    const res = await axios.post(`/test/upload`, form, { // baseURL 已配置，可以省略
      headers: { "Content-Type": "multipart/form-data" },
    });
    results.value = res.data.results;
    currentIndex.value = 0;
  } catch(error) {
    console.error("上传失败:", error);
    alert("图片上传或识别失败，请稍后重试。");
  }
}

// ===================== 分页 =====================
function prev() {
  if (currentIndex.value > 0) currentIndex.value--;
}
function next() {
  if (currentIndex.value < results.value.length - 1) currentIndex.value++;
}

// ===================== 保存标签 =====================
const availableLabels = ["苹果黑腐病", "苹果雪松锈病", "苹果 - 健康", "苹果黑星病", "蓝莓 - 健康", "樱桃 - 健康", "樱桃白粉病", "玉米普通锈病", "玉米灰斑病", "玉米 - 健康", "玉米大斑病（北方叶枯病）", "葡萄黑腐病", "葡萄埃斯卡病（黑麻疹病）", "葡萄 - 健康", "葡萄叶枯病（伊斯 ariopsis 属）", "柑橘黄龙病", "桃细菌性斑点病", "桃 - 健康", "甜椒细菌性斑点病", "甜椒 - 健康", "马铃薯早疫病", "马铃薯 - 健康", "马铃薯晚疫病", "树莓 - 健康", "大豆 - 健康", "南瓜白粉病", "草莓 - 健康", "草莓叶焦病", "番茄细菌性斑点病", "番茄早疫病", "番茄 - 健康", "番茄晚疫病", "番茄叶霉病", "番茄花叶病毒病", "番茄 Septoria 叶斑病", "番茄靶斑病", "番茄二斑叶螨", "番茄黄化曲叶病毒病", "小麦冠根腐病", "小麦 - 健康", "小麦叶锈病", "小麦散黑穗病"];
const selectedLabel = ref("");

async function saveLabel() {
  if (!selectedLabel.value) {
    alert("请先选择一个标签！");
    return;
  }
  
  const currentResult = results.value[currentIndex.value];

  const payload = {
    image_path: currentResult.image_url,
    label: selectedLabel.value,
    confidence: currentResult.confidence,
  };

  try {
    // baseURL 已配置，可以省略
    const res = await axios.post(`/detection/save`, payload);
    alert(res.data.msg || "保存成功");
    selectedLabel.value = ""; 
  } catch (error) {
    console.error("保存失败:", error.response?.data || error.message);
    alert(`保存失败: ${error.response?.data?.msg || '请检查网络或联系管理员'}`);
  }
}
</script>

<style scoped>
/* 你的样式保持不变 */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #42b983;
  padding: 10px 0;
  z-index: 1000;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.nav-left {
  display: flex;
  gap: 20px;
}
/* 确保 router-link 样式和 a 标签一致 */
.nav-left a, .nav-left .router-link-active {
  color: white;
  text-decoration: none;
  font-weight: bold;
  font-size: 16px;
}

.nav-left a:hover, .nav-left .router-link-active:hover {
  text-decoration: underline;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
}

.nav-right p {
  margin: 0;
  font-size: 14px;
}

.nav-right button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.nav-right button:hover {
  background-color: #369e6f;
}

.content {
  text-align: center;
  margin-top: 100px; /* 留出固定导航栏的高度 */
}

/* ... 页面其余部分的样式保持不变 ... */
.upload-section {
  margin: 20px 0;
}

.upload-section input {
  margin-bottom: 10px;
}

.upload-section button {
  margin-left: 10px;
  padding: 0.4rem 1rem;
  border: none;
  background-color: #42b983;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

.upload-section button:hover {
  background-color: #369e6f;
}

.results-section {
  margin-top: 30px;
}

.result-display {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-image {
  max-width: 300px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  margin-bottom: 10px;
}

.result-text {
  font-size: 1.1rem;
  font-weight: bold;
}

.pagination {
  margin-bottom: 10px;
}

.pagination button {
  margin: 0 5px;
  padding: 0.3rem 0.8rem;
  border: none;
  background-color: #42b983;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.label-selection {
  margin-top: 10px;
}

.label-selection select {
  padding: 0.3rem 0.6rem;
  border-radius: 5px;
  border: 1px solid #ccc;
  margin-right: 10px;
}

.label-selection button {
  padding: 0.3rem 0.8rem;
  border: none;
  background-color: #42b983;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

.label-selection button:hover {
  background-color: #369e6f;
}

.label-selection button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
