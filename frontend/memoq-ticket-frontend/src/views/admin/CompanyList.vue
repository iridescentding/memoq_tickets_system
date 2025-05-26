<template>
  <div class="company-list-container">
    <v-card>
      <v-card-title>
        公司管理
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          append-icon="mdi-magnify"
          label="搜索"
          single-line
          hide-details
        ></v-text-field>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="companies"
        :search="search"
        :loading="loading"
        :items-per-page="10"
        :footer-props="{
          'items-per-page-options': [5, 10, 15, 20],
          'items-per-page-text': '每页显示'
        }"
        class="elevation-1"
      >
        <template v-slot:item.actions="{ item }">
          <v-btn
            small
            color="primary"
            text
            :to="{ name: 'AdminCompanySSOManagement', params: { companyId: item.id }}"
          >
            <v-icon small>mdi-cog</v-icon>
            配置
          </v-btn>
        </template>
        
        <template v-slot:item.importance="{ item }">
          <v-chip
            :color="getImportanceColor(item.importance)"
            text-color="white"
            small
          >
            {{ getImportanceLabel(item.importance) }}
          </v-chip>
        </template>
        
        <template v-slot:item.is_active="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            text-color="white"
            small
          >
            {{ item.is_active ? '激活' : '禁用' }}
          </v-chip>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth';
import { useSnackbarStore } from '@/stores/snackbar';
import api from '@/api';

export default {
  name: 'CompanyList',
  
  setup() {
    // 使用 Pinia store
    const authStore = useAuthStore();
    const snackbarStore = useSnackbarStore();
    
    return {
      authStore,
      snackbarStore
    };
  },
  
  data() {
    return {
      search: '',
      loading: false,
      companies: [],
      headers: [
        { text: 'ID', value: 'id' },
        { text: '公司名称', value: 'name' },
        { text: '公司代码', value: 'code' },
        { text: '重要性', value: 'importance' },
        { text: '联系人', value: 'contact_person' },
        { text: '联系邮箱', value: 'contact_email' },
        { text: '状态', value: 'is_active' },
        { text: '创建时间', value: 'created_at' },
        { text: '操作', value: 'actions', sortable: false }
      ]
    };
  },
  
  computed: {
    // 从 Pinia store 获取用户信息
    user() {
      return this.authStore.user;
    }
  },
  
  created() {
    this.fetchCompanies();
  },
  
  methods: {
    async fetchCompanies() {
      this.loading = true;
      try {
        const response = await api.get('/api/companies/');
        this.companies = response.data.results;
      } catch (error) {
        console.error('获取公司列表失败:', error);
        this.snackbarStore.setSnackbar({
          text: '获取公司列表失败: ' + (error.response?.data?.detail || error.message),
          color: 'error'
        });
      } finally {
        this.loading = false;
      }
    },
    
    getImportanceColor(importance) {
      const colors = {
        1: 'green',
        2: 'blue',
        3: 'orange',
        4: 'red',
        5: 'purple'
      };
      return colors[importance] || 'grey';
    },
    
    getImportanceLabel(importance) {
      const labels = {
        1: '低',
        2: '中低',
        3: '中',
        4: '中高',
        5: '高'
      };
      return labels[importance] || '未知';
    }
  }
};
</script>

<style scoped>
.company-list-container {
  padding: 16px;
}
</style>