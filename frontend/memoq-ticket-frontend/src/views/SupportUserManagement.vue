<template>
  <div class="support-user-management">
    <v-container fluid>
      <!-- 面包屑导航 -->
      <v-breadcrumbs :items="breadcrumbs" class="pa-0 mb-4">
        <template v-slot:divider>
          <v-icon>mdi-chevron-right</v-icon>
        </template>
      </v-breadcrumbs>
      
      <h1 class="text-h4 mb-6">技术支持账号管理</h1>
      
      <!-- 操作按钮 -->
      <div class="d-flex justify-space-between align-center mb-4">
        <v-text-field
          v-model="search"
          append-icon="mdi-magnify"
          label="搜索技术支持账号"
          single-line
          hide-details
          density="compact"
          variant="outlined"
          class="search-field"
        ></v-text-field>
        
        <v-btn
          color="primary"
          prepend-icon="mdi-account-plus"
          @click="openCreateDialog"
        >
          创建技术支持账号
        </v-btn>
      </div>
      
      <!-- 技术支持账号列表 -->
      <v-card>
        <v-card-text class="pa-0">
          <v-data-table
            :headers="headers"
            :items="supportUsers"
            :loading="loading"
            class="elevation-0"
          >
            <template v-slot:item.role="{ item }">
              <v-chip
                :color="getRoleColor(item.role)"
                size="small"
                label
              >
                {{ getRoleText(item.role) }}
              </v-chip>
            </template>
            
            <template v-slot:item.is_active="{ item }">
              <v-icon
                :color="item.is_active ? 'success' : 'error'"
                size="small"
              >
                {{ item.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </v-icon>
              {{ item.is_active ? '活跃' : '禁用' }}
            </template>
            
            <template v-slot:item.actions="{ item }">
              <v-btn
                size="small"
                variant="text"
                color="primary"
                @click="openEditDialog(item)"
              >
                <v-icon size="small">mdi-pencil</v-icon>
                编辑
              </v-btn>
              
              <v-btn
                size="small"
                variant="text"
                color="warning"
                @click="openResetPasswordDialog(item)"
              >
                <v-icon size="small">mdi-lock-reset</v-icon>
                重置密码
              </v-btn>
              
              <v-btn
                size="small"
                variant="text"
                :color="item.is_active ? 'error' : 'success'"
                @click="toggleUserStatus(item)"
              >
                <v-icon size="small">
                  {{ item.is_active ? 'mdi-account-off' : 'mdi-account-check' }}
                </v-icon>
                {{ item.is_active ? '禁用' : '启用' }}
              </v-btn>
            </template>
            
            <template v-slot:no-data>
              <div class="text-center pa-5">
                <v-icon size="large" color="grey-lighten-1">mdi-account-group</v-icon>
                <p class="mt-3 text-grey-darken-1">暂无技术支持账号</p>
              </div>
            </template>
            
            <template v-slot:bottom>
              <div class="pa-4">
                <pagination-component
                  :current-page="currentPage"
                  :page-size="pageSize"
                  :total-items="totalSupportUsers"
                  :page-size-options="[10, 20, 50, 100]"
                  @update:current-page="updatePage"
                  @update:page-size="updatePageSize"
                  @page-change="onPageChange"
                />
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <!-- 创建/编辑技术支持账号对话框 -->
      <v-dialog
        v-model="dialog.show"
        max-width="600px"
      >
        <v-card>
          <v-card-title>
            <span class="text-h5">{{ dialog.isEdit ? '编辑技术支持账号' : '创建技术支持账号' }}</span>
          </v-card-title>
          
          <v-card-text>
            <v-form
              ref="formRef"
              v-model="dialog.valid"
            >
              <v-text-field
                v-model="dialog.form.username"
                label="用户名"
                required
                :rules="rules.username"
                variant="outlined"
                class="mb-3"
              ></v-text-field>
              
              <v-text-field
                v-if="!dialog.isEdit"
                v-model="dialog.form.password"
                label="密码"
                type="password"
                required
                :rules="rules.password"
                variant="outlined"
                class="mb-3"
              ></v-text-field>
              
              <v-text-field
                v-model="dialog.form.email"
                label="邮箱"
                type="email"
                required
                :rules="rules.email"
                variant="outlined"
                class="mb-3"
              ></v-text-field>
              
              <v-select
                v-model="dialog.form.role"
                label="角色"
                :items="roleOptions"
                item-title="text"
                item-value="value"
                required
                :rules="rules.role"
                variant="outlined"
                class="mb-3"
              ></v-select>
              
              <v-switch
                v-model="dialog.form.is_active"
                label="账号状态"
                color="success"
                :label-value="dialog.form.is_active ? '活跃' : '禁用'"
                hide-details
                class="mb-3"
              ></v-switch>
            </v-form>
          </v-card-text>
          
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="grey-darken-1"
              variant="text"
              @click="dialog.show = false"
            >
              取消
            </v-btn>
            <v-btn
              color="primary"
              variant="text"
              :loading="dialog.loading"
              :disabled="!dialog.valid"
              @click="saveUser"
            >
              保存
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- 重置密码对话框 -->
      <v-dialog
        v-model="resetPasswordDialog.show"
        max-width="500px"
      >
        <v-card>
          <v-card-title>
            <span class="text-h5">重置密码</span>
          </v-card-title>
          
          <v-card-text>
            <p class="mb-4">您正在为用户 <strong>{{ resetPasswordDialog.username }}</strong> 重置密码。</p>
            
            <v-form
              ref="resetPasswordFormRef"
              v-model="resetPasswordDialog.valid"
            >
              <v-text-field
                v-model="resetPasswordDialog.password"
                label="新密码"
                type="password"
                required
                :rules="rules.password"
                variant="outlined"
                class="mb-3"
              ></v-text-field>
              
              <v-text-field
                v-model="resetPasswordDialog.confirmPassword"
                label="确认新密码"
                type="password"
                required
                :rules="[
                  v => !!v || '请确认新密码',
                  v => v === resetPasswordDialog.password || '两次输入的密码不一致'
                ]"
                variant="outlined"
              ></v-text-field>
            </v-form>
          </v-card-text>
          
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="grey-darken-1"
              variant="text"
              @click="resetPasswordDialog.show = false"
            >
              取消
            </v-btn>
            <v-btn
              color="primary"
              variant="text"
              :loading="resetPasswordDialog.loading"
              :disabled="!resetPasswordDialog.valid"
              @click="resetPassword"
            >
              重置密码
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
      <!-- 确认对话框 -->
      <v-dialog
        v-model="confirmDialog.show"
        max-width="400px"
      >
        <v-card>
          <v-card-title class="text-h5">
            {{ confirmDialog.title }}
          </v-card-title>
          
          <v-card-text>
            {{ confirmDialog.message }}
          </v-card-text>
          
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="grey-darken-1"
              variant="text"
              @click="confirmDialog.show = false"
            >
              取消
            </v-btn>
            <v-btn
              :color="confirmDialog.color"
              variant="text"
              @click="confirmDialog.action"
            >
              确认
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useSnackbarStore } from '@/store/snackbar';
import api from '@/api';
import PaginationComponent from '@/components/PaginationComponent.vue';

