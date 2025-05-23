import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createPinia } from 'pinia';

// Vuetify
import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import '@mdi/font/css/materialdesignicons.css'; // Ensure you have this installed for icons

import App from './App.vue';
import routes from './router';
import axios from 'axios';

// 使用环境变量配置axios默认值
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/';
axios.defaults.baseURL = apiBaseUrl;
axios.defaults.headers.common['Content-Type'] = 'application/json';

console.log('API Base URL:', apiBaseUrl); // 调试用，可以在生产环境移除

// 创建Pinia状态管理
const pinia = createPinia();

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
});

// 创建Vuetify实例
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi', // This is already the default value - only for display purposes
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107',
        },
      },
    },
  },
});

// 创建Vue应用实例
const app = createApp(App);

// 全局注册axios
app.config.globalProperties.$axios = axios;

// 使用插件
app.use(pinia);
app.use(vuetify);
app.use(router);

// 挂载应用
app.mount('#app');
