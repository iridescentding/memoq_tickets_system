<template>
  <v-container fluid>
    <v-card :loading="loadingCompany || loadingTemplates">
      <v-card-title class="d-flex align-center">
        <v-icon left class="mr-2">mdi-email-edit-outline</v-icon>
        <span>通知模板管理: {{ company ? company.name : '加载中...' }}</span>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openTemplateDialog()" :disabled="!company">
          <v-icon left>mdi-plus</v-icon>
          添加模板
        </v-btn>
      </v-card-title>
      <v-card-subtitle v-if="company">
        管理该公司的自动通知模板。全局模板（如适用）也可能在此生效。
      </v-card-subtitle>
      <v-divider></v-divider>

      <v-card-text v-if="loadingTemplates">
        <v-progress-linear indeterminate></v-progress-linear>
        <p class="text-center mt-2">正在加载通知模板...</p>
      </v-card-text>
      <v-card-text v-else-if="templates.length === 0 && company">
        <v-alert type="info" prominent border="start" density="compact">
          该公司当前没有配置任何特定的通知模板。可能会使用全局默认模板。
        </v-alert>
      </v-card-text>
      <v-expansion-panels v-else variant="accordion">
        <v-expansion-panel
          v-for="template in templates"
          :key="template.id"
        >
          <v-expansion-panel-title>
            <v-icon left class="mr-3">{{ getChannelIcon(template.channel) }}</v-icon>
            <span class="font-weight-medium">{{ template.name }}</span>
            <v-chip small :color="template.is_active ? 'success' : 'grey'" class="ml-3">{{ template.is_active ? '已激活' : '未激活' }}</v-chip>
            <v-chip small color="blue-grey" class="ml-2">{{ template.event_type_display }} -> {{ template.channel_display }}</v-chip>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <p><strong>事件类型:</strong> {{ template.event_type_display }}</p>
            <p><strong>通知渠道:</strong> {{ template.channel_display }}</p>
            <p><strong>主题/标题模板:</strong></p>
            <v-code class="pa-2 d-block mb-2" style="white-space: pre-wrap;">{{ template.subject_template }}</v-code>
            <p><strong>内容模板:</strong> ({{ template.channel === 'email' ? 'HTML/文本' : 'Markdown/JSON' }})</p>
            <v-code class="pa-2 d-block" style="white-space: pre-wrap; max-height: 300px; overflow-y: auto;">{{ template.body_template }}</v-code>
            <v-divider class="my-3"></v-divider>
            <v-card-actions>
                <v-chip small prepend-icon="mdi-update">最后更新: {{ formatDate(template.updated_at) }}</v-chip>
                <v-spacer></v-spacer>
                <v-btn icon="mdi-pencil" variant="text" color="info" @click="openTemplateDialog(template)" density="compact"></v-btn>
                <v-btn icon="mdi-delete" variant="text" color="error" @click="deleteTemplate(template)" density="compact"></v-btn>
            </v-card-actions>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card>

    <v-dialog v-model="templateDialog.show" max-width="900px" persistent scrollable>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ templateDialog.isEdit ? '编辑' : '添加' }}通知模板</span>
        </v-card-title>
        <v-card-text style="max-height: 70vh;">
          <v-form ref="templateFormRef">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="templateDialog.data.name"
                  label="模板名称 (用于识别)"
                  :rules="[rules.required]"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="templateDialog.data.event_type"
                  :items="availableEventTypes"
                  item-title="text"
                  item-value="value"
                  label="事件类型"
                  :rules="[rules.required]"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="templateDialog.data.channel"
                  :items="availableChannels"
                  item-title="text"
                  item-value="value"
                  label="通知渠道"
                  :rules="[rules.required]"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </v-col>
               <v-col cols="12" md="6">
                <v-switch
                  v-model="templateDialog.data.is_active"
                  label="激活此模板"
                  color="success"
                  density="compact"
                ></v-switch>
              </v-col>
            </v-row>
            
            <v-text-field
              v-model="templateDialog.data.subject_template"
              label="主题/标题模板"
              :rules="[rules.required]"
              variant="outlined"
              density="compact"
              class="mt-2"
              hint="支持Django模板变量, 如 {{ ticket.title }}"
              persistent-hint
            ></v-text-field>

            <v-textarea
              v-model="templateDialog.data.body_template"
              label="内容模板"
              :rules="[rules.required]"
              rows="10"
              variant="outlined"
              class="mt-4"
              hint="邮件支持HTML, Webhook通常为Markdown或JSON结构。使用Django模板变量, 如 {{ ticket.description }} 或 {{ user_actor.username }}"
              persistent-hint
            ></v-textarea>
            <div class="mt-2 text-caption">
                可用变量示例 (具体可用变量取决于事件类型): <br>
                <code>{{ ticket.id }}</code>, <code>{{ ticket.title }}</code>, <code>{{ ticket.status_display }}</code>, <code>{{ ticket.company.name }}</code>, <br>
                <code>{{ user_actor.username }}</code> (操作用户), <code>{{ ticket_creator_user.username }}</code> (工单创建者), <br>
                <code>{{ reply.content }}</code> (回复内容), <code>{{ site_url }}</code>, <code>{{ ticket_url }}</code>, <code>{{ company_ticket_url }}</code>
            </div>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="blue-darken-1" variant="text" @click="closeTemplateDialog">取消</v-btn>
          <v-btn color="blue-darken-1" variant="elevated" @click="saveTemplate" :loading="templateDialog.loading">保存模板</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

     <v-dialog v-model="deleteDialog.show" max-width="500px">
        <v-card>
            <v-card-title class="text-h5">确认删除</v-card-title>
            <v-card-text>您确定要删除此通知模板吗？</v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue-darken-1" variant="text" @click="deleteDialog.show = false">取消</v-btn>
                <v-btn color="red-darken-1" variant="elevated" @click="confirmDeleteTemplate" :loading="deleteDialog.loading">删除</v-btn>
                <v-spacer></v-spacer>
            </v-card-actions>
        </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import api from '@/api';
