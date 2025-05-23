<template>
  <v-container fluid class="login-page-wrapper fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>
              <img
                :src="companyDetails && companyDetails.logo_url ? companyDetails.logo_url : '/img/memoq_logo_placeholder.png'"
                alt="Logo"
                style="max-height: 40px; margin-right: 10px; vertical-align: middle;"
              >
              <span style="vertical-align: middle;">{{ pageTitle }}</span>
            </v-toolbar-title>
          </v-toolbar>

          <v-card-text>
            <div class="login-form-section">
              <div class="text-h6 mb-2 text-center" v-if="companySlug">账号登录</div>
              <v-form @submit.prevent="handleLogin">
                <v-text-field
                  label="用户名或邮箱"
                  v-model="credentials.username"
                  prepend-icon="mdi-account"
                  type="text"
                  required
                  :error-messages="authErrorField"
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                ></v-text-field>
                <v-text-field
                  label="密码"
                  v-model="credentials.password"
                  prepend-icon="mdi-lock"
                  type="password"
                  required
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                ></v-text-field>
                <v-btn color="primary" type="submit" block :loading="loading">
                  登录
                </v-btn>
                <v-alert v-if="authErrorAlert" type="error" dense class="mt-3">
                  {{ authErrorAlert }}
                </v-alert>
              </v-form>
            </div>

            <div v-if="!companySlug" class="mt-4 text-caption text-center">
              此登录页面供支持人员使用。公司用户请使用其专用的登录URL。
            </div>

            <div v-if="companySlug && activeSsoOptions.length > 0" class="sso-login-section mt-6">
              <v-divider class="my-4">
                <span class="px-2 text-overline">或通过以下方式继续</span>
              </v-divider>
              
              <v-btn
                v-if="defaultSsoProviderDetails"
                @click="handleSsoLogin(defaultSsoProviderDetails.platform)"
                :color="defaultSsoProviderDetails.color || 'grey-darken-1'"
                block
                large
                class="mb-3 default-sso-btn"
                variant="elevated"
                height="48"
              >
                <v-icon left class="mr-2">{{ defaultSsoProviderDetails.icon }}</v-icon>
                通过 {{ defaultSsoProviderDetails.name }} 登录 (默认)
              </v-btn>

              <div 
                class="other-sso-options"
                :class="{ 'd-flex flex-wrap justify-center ga-2': otherSsoProvidersDetails.length > 0 }"
                >
                <v-btn
                  v-for="option in otherSsoProvidersDetails"
                  :key="option.platform"
                  @click="handleSsoLogin(option.platform)"
                  :color="option.color || 'grey-lighten-1'"
                  class="sso-option-btn"
                  :block="otherSsoProvidersDetails.length === 1 && !defaultSsoProviderDetails"
                  :class="{'flex-grow-1': otherSsoProvidersDetails.length > 1}"
                  variant="outlined"
                  height="44"
                >
                  <v-icon left class="mr-1">{{ option.icon }}</v-icon>
                  {{ option.name }}
                </v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import api from '@/api';

const route = useRoute();
const authStore = useAuthStore();

const credentials = ref({ username: '', password: '' });
const loading = ref(false);
const companyDetails = ref(null); // Stores fetched company details { name, logo_url, login_background_url, default_sso_provider_type, sso_providers: [] }
const companySlug = ref(route.params.companySlug);

const authErrorAlert = computed(() => {
  if (!authStore.error) return '';
  return !companySlug.value 
    ? `${authStore.error} 如果您是公司用户，请使用您公司特定的登录页面。`
    : authStore.error;
});
const authErrorField = computed(() => authStore.error && !companySlug.value ? '凭证无效或请使用公司登录入口。' : '');

const pageTitle = computed(() => {
  if (companySlug.value && companyDetails.value && companyDetails.value.name) {
    return `${companyDetails.value.name}`;
  }
  return '支持人员登录';
});

const platformDisplayInfo = {
  feishu: { name: '飞书', icon: 'mdi-alpha-f-box', color: '#005FFF' },
  enterprise_wechat: { name: '企业微信', icon: 'mdi-wechat', color: '#07C160' },
  wechat: { name: '微信', icon: 'mdi-wechat', color: '#07C160' },
  // Add more platforms here
};