export default {
  name: 'SupportUserManagement',
  components: {
    PaginationComponent
  },
  
  setup() {
    const snackbarStore = useSnackbarStore();
    const formRef = ref(null);
    const resetPasswordFormRef = ref(null);
    
    // 面包屑导航
    const breadcrumbs = [
      {
        title: '首页',
        disabled: false,
        href: '/'
      },
      {
        title: '管理员仪表盘',
        disabled: false,
        href: '/admin'
      },
      {
        title: '技术支持账号管理',
        disabled: true
      }
    ];
    
    // 技术支持账号列表
    const supportUsers = ref([]);
    const loading = ref(false);
    const totalSupportUsers = ref(0);
    const search = ref('');
    const currentPage = ref(1);
    const pageSize = ref(20); // 默认每页20条
    
    // 表头
    const headers = [
      { title: 'ID', key: 'id', sortable: true },
      { title: '用户名', key: 'username', sortable: true },
      { title: '邮箱', key: 'email', sortable: true },
      { title: '角色', key: 'role', sortable: true },
      { title: '状态', key: 'is_active', sortable: true },
      { title: '创建时间', key: 'date_joined', sortable: true },
      { title: '操作', key: 'actions', sortable: false }
    ];
    
    // 角色选项
    const roleOptions = [
      { text: '技术支持', value: 'support' },
      { text: '技术支持管理员', value: 'technical_support_admin' }
    ];
    
    // 表单验证规则
    const rules = {
      username: [
        v => !!v || '请输入用户名',
        v => (v && v.length >= 3) || '用户名至少需要3个字符'
      ],
      password: [
        v => !!v || '请输入密码',
        v => (v && v.length >= 8) || '密码至少需要8个字符'
      ],
      email: [
        v => !!v || '请输入邮箱',
        v => /.+@.+\..+/.test(v) || '请输入有效的邮箱地址'
      ],
      role: [
        v => !!v || '请选择角色'
      ]
    };
    
    // 对话框状态
    const dialog = reactive({
      show: false,
      isEdit: false,
      valid: false,
      loading: false,
      userId: null,
      form: {
        username: '',
        password: '',
        email: '',
        role: 'support',
        is_active: true
      }
    });
    
    // 重置密码对话框状态
    const resetPasswordDialog = reactive({
      show: false,
      valid: false,
      loading: false,
      userId: null,
      username: '',
      password: '',
      confirmPassword: ''
    });
    
    // 确认对话框状态
    const confirmDialog = reactive({
      show: false,
      title: '',
      message: '',
      color: 'primary',
      action: () => {}
    });
    
    // 计算属性
    const queryParams = computed(() => {
      const params = {
        page: currentPage.value,
        page_size: pageSize.value
      };
      
      // 添加搜索
      if (search.value) {
        params.search = search.value;
      }
      
      return params;
    });
    
    // 方法
    const fetchSupportUsers = async () => {
      loading.value = true;
      
      try {
        const response = await api.get('/users/support-users/', {
          params: queryParams.value
        });
        
        supportUsers.value = response.data.results;
        totalSupportUsers.value = response.data.count;
      } catch (error) {
        console.error('获取技术支持账号失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '获取技术支持账号失败，请稍后重试',
          color: 'error'
        });
      } finally {
        loading.value = false;
      }
    };
    
    const openCreateDialog = () => {
      dialog.isEdit = false;
      dialog.userId = null;
      dialog.form = {
        username: '',
        password: '',
        email: '',
        role: 'support',
        is_active: true
      };
      dialog.show = true;
    };
    
    const openEditDialog = (user) => {
      dialog.isEdit = true;
      dialog.userId = user.id;
      dialog.form = {
        username: user.username,
        email: user.email,
        role: user.role,
        is_active: user.is_active
      };
      dialog.show = true;
    };
    
    const saveUser = async () => {
      if (!dialog.valid) return;
      
      dialog.loading = true;
      
      try {
        if (dialog.isEdit) {
          // 更新用户
          await api.put(`/users/support-users/${dialog.userId}/`, dialog.form);
          snackbarStore.setSnackbar({
            show: true,
            text: '技术支持账号更新成功',
            color: 'success'
          });
        } else {
          // 创建用户
          await api.post('/users/support-users/', dialog.form);
          snackbarStore.setSnackbar({
            show: true,
            text: '技术支持账号创建成功',
            color: 'success'
          });
        }
        
        // 关闭对话框并刷新列表
        dialog.show = false;
        fetchSupportUsers();
      } catch (error) {
        console.error('保存技术支持账号失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: `${dialog.isEdit ? '更新' : '创建'}技术支持账号失败: ${error.response?.data?.detail || '请稍后重试'}`,
          color: 'error'
        });
      } finally {
        dialog.loading = false;
      }
    };
    
    const openResetPasswordDialog = (user) => {
      resetPasswordDialog.userId = user.id;
      resetPasswordDialog.username = user.username;
      resetPasswordDialog.password = '';
      resetPasswordDialog.confirmPassword = '';
      resetPasswordDialog.show = true;
    };
    
    const resetPassword = async () => {
      if (!resetPasswordDialog.valid) return;
      
      resetPasswordDialog.loading = true;
      
      try {
        await api.post(`/users/support-users/${resetPasswordDialog.userId}/reset-password/`, {
          password: resetPasswordDialog.password
        });
        
        snackbarStore.setSnackbar({
          show: true,
          text: '密码重置成功',
          color: 'success'
        });
        
        // 关闭对话框
        resetPasswordDialog.show = false;
      } catch (error) {
        console.error('重置密码失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: `重置密码失败: ${error.response?.data?.detail || '请稍后重试'}`,
          color: 'error'
        });
      } finally {
        resetPasswordDialog.loading = false;
      }
    };
    
    const toggleUserStatus = (user) => {
      confirmDialog.title = user.is_active ? '禁用账号' : '启用账号';
      confirmDialog.message = user.is_active
        ? `您确定要禁用用户 "${user.username}" 的账号吗？禁用后该用户将无法登录系统。`
        : `您确定要启用用户 "${user.username}" 的账号吗？启用后该用户将可以登录系统。`;
      confirmDialog.color = user.is_active ? 'error' : 'success';
      confirmDialog.action = async () => {
        try {
          await api.put(`/users/support-users/${user.id}/`, {
            ...user,
            is_active: !user.is_active
          });
          
          store.dispatch('setSnackbar', {
            show: true,
            text: `账号${user.is_active ? '禁用' : '启用'}成功`,
            color: 'success'
          });
          
          // 关闭确认对话框并刷新列表
          confirmDialog.show = false;
          fetchSupportUsers();
        } catch (error) {
          console.error('更新账号状态失败:', error);
          store.dispatch('setSnackbar', {
            show: true,
            text: `更新账号状态失败: ${error.response?.data?.detail || '请稍后重试'}`,
            color: 'error'
          });
        }
      };
      confirmDialog.show = true;
    };
    
    // 分页方法
    const updatePage = (page) => {
      currentPage.value = page;
    };
    
    const updatePageSize = (size) => {
      pageSize.value = size;
    };
    
    const onPageChange = () => {
      fetchSupportUsers();
    };
    
    // 辅助方法
    const getRoleColor = (role) => {
      const roleColors = {
        'support': 'blue',
        'technical_support_admin': 'purple'
      };
      return roleColors[role] || 'grey';
    };
    
    const getRoleText = (role) => {
      const roleTexts = {
        'support': '技术支持',
        'technical_support_admin': '技术支持管理员'
      };
      return roleTexts[role] || role;
    };
    
    // 监听搜索变化
    const debouncedSearch = () => {
      const timer = ref(null);
      return () => {
        clearTimeout(timer.value);
        timer.value = setTimeout(() => {
          currentPage.value = 1; // 重置到第一页
          fetchSupportUsers();
        }, 500);
      };
    };
    
    const handleSearch = debouncedSearch();
    
    watch(search, () => {
      handleSearch();
    });
    
    // 生命周期钩子
    onMounted(() => {
      fetchSupportUsers();
    });
    
    return {
      breadcrumbs,
      supportUsers,
      loading,
      totalSupportUsers,
      search,
      currentPage,
      pageSize,
      headers,
      roleOptions,
      rules,
      dialog,
      resetPasswordDialog,
      confirmDialog,
      formRef,
      resetPasswordFormRef,
      fetchSupportUsers,
      openCreateDialog,
      openEditDialog,
      saveUser,
      openResetPasswordDialog,
      resetPassword,
      toggleUserStatus,
      updatePage,
      updatePageSize,
      onPageChange,
      getRoleColor,
      getRoleText
    };
  }
};
</script>

<style scoped>
.support-user-management {
  padding: 16px;
}

.search-field {
  max-width: 300px;
}

@media (max-width: 600px) {
  .d-flex.justify-space-between {
    flex-direction: column;
    align-items: stretch !important;
  }
  
  .search-field {
    max-width: 100%;
    margin-bottom: 16px;
  }
}
</style>
