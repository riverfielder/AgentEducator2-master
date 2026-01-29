<!-- Login.vue -->
<template>
  <div class="auth-container">
    <div class="waves-container">
      <div class="wave wave1"></div>
      <div class="wave wave2"></div>
      <div class="wave wave3"></div>
    </div>

    <div class="auth-box">
      <div class="left-panel">
        <div class="platform-intro">
          <div class="logo-container">
            <div class="logo">闻道</div>
            <div class="logo-particles">
              <span></span><span></span><span></span>
              <span></span><span></span><span></span>
            </div>
          </div>
          <h2>大模型辅助智能化学习平台</h2>
          <p>探索人工智能辅助教学的无限可能</p>
          
          <div class="features">
            <div class="feature">
              <div class="feature-icon"><i class="fas fa-robot"></i></div>
              <div class="feature-text">智能知识图谱规划</div>
            </div>
            <div class="feature">
              <div class="feature-icon"><i class="fas fa-chart-line"></i></div>
              <div class="feature-text">实时学习数据分析</div>
            </div>
            <div class="feature">
              <div class="feature-icon"><i class="fas fa-comments"></i></div>
              <div class="feature-text">AI辅助答疑解惑</div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="auth-form-container">
          <h1>登录账户</h1>
          <p class="welcome-text">欢迎回来，请输入您的邮箱和密码</p>

          <form class="auth-form" @submit.prevent="handleLogin">
            <div class="form-group" :class="{ 'input-focus': focusedField === 'email', 'has-value': email }">
              <input
                  type="email"
                  id="email"
                  v-model="email"
                  placeholder="邮箱"
                  @focus="focusedField = 'email'"
                  @blur="focusedField = ''"
                  required
              />
              <label for="email">邮箱</label>
              <div class="input-border"></div>
            </div>

            <div class="form-group" :class="{ 'input-focus': focusedField === 'password', 'has-value': password }">
              <input
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  v-model="password"
                  placeholder="密码"
                  @focus="focusedField = 'password'"
                  @blur="focusedField = ''"
                  required
              />
              <label for="password">密码</label>
              <div class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </div>
              <div class="input-border"></div>
            </div>

            <div class="form-options">
              <label class="remember-me">
                <input type="checkbox" v-model="rememberMe" />
                <span class="checkmark"></span>
                记住我
              </label>
            </div>

            <button
                type="submit"
                class="auth-button"
                :disabled="loading || !email || !password"
            >
              <span v-if="!loading">登录</span>
              <div class="loader" v-else></div>
            </button>
          </form>

          <div v-if="errorMsg" class="error-message">
            {{ errorMsg }}
          </div>

          <div class="auth-footer">
            <p>没有账户? <router-link to="/register">立即注册</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import userService from '../api/userService';
import { useUserStore } from '../stores/userStore';

export default {
  name: 'Login',
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  data() {
    return {
      email: '',
      password: '',
      rememberMe: false,
      loading: false,
      errorMsg: '',
      focusedField: '',
      showPassword: false,
    };
  },
  mounted() {
    const savedEmail = localStorage.getItem('wendao_email');
    const savedRememberMe = localStorage.getItem('wendao_rememberMe');

    if (savedRememberMe === 'true' && savedEmail) {
      this.email = savedEmail;
      this.rememberMe = true;
    }

    this.animateWaves();
    this.animateParticles();
  },
  methods: {
    animateWaves() {
      const waves = document.querySelectorAll('.wave');
      waves.forEach((wave, index) => {
        const delay = index * 0.2;
        wave.style.animationDelay = `${delay}s`;
      });
    },
    animateParticles() {
      const particles = document.querySelectorAll('.logo-particles span');
      particles.forEach((particle, index) => {
        const delay = Math.random() * 2;
        const duration = 2 + Math.random() * 3;
        particle.style.animationDelay = `${delay}s`;
        particle.style.animationDuration = `${duration}s`;
      });
    },
    async handleLogin() {
      if (!this.email || !this.password) {
        this.errorMsg = '请输入邮箱和密码';
        return;
      }

      this.loading = true;
      this.errorMsg = '';

      try {
        const response = await userService.login(this.email, this.password);

        if (response.data.code === 200) {
          const userData = response.data.data;
          
          // 保存token
          localStorage.setItem('wendao_token', userData.token);
          
          // 立即保存用户角色信息，确保路由守卫能够正确识别
          localStorage.setItem('wendao_user_role', userData.role);

          // 获取完整的用户信息
          const userInfoResponse = await userService.getUserInfo();
          if (userInfoResponse.data.code === 200) {
            // 使用完整的用户信息更新store
            this.userStore.updateUserInfo(userInfoResponse.data.data);
          } else {
            // 如果获取完整信息失败，至少保存基本登录信息
            this.userStore.updateUserInfo({
              id: userData.id,
              name: userData.name,
              role: userData.role,
              avatar: userData.avatar
            });
          }

          if (this.rememberMe) {
            localStorage.setItem('wendao_email', this.email);
            localStorage.setItem('wendao_rememberMe', 'true');
          } else {
            localStorage.removeItem('wendao_email');
            localStorage.removeItem('wendao_rememberMe');
          }

          this.showLoginSuccess();

          setTimeout(() => {
            if (userData.role === 'teacher') {
              this.$router.push('/teacherHome');
            } else {
              this.$router.push('/');
            }
          }, 1000);
        } else {
          this.errorMsg = response.data.message || '登录失败，请检查邮箱和密码';
        }
      } catch (error) {
        console.error('登录请求错误:', error);
        this.errorMsg = error.message || '网络错误或服务器未响应';
      } finally {
        this.loading = false;
      }
    },
    showLoginSuccess() {
      const authBox = document.querySelector('.auth-box');
      authBox.classList.add('login-success');

      setTimeout(() => {
        authBox.classList.remove('login-success');
      }, 1000);
    }
  }
};
</script>

<style>
@import '../styles/auth.css';
</style>