import { useSnackbarStore } from '@/store/snackbar';

const route = useRoute();
const snackbarStore = useSnackbarStore();
const companyId = ref(route.params.companyId);

const loadingCompany = ref(false);
const loadingTemplates = ref(false);
const company = ref(null);
const templates = ref([]);
const templateFormRef = ref(null);

const templateDialog = ref({
  show: false,
  isEdit: false,
  loading: false,
  data: {
    id: null,
    name: '',
    event_type: '',
    channel: '',
    is_active: true,
    subject_template: '',
    body_template: '',
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

// These should match NotificationTemplate.EVENT_TYPE_CHOICES and CHANNEL_CHOICES from backend
const availableEventTypes = ref([
    { text: '工单创建', value: 'ticket_created' },
    { text: '工单状态变更', value: 'ticket_status_changed' },
    { text: '技术支持回复', value: 'ticket_replied_by_support' },
    { text: '客户回复', value: 'ticket_replied_by_customer' },
    { text: '工单分配', value: 'ticket_assigned' },
    { text: '工单转移', value: 'ticket_transferred' },
    { text: '工单暂停', value: 'ticket_paused' },
    { text: 'SLA首次响应预警', value: 'ticket_sla_ir_warning' },
    { text: 'SLA首次响应错过', value: 'ticket_sla_ir_missed' },
    { text: 'SLA解决预警', value: 'ticket_sla_resolution_warning' },
    { text: 'SLA解决错过', value: 'ticket_sla_resolution_missed' },
    { text: '工单闲置预警', value: 'ticket_idle_warning' },
]);
const availableChannels = ref([
    { text: '邮件 (Email)', value: 'email' },
    { text: '飞书 (Feishu)', value: 'feishu' },
    { text: '企业微信 (Enterprise WeChat)', value: 'enterprise_wechat' },
]);

const getChannelIcon = (channel) => {
    if (channel === 'email') return 'mdi-email-outline';
    if (channel === 'feishu') return 'mdi-alpha-f-box-outline';
    if (channel === 'enterprise_wechat') return 'mdi-wechat';
    return 'mdi-bell-outline';
};

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString('zh-CN', options);
}

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

async function fetchTemplates() {
  if (!companyId.value) return;
  loadingTemplates.value = true;
  try {
    // Fetch templates specific to this company. Backend might also return global templates if applicable.
    const response = await api.get(`/notification-templates/?company_id=${companyId.value}`);
    templates.value = response.data.results || response.data;
  } catch (error) {
    console.error("获取通知模板失败:", error);
    snackbarStore.setSnackbar({ text: `获取通知模板失败: ${error.message || error}`, color: 'error' });
    templates.value = [];
  } finally {
    loadingTemplates.value = false;
  }
}

function openTemplateDialog(template = null) {
  if (template) {
    templateDialog.value.isEdit = true;
    templateDialog.value.data = { ...template };
  } else {
    templateDialog.value.isEdit = false;
    templateDialog.value.data = {
      id: null,
      name: '',
      event_type: '',
      channel: '',
      is_active: true,
      subject_template: '',
      body_template: '',
      company: companyId.value, // Pre-fill company for new templates
    };
  }
  templateDialog.value.show = true;
}

function closeTemplateDialog() {
  templateDialog.value.show = false;
  templateFormRef.value?.resetValidation();
}

async function saveTemplate() {
  const { valid } = await templateFormRef.value.validate();
  if (!valid) return;

  templateDialog.value.loading = true;
  let payload = { ...templateDialog.value.data };
  if (!payload.company) { // Ensure company is set
    payload.company = companyId.value;
  }

  try {
    if (templateDialog.value.isEdit && payload.id) {
      await api.put(`/notification-templates/${payload.id}/`, payload);
      snackbarStore.setSnackbar({ text: '通知模板更新成功！', color: 'success' });
    } else {
      delete payload.id;
      await api.post('/notification-templates/', payload);
      snackbarStore.setSnackbar({ text: '通知模板添加成功！', color: 'success' });
    }
    fetchTemplates(); // Refresh list
    closeTemplateDialog();
  } catch (error) {
    console.error("保存通知模板失败:", error.response?.data || error.message);
    snackbarStore.setSnackbar({ text: `保存通知模板失败: ${error.response?.data?.detail || error.message || error}`, color: 'error' });
  } finally {
    templateDialog.value.loading = false;
  }
}

function deleteTemplate(template) {
    deleteDialog.value.itemToDelete = template;
    deleteDialog.value.show = true;
}

async function confirmDeleteTemplate() {
    if (!deleteDialog.value.itemToDelete) return;
    deleteDialog.value.loading = true;
    try {
        await api.delete(`/notification-templates/${deleteDialog.value.itemToDelete.id}/`);
        snackbarStore.setSnackbar({ text: '通知模板已删除。', color: 'success' });
        fetchTemplates(); // Refresh list
    } catch (error) {
        console.error("删除通知模板失败:", error);
        snackbarStore.setSnackbar({ text: `删除通知模板失败: ${error.message || error}`, color: 'error' });
    } finally {
        deleteDialog.value.loading = false;
        deleteDialog.value.show = false;
        deleteDialog.value.itemToDelete = null;
    }
}

onMounted(() => {
  if (companyId.value) {
    fetchCompanyDetails();
    fetchTemplates();
  } else {
    snackbarStore.setSnackbar({ text: '未提供公司ID，无法加载通知模板。', color: 'warning' });
  }
});

watch(() => route.params.companyId, (newId) => {
  if (newId) {
    companyId.value = newId;
    fetchCompanyDetails();
    fetchTemplates();
  }
});

</script>

<style scoped>
.v-code {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-family: monospace;
}
</style>
