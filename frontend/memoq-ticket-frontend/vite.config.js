import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path"; // Import path module

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"), // Add this line to configure the '@' alias
    },
  },
  // 开发服务器配置，优化Docker环境中的热重载
  server: {
    port: 3000, // 明确指定端口为3000
    watch: {
      // 在Docker环境中启用polling以确保文件变化能被正确检测
      usePolling: true,
      interval: 1000,
    },
    host: '0.0.0.0',
    // 允许在Docker环境中进行热模块替换
    hmr: {
      clientPort: 3000, // 客户端访问的端口
      overlay: true,    // 显示错误覆盖层
    },
    // 配置API代理，解决跨域问题
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  },
  // 优化构建配置
  build: {
    // 启用源码映射，方便调试
    sourcemap: true,
    // 分割代码块，优化加载性能
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia', 'vuetify'],
          'api': ['axios']
        }
      }
    },
    // 设置chunk大小警告阈值
    chunkSizeWarningLimit: 1000
  }
});
