<template>
  <div class="container">
    <h2>用户注册</h2>

    <input v-model="username" placeholder="用户名" />
    <input v-model="password" type="password" placeholder="密码" />

    <button @click="submit">注册</button>

    <p class="switch" @click="toLogin">
      已有账号？去登录
    </p>

    <p class="result">{{ message }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'

const router = useRouter()

const username = ref('')
const password = ref('')
const message = ref('')

const submit = async () => {
  message.value = ''
  try {
    const res = await register(username.value, password.value)
    message.value = res.data.message

    if (res.data.success) {
      // ✅ 注册成功 → 跳转登录页
      setTimeout(() => {
        router.push('/login')
      }, 800)
    }
  } catch (e) {
    message.value = '注册失败'
  }
}

const toLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.container {
  width: 300px;
  margin: 100px auto;
}

input {
  display: block;
  width: 100%;
  margin-bottom: 10px;
  padding: 6px;
}

button {
  width: 100%;
  padding: 6px;
}

.switch {
  margin-top: 10px;
  color: blue;
  cursor: pointer;
}

.result {
  margin-top: 10px;
  color: green;
}
</style>
