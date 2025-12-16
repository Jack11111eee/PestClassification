<template>
  <div class="register">
    <h2>注册</h2>
    <input v-model="username" placeholder="用户名"  @keyup.enter="register"/>
    <input v-model="password" type="password" placeholder="密码" @keyup.enter="register"/>
    <button @click="register">注册</button>
    <p>已有账号？<router-link to="/login">去登录</router-link></p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from '../api/axios'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const router = useRouter()

const register = async () => {
  try {
    await axios.post('auth/register', { username: username.value, password: password.value })
    alert('注册成功！请登录')
    router.push('/login')
  } catch (err) {
    alert(err.response.data.message)
  }
}
</script>

<style scoped>
.register {
  max-width: 400px;
  margin: 100px auto;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 10px;
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  text-align: center;
}
.register h2 {
  margin-bottom: 1.5rem;
  color: #42b983;
}

.register input,.register button{
  display: block;
  width: 100%;
  padding: 0.7rem;
  margin: 0.6rem 0;
  border-radius: 6px;
  box-sizing: border-box; 
}

.register input {
  border: 1px solid #ddd;
}

.register button {
  background: #42b983;
  color: #fff;
  border: none;
  font-size: 1rem;
  cursor: pointer;
}

.register button:hover {
  background-color: #369e6f;
}
</style>