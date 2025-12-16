// // src/stores/userStore.js

// import { defineStore } from 'pinia'
// import router from '@/router' // 引入 router

// export const useUserStore = defineStore('user', {
//   // 1. 数据中心：定义 state
//   state: () => ({
//     token: null,
//     username: null,
//     role: null,
//   }),

//   // 2. 计算属性：定义 getters
//   getters: {
//     // !!state.token 会将 token 字符串（非空）转为 true，将 null 或空字符串转为 false
//     isLoggedIn: (state) => !!state.token,
//     isAdmin: (state) => state.role === 'admin',
//     // 用于在导航栏显示 "当前用户：xxx"
//     currentUserDisplay: (state) => state.username || '未登录',
//   },

//   // 3. 方法：定义 actions
//   actions: {
//     // 登录成功后，调用这个 action 来保存用户信息
//     setUser(userData) {
//       this.token = userData.access_token;
//       this.username = userData.username;
//       this.role = userData.role;
//     },

//     // 退出登录时，调用这个 action
//     logout() {
//       // 清空 state 中的数据
//       this.token = null;
//       this.username = null;
//       this.role = null;

//       // Pinia 持久化插件不会自动清空 localStorage，所以我们手动清一下
//       // 注意：'user' 必须和 defineStore 的第一个参数 'user' 完全一样
//       localStorage.removeItem('user');

//       // 跳转到登录页
//       router.push('/login');
//     },
//   },

//   // 4. 开启持久化！
//   persist: true,
// })
