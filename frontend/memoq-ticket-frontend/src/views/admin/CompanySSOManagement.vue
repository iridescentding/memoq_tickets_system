<template>
  <v-container fluid>
    <v-card :loading="loadingCompany || loadingSsoConfigs" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon left class="mr-2">mdi-key-chain</v-icon>
        <span>SSO登录配置: {{ company ? company.name : '加载中...' }}</span>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openSsoDialog()" :disabled="!company">
          <v-icon left>mdi-plus</v-icon>
          添加SSO提供商
        </v-btn>
      </v-card-title>
      <v-card-subtitle v-if="company">
        管理公司的单点登录选项。当前默认SSO: 
        <v-chip v-if="company.default_sso_provider_type" color="green" small class="ml-1">
          {{ getProviderDisplayName(company.default_sso_provider_type) }}
        </v-chip>
        <span v-else class="ml-1">未设置</span>
      </v-card-subtitle>
      <v-divider></v-divider>

      <v-card-text v-if="loadingSsoConfigs">
        <v-progress-linear indeterminate></v-progress-linear>
        <p class="text-center mt-2">正在加载SSO配置...</p>
      </v-card-text>
      <v-card-text v-else-if="ssoConfigs.length === 0 && company">
        <v-alert type="info" prominent border="start" density="compact">
          该公司当前没有配置任何SSO提供商。
        </v-alert>
      </v-card-text>
      <v-list v-else lines="three">
        <template v-for="(config, index) in ssoConfigs" :key="config.id">
          <v-list-item>
            <template v-slot:prepend>
              <v-icon :color="getProviderPlatformInfo(config.provider_type).color || 'grey'">
                {{ getProviderPlatformInfo(config.provider_type).icon || 'mdi-key-variant' }}
              </v-icon>
            </template>
            <v-list-item-title class="font-weight-medium">
              {{ config.provider_type_display }}
              <v-chip v-if="config.is_enabled" color="success" x-small class="ml-2">已启用</v-chip>
              <v-chip v-else color="grey" x-small class="ml-2">已禁用</v-chip>
              <v-chip v-if="company && company.default_sso_provider_type === config.provider_type" color="amber" x-small class="ml-2">默认</v-chip>
            </v-list-item-title>
            <v-list-item-subtitle>
              App ID: {{ config.app_id || '未设置' }} <br>
              Webhook URL: {{ config.webhook_url || '未设置' }}
            </v-list-item-subtitle>

            <template v-slot:append>
              <v-btn icon="mdi-pencil" variant="text" color="info" @click="openSsoDialog(config)" class="mr-1" density="compact"></v-btn>
              <v-btn 
                v-if="company && company.default_sso_provider_type !== config.provider_type && config.is_enabled" 
                icon="mdi-star-check-outline" 
                variant="text" 
                color="amber-darken-2" 
                @click="setDefaultSso(config.provider_type)"
                density="compact"
                title="设为默认"
                class="mr-1"
              ></v-btn>
               <v-btn 
                v-if="company && company.default_sso_provider_type === config.provider_type" 
                icon="mdi-star-off-outline" 
                variant="text" 
                color="grey" 
                @click="clearDefaultSso()"
                density="compact"
                title="取消默认"
                class="mr-1"
              ></v-btn>
              <v-btn icon="mdi-delete" variant="text" color="error" @click="deleteSsoConfig(config)" density="compact"></v-btn>
            </template>
          </v-list-item>
          <v-divider v-if="index < ssoConfigs.length - 1"></v-divider>
        </template>
      </v-list>
    </v-card>

    <v-dialog v-model="ssoDialog.show" max-width="700px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ ssoDialog.isEdit ? '编辑' : '添加' }} SSO 提供商</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="ssoFormRef">
            <v-select
              v-model="ssoDialog.data.provider_type"
              :items="availableProviderTypes"
              item-title="text"
              item-value="value"
              label="提供商类型"
              :rules="[rules.required]"
              :disabled="ssoDialog.isEdit"
              variant="outlined"
              density="compact"
              class="mb-3"
            ></v-select>
            <v-text-field
              v-model="ssoDialog.data.app_id"
              label="App ID / Corp ID"
              variant="outlined"
              density="compact"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="ssoDialog.data.app_secret"
              label="App Secret / Corp Secret"
              type="password"
              variant="outlined"
              density="compact"
              class="mb-3"
              hint="仅在创建或更新密钥时填写"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="ssoDialog.data.agent_id"
              label="Agent ID (可选, 如企业微信)"
              variant="outlined"
              density="compact"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="ssoDialog.data.webhook_url"
              label="消息通知 Webhook URL (可选)"
              type="url"
              variant="outlined"
              density="compact"
              class="mb-3"
            ></v-text-field>
            <v-textarea
              v-model="ssoDialog.data.additional_config_str"
              label="其他配置 (JSON格式, 可选)"
              rows="3"
              variant="outlined"
              density="compact"
              class="mb-3"
              hint='例如: {"custom_param": "value"}'
            ></v-textarea>
            <v-switch
              v-model="ssoDialog.data.is_enabled"
              label="启用此SSO提供商"
              color="success"
            ></v-switch>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue-darken-1" variant="text" @click="closeSsoDialog">取消</v-btn>
          <v-btn color="blue-darken-1" variant="elevated" @click="saveSsoConfig" :loading="ssoDialog.loading">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialog.show" max-width="500px">
        <v-card>
            <v-card-title class="text-h5">确认删除</v-card-title>
            <v-card-text>您确定要删除此SSO配置吗？此操作无法撤销。</v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue-darken-1" variant="text" @click="deleteDialog.show = false">取消</v-btn>
                <v-btn color="red-darken-1" variant="elevated" @click="confirmDeleteSso" :loading="deleteDialog.loading">删除</v-btn>
                <v-spacer></v-spacer>
            </v-card-actions>
        </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import api from '@/api';
