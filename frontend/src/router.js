// frontend/src/router.js (修改后)
import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import Home from './views/Home.vue'
// ++ 1. 导入新的 "我的提交" 组件 ++
import MySubmissions from './views/MySubmissions.vue'
import AdminUsers from './views/AdminUsers.vue';

const routes = [
  { path: '/', component: Login },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  // 我们也为 Home 页面添加 meta 标记，因为它通常也需要登录
  { path: '/home', component: Home, meta: { requiresAuth: true } }, 

  // 这是你已有的管理员路由
  {
    path: '/admin/detections',
    name: 'AdminDetections',
    component: () => import('./views/AdminDetections.vue'),
    // 管理员页面肯定需要登录，并且需要管理员权限
    meta: { requiresAuth: true, requiresAdmin: true } 
  },

  // ++ 2. 添加新的 "我的提交" 路由规则 ++
  {
    path: '/my-submissions',
    name: 'MySubmissions',
    component: MySubmissions,
    meta: { requiresAuth: true } // 这个 meta 字段是关键
  },

  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: AdminUsers,
    meta: { requiresAdmin: true } // <-- 关键：确保只有管理员能访问
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ++ 3. 添加全局导航守卫 (非常重要！) ++
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user')); // 假设用户信息也存在 localStorage

  // 检查路由是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!token) {
      // 如果没有 token，重定向到登录页
      next({ path: '/login' });
    } else {
      // 检查是否需要管理员权限
      if (to.matched.some(record => record.meta.requiresAdmin)) {
        
          next(); // 用户是管理员，允许访问
        
      } else {
        next(); // 路由只需要普通登录，用户有 token，允许访问
      }
    }
  } else {
    next(); // 路由不需要认证，直接放行
  }
});

export default router
