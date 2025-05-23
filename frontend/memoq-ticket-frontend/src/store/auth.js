import { defineStore } from 'pinia';
import api from '@/api';
import router from '@/router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    error: null,
    loading: false,
  }),
  
  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated,
    userRole: (state) => state.user?.role || 'customer', // Default to customer if no role
    currentUserId: (state) => state.user?.id || null,
    // 角色判断getter
    isSystemAdmin: (state) => state.user?.role === 'system_admin',
    isTechnicalSupportAdmin: (state) => state.user?.role === 'technical_support_admin',
    isSupport: (state) => state.user?.role === 'support',
    isCustomer: (state) => state.user?.role === 'customer' || !state.user?.role,
    // 判断是否有管理权限（系统管理员或技术支持管理员）
    hasAdminAccess: (state) => ['system_admin', 'technical_support_admin'].includes(state.user?.role),
    // 判断是否有支持权限（系统管理员、技术支持管理员或技术支持）
    hasSupportAccess: (state) => ['system_admin', 'technical_support_admin', 'support'].includes(state.user?.role),
    // 获取用户所属公司
    userCompany: (state) => state.user?.company || null,
    // 判断是否是技术人员（非公司用户）
    isTechnicalStaff: (state) => ['system_admin', 'technical_support_admin', 'support'].includes(state.user?.role),
  },
  
  actions: {
    async login(credentials) {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.post('/auth/login/', credentials);
        const { access, user } = response.data; // 调整为后端API响应格式
        this.token = access;
        this.user = user;
        this.isAuthenticated = true;
        localStorage.setItem('token', access);
        localStorage.setItem('user', JSON.stringify(user));
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`; // 设置后续请求的认证头
        
        // 根据角色重定向到相应页面
        this.redirectBasedOnRole();
        return true;
      } catch (error) {
        this.error = error.response?.data?.detail || '登录失败，请检查您的凭据。';
        this.isAuthenticated = false;
        this.user = null;
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        console.error('登录错误:', error);
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    // 根据用户角色重定向到相应页面
    redirectBasedOnRole() {
      if (!this.isAuthenticated) return;
      
      if (this.isSystemAdmin || this.isTechnicalSupportAdmin) {
        router.push('/admin');
      } else if (this.isSupport) {
        router.push('/support');
      } else if (this.isCustomer) {
        router.push('/submit-ticket');
      }
    },
    
    // 使用OAuth进行登录
    async loginWithOAuth(oauthData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await api.post('/auth/oauth/login/', oauthData);
        const { access, user } = response.data;
        this.token = access;
        this.user = user;
        this.isAuthenticated = true;
        localStorage.setItem('token', access);
        localStorage.setItem('user', JSON.stringify(user));
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        
        // 根据角色重定向
        this.redirectBasedOnRole();
        return true;
      } catch (error) {
        this.error = error.response?.data?.detail || '第三方登录失败，请稍后再试。';
        this.isAuthenticated = false;
        this.user = null;
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        console.error('OAuth登录错误:', error);
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    logout() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      this.error = null;
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization']; // 清除认证头
      
      // 重定向到登录页面
      router.push('/login');
    },
    
    async fetchUser() {
      if (!this.token) {
        this.logout(); // 如果没有token，确保状态清理
        return;
      }
      this.loading = true;
      try {
        // 获取当前用户资料
        const response = await api.get('/users/me/'); 
        this.user = response.data;
        this.isAuthenticated = true;
        localStorage.setItem('user', JSON.stringify(this.user));
      } catch (error) {
        console.error('获取用户信息失败:', error);
        this.logout(); // 如果获取用户失败（例如，token过期），则登出
      }
      this.loading = false;
    },
    
    // 检查用户是否有权限访问特定路由
    checkRoutePermission(route) {
      // 如果路由不需要认证，直接允许
      if (!route.meta?.requiresAuth) return true;
      
      // 如果需要认证但用户未登录，拒绝访问
      if (!this.isAuthenticated) return false;
      
      // 检查是否需要管理员权限
      if (route.meta?.requiresAdmin && !this.hasAdminAccess) return false;
      
      // 检查是否需要技术支持权限
      if (route.meta?.requiresSupport && !this.hasSupportAccess) return false;
      
      // 检查是否是公司用户专属路由
      if (route.meta?.requiresCompanyUser && !this.isCustomer) return false;
      
      // 检查是否是技术人员专属路由
      if (route.meta?.requiresTechnicalStaff && !this.isTechnicalStaff) return false;
      
      // 通过所有检查，允许访问
      return true;
    },
    
    // 初始化store，从localStorage加载
    initializeAuth() {
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      if (token && user) {
        this.token = token;
        this.user = JSON.parse(user);
        this.isAuthenticated = true;
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } else {
        this.logout(); // 如果没有存储的认证数据，确保状态清理
      }
    },
    
    // 更新用户数据
    updateUser(userData) {
      this.user = { ...this.user, ...userData };
      localStorage.setItem('user', JSON.stringify(this.user));
    }
  }
});