import { useSnackbarStore } from '@/store/snackbar'; // Assuming you have this

const route = useRoute();
const snackbarStore = useSnackbarStore();
const companyId = ref(route.params.companyId); // Assuming companyId is passed as a route param

const loadingCompany = ref(false);
const loadingSsoConfigs = ref(false);
const company = ref(null);
const ssoConfigs = ref([]);
const ssoFormRef = ref(null);

const ssoDialog = ref({
  show: false,
  isEdit: false,
  loading: false,
  data: {
    id: null,
    provider_type: '',
    is_enabled: true,
    app_id: '',
    app_secret: '',
    agent_id: '',
    webhook_url: '',
    additional_config_str: '{}', // Store as string for textarea, parse before sending
  },
});

const deleteDialog = ref({
    show: false,
    loading: false,
    itemToDelete: null,
});

const rules = {
  required: value => !!value || '此字段为必填项.',
};

const availableProviderTypes = ref([
  { text: '飞书 (Feishu)', value: 'feishu' },
  { text: '企业微信 (Enterprise WeChat)', value: 'enterprise_wechat' },
  { text: '微信 (WeChat)', value: 'wechat' },
  // Add more as supported by backend CompanySSOProvider.PROVIDER_CHOICES
]);

const platformDisplayInfo = {
  feishu: { name: '飞书', icon: 'mdi-alpha-f-box', color: '#005FFF' },
  enterprise_wechat: { name: '企业微信', icon: 'mdi-wechat', color: '#07C160' },
  wechat: { name: '微信', icon: 'mdi-wechat', color: '#07C160' },
};

const getProviderPlatformInfo = (providerType) => {
    return platformDisplayInfo[providerType] || { name: providerType, icon: 'mdi-key-variant', color: 'grey' };
};
const getProviderDisplayName = (providerType) => {
    const info = platformDisplayInfo[providerType];
    return info ? info.name : providerType;
};


async function fetchCompanyDetails() {
  if (!companyId.value) return;
  loadingCompany.value = true;
  try {
    const response = await api.get(`/companies/${companyId.value}/`);
    company.value = response.data;
  } catch (error) {
    console.error("获取公司详情失败:", error);
    snackbarStore.setSnackbar({ text: `获取公司详情失败: ${error.message || error}`, color: 'error' });
  } finally {
    loadingCompany.value = false;
  }
}

async function fetchSsoConfigs() {
  if (!companyId.value) return;
  loadingSsoConfigs.value = true;
  try {
    // Assuming API endpoint like /company-sso-providers/?company_id=<id>
    const response = await api.get(`/company-sso-providers/?company_id=${companyId.value}`);
    ssoConfigs.value = response.data.results || response.data; // Adjust based on pagination
  } catch (error) {
    console.error("获取SSO配置失败:", error);
    snackbarStore.setSnackbar({ text: `获取SSO配置失败: ${error.message || error}`, color: 'error' });
    ssoConfigs.value = [];
  } finally {
    loadingSsoConfigs.value = false;
  }
}

function openSsoDialog(config = null) {
  if (config) {
    ssoDialog.value.isEdit = true;
    ssoDialog.value.data = { 
        ...config, 
        additional_config_str: config.additional_config ? JSON.stringify(config.additional_config, null, 2) : '{}'
    };
  } else {
    ssoDialog.value.isEdit = false;
    ssoDialog.value.data = {
      id: null,
      provider_type: '',
      is_enabled: true,
      app_id: '',
      app_secret: '',
      agent_id: '',
      webhook_url: '',
      additional_config_str: '{}',
    };
  }
  ssoDialog.value.show = true;
}

