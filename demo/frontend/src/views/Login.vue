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
    // 调用后端登录接口
    const res = await login(username.value, password.value)

    console.log('登录接口返回：', res.data)

    message.value = res.data.message

    if (res.data.success) {
      // ⭐⭐⭐ 关键：保存当前登录用户信息
      localStorage.setItem(
        'user',
        JSON.stringify({
          username: username.value,
          role: res.data.role
        })
      )

      console.log('已保存 user 到 localStorage:', localStorage.getItem('user'))

      // 跳转到首页 / 病虫害识别页
      router.push('/test')
    }
  } catch (e) {
    console.error('登录异常:', e)
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
