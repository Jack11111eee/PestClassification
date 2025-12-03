import { createApp } from 'vue'
import App from './App.vue'//主组件
import router from './router'//路由配置

createApp(App).use(router).mount('#app')