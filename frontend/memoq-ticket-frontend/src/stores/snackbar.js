import { defineStore } from 'pinia';

export const useSnackbarStore = defineStore('snackbar', {
  state: () => ({
    show: false,
    text: '',
    color: 'success', // 默认颜色
    timeout: 5000, // 默认显示时间
  }),
  
  actions: {
    setSnackbar(payload) {
      this.show = payload.show !== undefined ? payload.show : true;
      this.text = payload.text || '';
      this.color = payload.color || 'success';
      this.timeout = payload.timeout || 5000;
      
      // 如果设置了自动关闭，则在指定时间后自动关闭
      if (this.show && this.timeout > 0) {
        setTimeout(() => {
          this.show = false;
        }, this.timeout);
      }
    },
    
    closeSnackbar() {
      this.show = false;
    }
  }
});