<template>
  <div class="login">
    <h2>登录</h2>
    <input v-model="username" placeholder="用户名"  @keyup.enter="login" />
    <input v-model="password" type="password" placeholder="密码"  @keyup.enter="login" />
    <button @click="login" >登录</button>
    <p>没有账号？<router-link to="/register">去注册</router-link></p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from '../api/axios'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const router = useRouter()

const login = async () => {
  try {
    const res = await axios.post('auth/login', {
      username: username.value,
      password: password.value
    })
    localStorage.setItem('token', res.data.token)
    router.push('/home')
  } catch (err) {
    alert(err.response?.data?.message || '登录失败')
  }
}
</script>

<style scoped>
.login {
  max-width: 400px;
  margin: 100px auto;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 10px;
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  text-align: center;
}

.login h2 {
  margin-bottom: 1.5rem;
  color: #42b983;
}

.login input, .login button {
  display: block;
  width: 100%;
  padding: 0.7rem;
  margin: 0.6rem 0;
  border-radius: 6px;
  box-sizing: border-box;  /* 这行很重要，确保 padding 和 border 包括在宽度计算内 */
}

.login input {
  border: 1px solid #ddd;
}

.login button {
  background: #42b983;
  color: #fff;
  border: none;
  font-size: 1rem;
  cursor: pointer;
}

.login button:hover {
  background: #369e6f;
}
</style>