function closeSsoDialog() {
  ssoDialog.value.show = false;
  ssoFormRef.value?.resetValidation();
}

async function saveSsoConfig() {
  const { valid } = await ssoFormRef.value.validate();
  if (!valid) return;

  ssoDialog.value.loading = true;
  let payload = { ...ssoDialog.value.data, company: companyId.value };
  
  // Parse additional_config_str to JSON object
  try {
    payload.additional_config = JSON.parse(payload.additional_config_str || '{}');
  } catch (e) {
    snackbarStore.setSnackbar({ text: '其他配置JSON格式无效。', color: 'error' });
    ssoDialog.value.loading = false;
    return;
  }
  delete payload.additional_config_str; // Remove string version from payload

  // Do not send app_secret if it's not being changed (empty or placeholder)
  if (!payload.app_secret && ssoDialog.value.isEdit) {
    delete payload.app_secret;
  }


  try {
    if (ssoDialog.value.isEdit && payload.id) {
      await api.put(`/company-sso-providers/${payload.id}/`, payload);
      snackbarStore.setSnackbar({ text: 'SSO配置更新成功！', color: 'success' });
    } else {
      delete payload.id; // Ensure no ID for create
      await api.post('/company-sso-providers/', payload);
      snackbarStore.setSnackbar({ text: 'SSO配置添加成功！', color: 'success' });
    }
    fetchSsoConfigs(); // Refresh list
    closeSsoDialog();
  } catch (error) {
    console.error("保存SSO配置失败:", error.response?.data || error.message);
    snackbarStore.setSnackbar({ text: `保存SSO配置失败: ${error.response?.data?.detail || error.message || error}`, color: 'error' });
  } finally {
    ssoDialog.value.loading = false;
  }
}

async function setDefaultSso(providerType) {
    if (!company.value) return;
    loadingCompany.value = true;
    try {
        await api.patch(`/companies/${companyId.value}/`, { default_sso_provider_type: providerType });
        company.value.default_sso_provider_type = providerType; // Update local state
        snackbarStore.setSnackbar({ text: `已将 ${getProviderDisplayName(providerType)} 设为默认SSO。`, color: 'success' });
    } catch (error) {
        console.error("设置默认SSO失败:", error);
        snackbarStore.setSnackbar({ text: `设置默认SSO失败: ${error.message || error}`, color: 'error' });
    } finally {
        loadingCompany.value = false;
    }
}

async function clearDefaultSso() {
    if (!company.value) return;
    loadingCompany.value = true;
    try {
        await api.patch(`/companies/${companyId.value}/`, { default_sso_provider_type: null });
        company.value.default_sso_provider_type = null; // Update local state
        snackbarStore.setSnackbar({ text: '已取消默认SSO提供商。', color: 'success' });
    } catch (error) {
        console.error("取消默认SSO失败:", error);
        snackbarStore.setSnackbar({ text: `取消默认SSO失败: ${error.message || error}`, color: 'error' });
    } finally {
        loadingCompany.value = false;
    }
}

function deleteSsoConfig(config) {
    deleteDialog.value.itemToDelete = config;
    deleteDialog.value.show = true;
}

async function confirmDeleteSso() {
    if (!deleteDialog.value.itemToDelete) return;
    deleteDialog.value.loading = true;
    try {
        await api.delete(`/company-sso-providers/${deleteDialog.value.itemToDelete.id}/`);
        snackbarStore.setSnackbar({ text: 'SSO配置已删除。', color: 'success' });
        fetchSsoConfigs(); // Refresh list
        if (company.value && company.value.default_sso_provider_type === deleteDialog.value.itemToDelete.provider_type) {
            company.value.default_sso_provider_type = null; // Clear default if it was deleted
        }
    } catch (error) {
        console.error("删除SSO配置失败:", error);
        snackbarStore.setSnackbar({ text: `删除SSO配置失败: ${error.message || error}`, color: 'error' });
    } finally {
        deleteDialog.value.loading = false;
        deleteDialog.value.show = false;
        deleteDialog.value.itemToDelete = null;
    }
}


onMounted(() => {
  if (companyId.value) {
    fetchCompanyDetails();
    fetchSsoConfigs();
  } else {
    snackbarStore.setSnackbar({ text: '未提供公司ID，无法加载SSO配置。', color: 'warning' });
  }
});

// Watch for companyId changes if this component can be reused without full remount
watch(() => route.params.companyId, (newId) => {
  if (newId) {
    companyId.value = newId;
    fetchCompanyDetails();
    fetchSsoConfigs();
  }
});

</script>

<style scoped>
.v-list-item-subtitle {
  white-space: normal;
  line-height: 1.4;
}
.v-chip {
    font-size: 0.75rem;
    height: 20px;
}
</style>
