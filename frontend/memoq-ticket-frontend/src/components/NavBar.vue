<template>
  <v-app-bar
    app
    color="primary"
    dark
  >
    <v-toolbar-title class="mr-4">
      <router-link
        to="/"
        class="white--text text-decoration-none"
      >
        <!-- <img src="../assets/logo.png" alt="memoQ Logo" class="logo" style="height: 30px; vertical-align: middle; margin-right: 8px;" v-if="false"> -->
        memoQ工单系统
      </router-link>
    </v-toolbar-title>

    <!-- 未登录用户菜单 -->
    <template v-if="!isLoggedIn">
      <v-spacer />
      <v-btn
        text
        to="/login"
      >
        登录
      </v-btn>
    </template>

    <!-- 已登录用户菜单 -->
    <template v-else>
      <!-- 客户用户菜单 -->
      <template v-if="userRole === 'customer'">
        <v-btn
          text
          to="/submit-ticket"
        >
          提交工单
        </v-btn>
        <v-btn
          text
          to="/tickets"
        >
          我的工单
        </v-btn>
      </template>

      <!-- 技术支持菜单 -->
      <template v-if="userRole === 'support'">
        <v-btn
          text
          to="/support"
        >
          技术支持面板
        </v-btn>
        <v-btn
          text
          to="/tickets"
        >
          工单列表
        </v-btn>
      </template>

      <!-- 管理员菜单 -->
      <template v-if="userRole === 'admin'">
        <v-btn
          text
          to="/admin"
        >
          管理面板
        </v-btn>
        <v-btn
          text
          to="/tickets"
        >
          工单列表
        </v-btn>
      </template>

      <v-spacer />

      <!-- 用户信息下拉菜单 -->
      <v-menu offset-y>
        <template #activator="{ props }">
          <v-btn
            text
            v-bind="props"
          >
            <v-avatar
              :color="userAvatar ? undefined : 'secondary'"
              size="32"
              class="mr-2"
            >
              <v-img
                v-if="userAvatar"
                :src="userAvatar"
                alt="User Avatar"
              />
              <span
                v-else
                class="white--text"
              >{{ userInitials }}</span>
            </v-avatar>
            {{ userName }}
            <v-icon right>
              mdi-menu-down
            </v-icon>
          </v-btn>
        </template>
        <v-list dense>
          <v-list-item to="/profile">
            <v-list-item-title>个人资料</v-list-item-title>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-title>退出登录</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-app-bar>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';

export default {
  name: 'NavBar',
  setup() {
    const router = useRouter();
    const route = useRoute();
    
    const isLoggedIn = ref(false);
    const userRole = ref('');
    const userName = ref('');
    const userAvatar = ref(''); // URL to avatar image

    const userInitials = computed(() => {
      if (!userName.value) return '';
      return userName.value.substring(0, 1).toUpperCase();
    });

    const logout = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      isLoggedIn.value = false;
      userRole.value = '';
      userName.value = '';
      userAvatar.value = '';
      // Optionally, reset axios auth header if set globally
      // if (this.$axios) { this.$axios.defaults.headers.common['Authorization'] = ''; }
      router.push('/login');
    };

    const checkLoginStatus = () => {
      const token = localStorage.getItem('token');
      const userString = localStorage.getItem('user');
      if (token && userString) {
        try {
          const user = JSON.parse(userString);
          isLoggedIn.value = true;
          userRole.value = user.role || 'customer';
          userName.value = user.username || '';
          userAvatar.value = user.avatar || ''; // Assuming user object might have an avatar URL
        } catch (e) {
          console.error('Failed to parse user from localStorage', e);
          logout(); // Clear corrupted data
        }
      } else {
        isLoggedIn.value = false;
        userRole.value = '';
        userName.value = '';
        userAvatar.value = '';
      }
    };

    onMounted(() => {
      checkLoginStatus();
      // Event listener for storage changes to reflect login status across tabs/windows
      window.addEventListener('storage', checkLoginStatus);
      // Also, if a global event bus is used for login/logout, subscribe here
    });

    // Watch for route changes to potentially update active state if needed, though Vuetify handles this for `to` prop
    watch(() => route.path, () => {
      // If login status could change without a full page reload (e.g. token expiry handled by interceptor)
      // it might be necessary to re-check login status here or via a global event.
      checkLoginStatus(); 
    });

    return {
      isLoggedIn,
      userRole,
      userName,
      userAvatar,
      userInitials,
      logout
    };
  }
};
</script>

<style scoped>
.white--text {
  color: white !important;
}
.text-decoration-none {
  text-decoration: none;
}
/* Add any additional custom styles if Vuetify defaults aren't enough */
</style>
