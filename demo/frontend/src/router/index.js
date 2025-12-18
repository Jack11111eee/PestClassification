import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Test from '@/views/Test.vue'
import Admin from '@/views/Admin.vue'
import Audit from '@/views/Audit.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/test',component:Test},
  { path: '/user_manage',component:Admin},
  { path: '/audit',component: Audit}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
