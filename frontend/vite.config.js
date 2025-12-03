import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
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
  // --- 从这里开始是新增的内容 ---
  server: {
    // 这个 host:'0.0.0.0' 是为了让你在自己电脑上用 IP 地址访问，
    // 我在服务器上运行时，也是必须的。
    host: '0.0.0.0', 
    
    proxy: {
      // 我们约定，所有发往后端的请求，路径都以 '/api' 开头
      '/api': {
        // 后端服务实际的地址
        target: 'http://127.0.0.1:5000',

        // 必须设置为 true，不然会请求失败
        changeOrigin: true,

        // 这个是可选的，意思是把请求路径中的 /api 去掉，
        // 比如前端请求 /api/login，代理后会变成 /login 再发给后端
        //rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  }
  // --- 新增内容到这里结束 ---
})