const activeSsoOptions = computed(() => {
  if (companyDetails.value && companyDetails.value.sso_providers) {
    return companyDetails.value.sso_providers
      .filter(p => p.is_enabled && platformDisplayInfo[p.provider_type])
      .map(p => ({
        platform: p.provider_type,
        ...platformDisplayInfo[p.provider_type]
      }));
  }
  return [];
});

const defaultSsoProviderDetails = computed(() => {
  if (companyDetails.value && companyDetails.value.default_sso_provider_type) {
    const defaultPlatform = companyDetails.value.default_sso_provider_type;
    return activeSsoOptions.value.find(opt => opt.platform === defaultPlatform);
  }
  return null;
});

const otherSsoProvidersDetails = computed(() => {
  if (defaultSsoProviderDetails.value) {
    return activeSsoOptions.value.filter(opt => opt.platform !== defaultSsoProviderDetails.value.platform);
  }
  return activeSsoOptions.value;
});

const fetchCompanyPublicDetails = async () => {
  let details = null;
  if (companySlug.value) {
    try {
      // IMPORTANT: This endpoint (`/public/company-details-by-slug/${companySlug.value}/`)
      // must be publicly accessible and return data including:
      // name, logo_url, login_background_url, default_sso_provider_type, 
      // and a list of sso_providers (each with provider_type, is_enabled, app_id if needed by frontend)
      const response = await api.get(`/public/company-details-by-slug/${companySlug.value}/`);
      details = response.data;
    } catch (error) {
      console.error("获取公司公共详情失败:", error);
      details = { name: "公司登录", logo_url: "/img/memoq_logo_placeholder.png", login_background_url: "/img/localization_background.jpg", sso_providers: [], default_sso_provider_type: null };
    }
  } else {
    details = { name: "MemoQ 支持系统", logo_url: "/img/memoq_logo_placeholder.png", login_background_url: "/img/localization_background.jpg", sso_providers: [], default_sso_provider_type: null };
  }
  companyDetails.value = details;
  applyBackground(details.login_background_url);
};

const applyBackground = (bgUrl) => {
  const wrapper = document.querySelector('.login-page-wrapper');
  if (wrapper) {
    wrapper.style.backgroundImage = `url(${bgUrl || '/img/localization_background.jpg'})`;
  }
};

onMounted(() => {
  authStore.error = null;
  fetchCompanyPublicDetails();
  if (authStore.isAuthenticated && !authStore.loading) {
    authStore.redirectBasedOnRole();
  }
});

const handleLogin = async () => {
  loading.value = true;
  authStore.error = null;
  const success = await authStore.login({ ...credentials.value });
  loading.value = false;
};

const handleSsoLogin = (platform) => {
  authStore.error = null;
  // The backend /api/auth/oauth/initiate/ endpoint is responsible for
  // looking up company-specific app_id/secret based on companySlug and platform,
  // then redirecting to the OAuth provider.
  const backendSsoInitiateUrl = `/api/auth/oauth/initiate/${platform}/`;
  const frontendCallbackUrl = `${window.location.origin}/oauth/callback/${platform}`; // Frontend route to handle post-SSO

  const params = new URLSearchParams();
  if (companySlug.value) {
    params.append('company_slug', companySlug.value);
  }
  // This tells backend where to redirect user after its own processing of OAuth provider's callback
  params.append('frontend_redirect_uri', frontendCallbackUrl); 

  window.location.href = `${backendSsoInitiateUrl}?${params.toString()}`;
  console.log(`重定向至后端进行 ${platform} SSO 初始化，公司: ${companySlug.value || 'N/A'}`);
};
</script>

<style scoped>
.login-page-wrapper {
  background-image: url('/img/localization_background.jpg'); /* Default fallback */
  background-size: cover;
  background-position: center center;
  min-height: 100vh;
  padding: 16px;
}
.v-card {
  border-radius: 8px;
  padding-bottom: 16px; /* Extra space for SSO buttons */
}
.v-toolbar-title {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
}
.login-form-section {
  margin-bottom: 1rem;
}
.sso-login-section .v-divider span {
  color: rgba(0,0,0,0.6);
}
.default-sso-btn {
  font-weight: 500;
  text-transform: none; /* Keep case as defined in name */
}
.other-sso-options {
  gap: 8px;
}
.sso-option-btn {
  min-width: 120px;
  text-transform: none;
}
</style>