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
            :src="results[currentIndex].preview_url"
            class="preview-image"
          />
          <p class="result-text">
            识别结果：{{ translateClassName(results[currentIndex].class_name) }}（置信度：
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

// 翻译函数 前端的中英文映射
const translationMap = {
  'Apple_Black_Rot': '苹果黑腐病',
  'Apple_Cedar_Apple_Rust': '苹果雪松锈病',
  'Apple_healthy': '苹果-健康',
  'Apple_Scab': '苹果黑星病',
  'Blueberry_healthy': '蓝莓-健康',
  'Cherry_healthy': '樱桃-健康',
  'Cherry_Powdery_Mildew': '樱桃白粉病',
  'Corn_Common_Rust': '玉米普通锈病',
  'Corn_Gray_Leaf_Spot': '玉米灰斑病',
  'Corn_healthy': '玉米-健康',
  'Corn_Northern_Leaf_Blight': '玉米大斑病',
  'Grape_Black_Rot': '葡萄黑腐病',
  'Grape_Esca_Black_Measles': '葡萄埃斯卡病',
  'Grape_healthy': '葡萄-健康',
  'Grape_Leaf_Blight_Isariopsis': '葡萄叶枯病',
  'Orange_Haunglongbing_Citrus_Greening': '柑橘黄龙病',
  'Peach_Bacterial_Spot': '桃细菌性斑点病',
  'Peach_healthy': '桃-健康',
  'Pepper_Bell_Bacterial_Spot': '甜椒细菌性斑点病',
  'Pepper_Bell_healthy': '甜椒-健康',
  'Potato_Early_Blight': '马铃薯早疫病',
  'Potato_healthy': '马铃薯-健康',
  'Potato_Late_Blight': '马铃薯晚疫病',
  'Raspberry_healthy': '树莓-健康',
  'Soybean_healthy': '大豆-健康',
  'Squash_Powdery_Mildew': '南瓜白粉病',
  'Strawberry_healthy': '草莓-健康',
  'Strawberry_Leaf_Scorch': '草莓叶焦病',
  'Tomato_Bacterial_Spot': '番茄细菌性斑点病',
  'Tomato_Early_Blight': '番茄早疫病',
  'Tomato_healthy': '番茄-健康',
  'Tomato_Late_Blight': '番茄晚疫病',
  'Tomato_Leaf_Mold': '番茄叶霉病',
  'Tomato_Mosaic_Virus': '番茄花叶病毒病',
  'Tomato_Septoria_Leaf_Spot': '番茄Septoria叶斑病',
  'Tomato_Target_Spot': '番茄靶斑病',
  'Tomato_Two_Spotted_Spider_Mite': '番茄二斑叶螨',
  'Tomato_Yellow_Leaf_Curl_Virus': '番茄黄化曲叶病毒病',
  'Wheat_Crown_and_Root_Rot': '小麦冠根腐病',
  'Wheat_healthy': '小麦-健康',
  'Wheat_Leaf_Rust': '小麦叶锈病',
  'Wheat_Loose_Smut': '小麦散黑穗病'
};

function translateClassName(englishName) {
  // 尝试在字典里查找，如果找到了就返回中文，找不到就返回原始英文名
  return translationMap[englishName] || englishName;
}

// ===================== 上传图片并识别 =====================
const selectedFiles = ref([]);
const previewUrls = ref([]); // <--- 新增：用于存储所有文件的预览URL
const results = ref([]);
const currentIndex = ref(0);

// 修改 handleFiles 函数
function handleFiles(e) {
  // 清空旧数据
  selectedFiles.value = [];
  results.value = [];
  
  // 释放之前可能创建的URL，防止内存泄漏
  previewUrls.value.forEach(url => URL.revokeObjectURL(url));
  previewUrls.value = [];

  const files = Array.from(e.target.files);
  if (files.length > 0) {
    selectedFiles.value = files;
    // 为每一个选中的文件创建预览URL
    previewUrls.value = files.map(file => URL.createObjectURL(file));
  }
}

async function uploadImages() {
  const form = new FormData();
  selectedFiles.value.forEach((file) => form.append("images", file)); // 注意：你的后端需要能处理多文件，字段名要对应
  try {
    // 假设你的后端接口能处理多文件并按顺序返回结果
    const res = await axios.post(`/test/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    // --- 关键修改在这里 ---
    // res.data.results 是后端返回的识别结果数组
    // previewUrls.value 是我们前端自己生成的预览URL数组
    // 我们将它们合并成一个新的、更完整的结果数组
    results.value = res.data.results.map((result, index) => {
      return {
        ...result, // 包含后端返回的 class_name, confidence 等
        preview_url: previewUrls.value[index] // <--- 新增：添加我们自己的预览URL
      };
    });
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
/* ========== 顶部导航 ========== */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #42b983;
  padding: 14px 0;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  z-index: 1000;
}

nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 28px;
}

.nav-left {
  display: flex;
  gap: 24px;
}

.nav-left a,
.nav-left .router-link-active {
  color: white;
  text-decoration: none;
  font-weight: 600;
  font-size: 17px;
  padding: 6px 10px;
  border-radius: 6px;
  transition: 0.2s;
}

.nav-left a:hover,
.nav-left .router-link-active:hover {
  background-color: rgba(255,255,255,0.18);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
}

.nav-right button {
  background-color: white;
  color: #42b983;
  border: none;
  padding: 0.45rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: 0.2s;
}

.nav-right button:hover {
  background-color: #e8f8f0;
}

/* ========== 页面主体 ========== */
.content {
  margin-top: 110px;
  text-align: center;
  padding: 0 20px;
}

h2 {
  font-size: 26px;
  margin-bottom: 6px;
}

hr {
  margin: 30px auto;
  width: 80%;
  border: 0;
  border-top: 1px solid #ccc;
}

/* ========== 上传卡片 ========== */
.upload-section {
  margin: 30px auto;
  width: 380px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.12);
}

.upload-section h3 {
  margin-bottom: 12px;
  font-size: 20px;
}

.upload-section input {
  margin: 10px 0;
}

.upload-section button {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 0.45rem 1.2rem;
  border-radius: 6px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: 0.2s;
}

.upload-section button:hover {
  background-color: #369e6f;
}

/* ========== 结果区域 ========== */
.results-section {
  margin-top: 40px;
}

.result-display {
  width: 420px;
  margin: 20px auto;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.12);
}

.preview-image {
  max-width: 320px;
  border-radius: 10px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

.result-text {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 14px;
}

/* 分页按钮 */
.pagination {
  margin-bottom: 10px;
}

.pagination button {
  padding: 0.35rem 0.9rem;
  border: none;
  border-radius: 6px;
  background-color: #42b983;
  color: white;
  cursor: pointer;
  transition: 0.2s;
}

.pagination button:hover {
  background-color: #369e6f;
}

.pagination button:disabled {
  background-color: #bbb;
}

/* 标签选择 */
.label-selection {
  margin-top: 16px;
}

.label-selection select {
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  margin-right: 12px;
  min-width: 160px;
}

.label-selection button {
  padding: 0.4rem 1rem;
  border: none;
  background-color: #42b983;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}

.label-selection button:hover {
  background-color: #369e6f;
}

.label-selection button:disabled {
  background-color: #ccc;
}
</style>
