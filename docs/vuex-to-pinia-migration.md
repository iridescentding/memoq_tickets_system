# Vuex 到 Pinia 迁移指南

## 迁移概述

本项目已将所有状态管理从 Vuex 迁移到 Pinia，以获得更好的类型支持、更简洁的API和更好的开发体验。

## 主要变更

1. **Store 结构变更**
   - 创建了等价的 Pinia store：
     - `useAuthStore` - 用户认证和权限管理
     - `useSnackbarStore` - 全局消息通知
     - `useRootStore` - 兼容层，用于平滑迁移

2. **组件中的用法变更**
   - 替换 `import { useStore } from 'vuex'` 为特定的 store 导入，如 `import { useSnackbarStore } from '@/store/snackbar'`
   - 替换 `const store = useStore()` 为特定的 store 实例，如 `const snackbarStore = useSnackbarStore()`
   - 替换 `store.dispatch('setSnackbar', {...})` 为直接调用 store 的 action，如 `snackbarStore.setSnackbar({...})`

3. **依赖变更**
   - 移除了 Vuex 依赖
   - 添加了 Pinia 依赖

## 迁移后的使用示例

### 全局消息通知

```js
// 旧版 (Vuex)
import { useStore } from 'vuex';

const store = useStore();
store.dispatch('setSnackbar', {
  show: true,
  text: '操作成功',
  color: 'success'
});

// 新版 (Pinia)
import { useSnackbarStore } from '@/store/snackbar';

const snackbarStore = useSnackbarStore();
snackbarStore.setSnackbar({
  show: true,
  text: '操作成功',
  color: 'success'
});
```

### 用户认证和权限

```js
// 旧版 (Vuex)
import { useStore } from 'vuex';

const store = useStore();
const isAdmin = computed(() => store.getters['auth/isSystemAdmin']);
await store.dispatch('auth/login', credentials);

// 新版 (Pinia)
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.isSystemAdmin);
await authStore.login(credentials);
```

## 迁移的好处

1. **更好的类型支持** - Pinia 提供了完整的 TypeScript 支持
2. **更简洁的 API** - 无需使用 mutations，直接修改状态
3. **更好的开发体验** - 自动补全、跳转到定义等 IDE 功能更加可靠
4. **更小的包体积** - Pinia 比 Vuex 更轻量
5. **更好的测试支持** - 可以直接导入 store 进行测试

## 注意事项

如果您在开发中遇到任何与状态管理相关的问题，请参考 Pinia 的官方文档：https://pinia.vuejs.org/
