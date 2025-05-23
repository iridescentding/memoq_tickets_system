<template>
  <v-app-bar app color="primary" dark>
    <v-app-bar-title>
      <router-link to="/" class="text-decoration-none text-white">
        memoQ工单系统
      </router-link>
    </v-app-bar-title>
    
    <v-spacer></v-spacer>
    
    <!-- 未登录状态显示登录按钮 -->
    <template v-if="!isLoggedIn">
      <v-btn to="/login" text>
        <v-icon left>mdi-login</v-icon>
        登录
      </v-btn>
    </template>
    
    <!-- 已登录状态显示用户菜单 -->
    <template v-else>
      <v-btn to="/submit-ticket" text>
        <v-icon left>mdi-plus-circle</v-icon>
        提交工单
      </v-btn>
      
      <v-btn to="/tickets" text>
        <v-icon left>mdi-ticket</v-icon>
        我的工单
      </v-btn>
      
      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn icon v-bind="props">
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item to="/profile">
            <v-list-item-title>个人资料</v-list-item-title>
          </v-list-item>
          
          <v-list-item v-if="isAdmin" to="/admin">
            <v-list-item-title>管理控制台</v-list-item-title>
          </v-list-item>
          
          <v-list-item v-if="isSupport" to="/support">
            <v-list-item-title>支持控制台</v-list-item-title>
          </v-list-item>
          
          <v-divider></v-divider>
          
          <v-list-item @click="logout">
            <v-list-item-title>退出登录</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-app-bar>
</template>

<script>
import { computed } from 'vue';
import { useAuthStore } from '@/store/auth';

export default {
  name: 'AppBar',
  setup() {
    const authStore = useAuthStore();
    
    const isLoggedIn = computed(() => authStore.isAuthenticated);
    const isAdmin = computed(() => {
      const role = authStore.userRole;
      return role === 'system_admin' || role === 'technical_support_admin';
    });
    const isSupport = computed(() => authStore.userRole === 'support');
    
    const logout = async () => {
      await authStore.logout();
      // 退出后重定向到首页
      window.location.href = '/';
    };
    
    return {
      isLoggedIn,
      isAdmin,
      isSupport,
      logout
    };
  }
};
</script>