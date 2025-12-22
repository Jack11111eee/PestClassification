<template>
  <div class="login-container">
    <div class="login-card">
      <!-- 装饰性图标 -->
      <div class="login-header">
        <div class="user-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
        <h2 class="login-title">用户登录</h2>
        <p class="login-subtitle">欢迎回来，请登录您的账户</p>
      </div>

      <!-- 表单区域 -->
      <div class="form-container">
        <div class="input-group">
          <div class="input-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>
          </div>
          <input 
            v-model="username" 
            placeholder="请输入用户名" 
            class="form-input"
            @keyup.enter="submit"
          />
        </div>

        <div class="input-group">
          <div class="input-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
            </svg>
          </div>
          <input 
            v-model="password" 
            type="password" 
            placeholder="请输入密码" 
            class="form-input"
            @keyup.enter="submit"
          />
        </div>

        <!-- 登录按钮 -->
        <button 
          @click="submit" 
          class="submit-btn"
          :class="{ 'submitting': isSubmitting }"
          :disabled="isSubmitting"
        >
          <span v-if="!isSubmitting">登录</span>
          <span v-else class="loading-dots">
            <span class="dot">.</span>
            <span class="dot">.</span>
            <span class="dot">.</span>
          </span>
        </button>

        <!-- 注册链接 -->
        <p class="register-link">
          还没有账号？
          <span @click="toRegister" class="register-text">立即注册</span>
        </p>

        <!-- 消息提示 -->
        <div 
          v-if="message" 
          class="message-box"
          :class="messageType"
        >
          <div class="message-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path v-if="messageType === 'error'" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              <path v-if="messageType === 'success'" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <span>{{ message }}</span>
        </div>
      </div>

      <!-- 底部装饰 -->
      <div class="login-footer">
        <div class="footer-line"></div>
        <span class="footer-text">Vue Login System</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/api/auth'

const router = useRouter()

const username = ref('')
const password = ref('')
const message = ref('')
const isSubmitting = ref(false)

// 根据消息内容判断消息类型
const messageType = computed(() => {
  if (message.value.includes('成功') || message.value.includes('欢迎')) {
    return 'success'
  } else if (message.value) {
    return 'error'
  }
  return ''
})

const submit = async () => {
  message.value = ''
  
  if (!username.value || !password.value) {
    message.value = '请输入用户名和密码'
    return
  }

  isSubmitting.value = true

  try {
    const res = await login(username.value, password.value)
    console.log('登录接口返回：', res.data)

    message.value = res.data.message || '登录成功'

    if (res.data.success) {
      // 1️⃣ 单独存 username（给接口用）
      localStorage.setItem('username', username.value)

      // 2️⃣ 存 user 对象（给角色 / UI 用）
      localStorage.setItem(
        'user',
        JSON.stringify({
          username: username.value,
          role: res.data.role || 'user'
        })
      )

      console.log('localStorage.username =', localStorage.getItem('username'))
      console.log('localStorage.user =', localStorage.getItem('user'))

      // 显示成功消息后跳转
      setTimeout(() => {
        router.push('/test')
      }, 1500)
    }
  } catch (e) {
    console.error('登录异常:', e)
    message.value = '登录失败，请检查用户名或密码'
  } finally {
    isSubmitting.value = false
  }
}

const toRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.login-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.login-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.35);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.user-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 36px;
}

.user-icon svg {
  width: 40px;
  height: 40px;
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.form-container {
  margin-bottom: 20px;
}

.input-group {
  position: relative;
  margin-bottom: 20px;
}

.input-icon {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #764ba2;
  z-index: 1;
}

.input-icon svg {
  width: 20px;
  height: 20px;
}

.form-input {
  width: 100%;
  padding: 15px 15px 15px 45px;
  border: 2px solid #e1e1e1;
  border-radius: 12px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #f8f9fa;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #764ba2;
  background: white;
  box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.1);
}

.form-input::placeholder {
  color: #999;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 10px;
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.submit-btn::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 5px;
  height: 5px;
  background: rgba(255, 255, 255, 0.5);
  opacity: 0;
  border-radius: 100%;
  transform: scale(1, 1) translate(-50%);
  transform-origin: 50% 50%;
}

.submit-btn:focus:not(:active)::after {
  animation: ripple 1s ease-out;
}

@keyframes ripple {
  0% {
    transform: scale(0, 0);
    opacity: 0.5;
  }
  100% {
    transform: scale(20, 20);
    opacity: 0;
  }
}

.loading-dots {
  display: inline-block;
}

.dot {
  opacity: 0;
  animation: dot-flash 1.5s infinite;
  font-size: 24px;
  line-height: 1;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-flash {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

.register-link {
  text-align: center;
  margin: 20px 0;
  color: #666;
  font-size: 14px;
}

.register-text {
  color: #764ba2;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 4px 8px;
  border-radius: 6px;
}

.register-text:hover {
  color: #667eea;
  background: rgba(118, 75, 162, 0.1);
  text-decoration: underline;
}

.message-box {
  padding: 12px 16px;
  border-radius: 10px;
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-box.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message-box.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.message-icon svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
}

.footer-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, #e1e1e1, transparent);
  margin-bottom: 15px;
}

.footer-text {
  color: #999;
  font-size: 12px;
  letter-spacing: 1px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    padding: 10px;
  }
  
  .login-card {
    padding: 30px 20px;
  }
  
  .login-title {
    font-size: 24px;
  }
}
</style>
