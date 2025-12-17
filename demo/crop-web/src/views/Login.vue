<template>
  <div class="container">
    <h2>用户登录</h2>

    <input v-model="username" placeholder="用户名" />
    <input v-model="password" type="password" placeholder="密码" />
    
    <button @click="submit">登录</button>

    <p class="switch" @click="toRegister">
      没有账号？去注册
    </p>

    <p class="result">{{ message }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'

const router = useRouter()

const username = ref('')
const password = ref('')
const message = ref('')

const submit = async () => {
  message.value = ''
  try {
    const res = await login(username.value, password.value)
    message.value = res.data.message

    if (res.data.success) {
      // 以后这里跳首页
      console.log('登录成功')
      router.push('/test')
    }
  } catch (e) {
    message.value = '登录失败'
  }
}

const toRegister = () => {
  router.push('/register')
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
