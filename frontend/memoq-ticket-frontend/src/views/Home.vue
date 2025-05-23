<template>
  <div class="home-page-wrapper">
    <!-- 背景图 -->
    <div class="background-image"></div>
    
    <!-- 内容区域 -->
    <v-container class="fill-height">
      <v-row justify="center" align="center">
        <v-col cols="12" md="8" lg="6">
          <!-- 欢迎卡片 -->
          <v-card class="welcome-card elevation-10 rounded-lg">
            <v-row no-gutters>
              <!-- 左侧信息区 -->
              <v-col cols="12" md="6" class="pa-6 d-flex flex-column justify-center">
                <div class="text-center mb-6">
                  <v-img
                    src="/assets/memoq_logo.webp"
                    alt="memoQ Logo"
                    height="60"
                    contain
                    class="mx-auto mb-4"
                  />
                  <h1 class="text-h4 font-weight-bold primary--text mb-2">memoQ 工单系统</h1>
                  <p class="text-subtitle-1 text-medium-emphasis">专业的本地化技术支持平台</p>
                </div>
                
                <p class="text-body-1 text-medium-emphasis mb-6">
                  欢迎使用 memoQ 工单系统。技术支持人员请在此登录，公司用户请使用专属链接访问。
                </p>
                
                <div class="d-flex flex-column gap-3">
                  <v-btn
                    color="primary"
                    size="large"
                    block
                    elevation="2"
                    @click="showLoginForm = true"
                  >
                    <v-icon start>mdi-login</v-icon>
                    技术支持登录
                  </v-btn>
                  
                  <v-btn
                    variant="outlined"
                    color="primary"
                    size="large"
                    block
                    @click="goToCompanyLogin"
                  >
                    <v-icon start>mdi-domain</v-icon>
                    公司用户入口
                  </v-btn>
                </div>
              </v-col>
              
              <!-- 右侧登录表单区 -->
              <v-col cols="12" md="6" class="login-form-col">
                <v-card-text v-if="showLoginForm" class="pa-6">
                  <h2 class="text-h5 font-weight-bold mb-4">技术支持登录</h2>
                  
                  <v-form
                    ref="loginFormRef"
                    v-model="validForm"
                    @submit.prevent="submitForm"
                  >
                    <v-text-field
                      v-model="loginForm.username"
                      label="用户名"
                      name="username"
                      prepend-inner-icon="mdi-account"
                      variant="outlined"
                      :rules="rules.username"
                      required
                      class="mb-3"
                    />

                    <v-text-field
                      v-model="loginForm.password"
                      label="密码"
                      name="password"
                      prepend-inner-icon="mdi-lock"
                      type="password"
                      variant="outlined"
                      :rules="rules.password"
                      required
                      class="mb-4"
                    />
                    
                    <v-alert
                      v-if="loginError"
                      type="error"
                      density="compact"
                      variant="tonal"
                      class="mb-4"
                    >
                      {{ loginError }}
                    </v-alert>
                    
                    <v-btn
                      type="submit"
                      color="primary"
                      block
                      size="large"
                      :loading="loading"
                      :disabled="!validForm"
                    >
                      登录
                    </v-btn>
                  </v-form>
                </v-card-text>
                
                <div v-else class="d-flex justify-center align-center fill-height pa-6">
                  <v-img
                    src="/assets/support_illustration.svg"
                    alt="技术支持插图"
                    max-height="250"
                    contain
                    class="mx-auto"
                  />
                </div>
              </v-col>
            </v-row>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';

export default {
  name: 'HomeView',
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const loginFormRef = ref(null);
    const validForm = ref(false);
    const loginError = ref(null);
    const loading = ref(false);
    const showLoginForm = ref(false);

    const loginForm = reactive({
      username: '',
      password: ''
    });

    const rules = reactive({
      username: [
        v => !!v || '请输入用户名'
      ],
      password: [
        v => !!v || '请输入密码'
      ]
    });

    const submitForm = async () => {
      loginError.value = null;
      if (!validForm.value) return;

      loading.value = true;
      try {
        // 构建登录请求数据
        const loginData = {
          username: loginForm.username,
          password: loginForm.password
        };
        
        // 调用登录API
        const success = await authStore.login(loginData);
        
        if (success) {
          // 根据用户角色跳转到不同页面
          redirectBasedOnRole();
        }
      } catch (error) {
        console.error('登录失败:', error);
        loginError.value = error.message || '登录失败，请检查用户名和密码';
      } finally {
        loading.value = false;
      }
    };

    // 根据用户角色跳转到相应页面
    const redirectBasedOnRole = () => {
      const role = authStore.userRole;
      
      if (role === 'system_admin' || role === 'technical_support_admin') {
        router.push('/admin');
      } else if (role === 'support') {
        router.push('/support');
      } else {
        // 普通用户直接跳转到工单提交页面
        router.push('/submit-ticket');
      }
    };

    const goToCompanyLogin = () => {
      // 显示公司登录对话框或跳转到公司登录页面
      router.push('/company-login');
    };

    return {
      loginForm,
      rules,
      loading,
      loginFormRef,
      validForm,
      loginError,
      submitForm,
      showLoginForm,
      goToCompanyLogin
    };
  }
};
</script>

<style scoped>
.home-page-wrapper {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.background-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url('/assets/localization_bg.jpg');
  background-size: cover;
  background-position: center;
  filter: brightness(0.8);
  z-index: -1;
}

.welcome-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.login-form-col {
  background-color: #f5f5f5;
  border-left: 1px solid rgba(0, 0, 0, 0.12);
}

@media (max-width: 960px) {
  .login-form-col {
    border-left: none;
    border-top: 1px solid rgba(0, 0, 0, 0.12);
  }
}
</style>

