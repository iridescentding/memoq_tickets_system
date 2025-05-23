import { defineStore } from 'pinia';

// 创建一个空的根store，用于替代可能存在的vuex根store
// 这样可以确保迁移过程中的兼容性
export const useRootStore = defineStore('root', {
  state: () => ({
    // 可以添加全局共享状态
  }),
  
  getters: {
    // 全局getter
  },
  
  actions: {
    // 全局actions
    
    // 兼容vuex的dispatch方法，用于平滑迁移
    // 这个方法会根据action类型分发到对应的store
    dispatch(type, payload) {
      // 处理setSnackbar action
      if (type === 'setSnackbar') {
        // 动态导入snackbar store并调用其action
        const { useSnackbarStore } = require('./snackbar');
        const snackbarStore = useSnackbarStore();
        snackbarStore.setSnackbar(payload);
        return;
      }
      
      // 处理auth相关actions
      if (type.startsWith('auth/')) {
        const actionName = type.split('/')[1];
        const { useAuthStore } = require('./auth');
        const authStore = useAuthStore();
        
        if (typeof authStore[actionName] === 'function') {
          return authStore[actionName](payload);
        }
      }
      
      console.warn(`Action "${type}" not found in any store`);
    }
  }
});
