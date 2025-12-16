// frontend/vite.config.js

import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // === 新增的核心配置：服务器和代理 ===
  server: {
    host: '0.0.0.0', // 允许通过 IP 地址访问
    port: 5174,      // 前端开发服务器端口
    proxy: {
      // 代理 API 请求
      '/api': {
        target: 'http://127.0.0.1:5000', // 指向你的 Flask 后端服务
        changeOrigin: true, // 必须设置为 true
      },
      // 代理静态文件（如上传的图片）请求
      '/static': {
        target: 'http://127.0.0.1:5000', // 同样指向 Flask 后端
        changeOrigin: true, // 必须设置为 true
      }
    }
  }
})
