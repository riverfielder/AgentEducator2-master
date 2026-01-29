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
          <h2>欢迎加入闻道学习平台</h2>
          <p>创建账户，开始您的智能学习之旅</p>
          
          <div class="features">
            <div class="feature">
              <div class="feature-icon"><i class="fas fa-book-reader"></i></div>
              <div class="feature-text">丰富的教学资源</div>
            </div>
            <div class="feature">
              <div class="feature-icon"><i class="fas fa-graduation-cap"></i></div>
              <div class="feature-text">个性化学习体验</div>
            </div>
            <div class="feature">
              <div class="feature-icon"><i class="fas fa-brain"></i></div>
              <div class="feature-text">智能知识图谱</div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="auth-form-container">
          <h1>创建账户</h1>
          <p class="welcome-text">填写以下信息完成注册</p>

          <form class="auth-form" @submit.prevent="handleRegister">
            <div class="form-group" :class="{ 'input-focus': focusedField === 'username', 'has-value': form.username }">
              <input
                type="text"
                id="username"
                v-model="form.username"
                placeholder="用户名"
                @focus="focusedField = 'username'"
                @blur="focusedField = ''"
                required
              />
              <label for="username">用户名</label>
              <div class="input-border"></div>
            </div>
            
            <div class="form-group" :class="{ 'input-focus': focusedField === 'email', 'has-value': form.email }">
              <input
                type="email"
                id="email"
                v-model="form.email"
                placeholder="电子邮箱"
                @focus="focusedField = 'email'"
                @blur="focusedField = ''"
                required
              />
              <label for="email">电子邮箱</label>
              <div class="input-border"></div>
            </div>
            
            <div class="form-group" :class="{ 'input-focus': focusedField === 'password', 'has-value': form.password }">
              <input
                :type="showPassword ? 'text' : 'password'"
                id="password"
                v-model="form.password"
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
            
            <div class="form-group role-selection">
              <div class="role-options">
                <div 
                  class="role-option" 
                  :class="{ 'active': form.role === 'student' }" 
                  @click="form.role = 'student'"
                >
                  <i class="fas fa-user-graduate role-icon"></i>
                  <span>学生</span>
                </div>
                <div 
                  class="role-option" 
                  :class="{ 'active': form.role === 'teacher' }" 
                  @click="form.role = 'teacher'"
                >
                  <i class="fas fa-chalkboard-teacher role-icon"></i>
                  <span>教师</span>
                </div>
              </div>
            </div>
            
            <div class="form-options">
              <label class="remember-me">
                <input type="checkbox" id="terms" v-model="form.agreeTerms" />
                <span class="checkmark"></span>
                我已阅读并同意服务条款
              </label>
            </div>
            
            <div v-if="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>
            
            <button 
              type="submit" 
              class="auth-button"
              :disabled="isLoading || !form.agreeTerms || !form.username || !form.email || !form.password"
            >
              <span v-if="!isLoading">注册</span>
              <div class="loader" v-else></div>
            </button>
          </form>
          
          <div class="auth-footer">
            <p>已有账户? <router-link to="/login">立即登录</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import userService from '../api/userService';

export default {
  name: 'Register',
  data() {
    return {
      form: {
        username: '',
        email: '',
        password: '',
        role: 'student',
        agreeTerms: false
      },
      focusedField: '', // 添加这个跟踪聚焦状态
      showPassword: false,
      isLoading: false,
      errorMessage: ''
    };
  },
  methods: {
    async handleRegister() {
      if (!this.validateForm()) {
        return;
      }

      this.isLoading = true;
      this.errorMessage = '';

      try {
        const response = await userService.register({
          username: this.form.username,
          email: this.form.email,
          password: this.form.password,
          role: this.form.role
        });

        if (response.data.code === 200) {
          // 注册成功，跳转到登录页
          this.$router.push('/login');
        } else {
          this.errorMessage = response.data.message || '注册失败，请稍后再试';
        }
      } catch (error) {
        console.error('注册失败:', error);
        this.errorMessage = error.message || '注册失败，请检查网络连接或稍后再试';
      } finally {
        this.isLoading = false;
      }
    },
    validateForm() {
      if (!this.form.username.trim()) {
        this.errorMessage = '请输入用户名';
        return false;
      }

      if (!this.form.email.trim()) {
        this.errorMessage = '请输入电子邮箱';
        return false;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.form.email)) {
        this.errorMessage = '请输入有效的电子邮箱地址';
        return false;
      }

      if (!this.form.password) {
        this.errorMessage = '请输入密码';
        return false;
      }

      if (this.form.password.length < 6) {
        this.errorMessage = '密码长度必须至少为6个字符';
        return false;
      }

      if (!this.form.agreeTerms) {
        this.errorMessage = '请同意服务条款';
        return false;
      }

      return true;
    }
  }
};
</script>

<style>
@import '../styles/auth.css';

/* 角色选择特有样式 */
.role-selection {
  margin: 20px 0;
}

.role-options {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.role-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f9fafb;
}

.role-option.active {
  border-color: #6366f1;
  background-color: rgba(99, 102, 241, 0.05);
}

.role-icon {
  font-size: 24px;
  margin-bottom: 10px;
  color: #6b7280;
}

.role-option.active .role-icon {
  color: #6366f1;
}

@media (max-width: 768px) {
  .role-options {
    flex-direction: column;
    gap: 10px;
  }
}
</style>

