<template>
  <div class="company-detail-layout">
    <v-card class="mb-4">
      <v-card-title>
        <v-btn icon @click="$router.push({ name: 'AdminCompanyList' })">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        公司详情配置: {{ companyName }}
      </v-card-title>
      
      <v-card-text>
        <v-tabs v-model="activeTab">
          <v-tab :to="{ name: 'AdminCompanySSOManagement', params: { companyId } }">
            <v-icon left>mdi-account-key</v-icon>
            SSO配置
          </v-tab>
          <v-tab :to="{ name: 'AdminCompanyNotificationTemplates', params: { companyId } }">
            <v-icon left>mdi-bell-outline</v-icon>
            通知模板
          </v-tab>
        </v-tabs>
      </v-card-text>
    </v-card>
    
    <router-view></router-view>
  </div>
</template>

<script>
import { useSnackbarStore } from '@/stores/snackbar';
import api from '@/api';

export default {
  name: 'CompanyDetailLayout',
  
  props: {
    companyId: {
      type: [String, Number],
      required: true
    }
  },
  
  setup() {
    // 使用 Pinia store
    const snackbarStore = useSnackbarStore();
    
    return {
      snackbarStore
    };
  },
  
  data() {
    return {
      activeTab: 0,
      companyName: '',
      loading: false
    };
  },
  
  created() {
    this.fetchCompanyDetails();
  },
  
  methods: {
    async fetchCompanyDetails() {
      this.loading = true;
      try {
        const response = await api.get(`/api/companies/${this.companyId}/`);
        this.companyName = response.data.name;
      } catch (error) {
        console.error('获取公司详情失败:', error);
        this.snackbarStore.setSnackbar({
          text: '获取公司详情失败: ' + (error.response?.data?.detail || error.message),
          color: 'error'
        });
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.company-detail-layout {
  padding: 16px;
}
</style>\

