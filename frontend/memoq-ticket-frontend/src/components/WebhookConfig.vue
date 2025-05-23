// 实现公司Webhook配置与测试组件

<template>
  <div class="webhook-config-container">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>{{ company ? `${company.name} - Webhook配置` : 'Webhook配置' }}</span>
        <v-btn
          color="primary"
          @click="addNewWebhook"
        >
          添加Webhook
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        <v-alert
          v-if="webhooks.length === 0"
          type="info"
          class="mb-4"
        >
          该公司尚未配置任何Webhook。Webhook可用于在工单状态变更、回复添加等事件发生时通知外部系统。
        </v-alert>
        
        <v-expansion-panels v-model="openPanel">
          <v-expansion-panel
            v-for="(webhook, index) in webhooks"
            :key="webhook.id"
          >
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <v-chip
                  :color="webhook.is_active ? 'success' : 'grey'"
                  class="mr-2"
                  size="small"
                >
                  {{ webhook.is_active ? '已启用' : '已禁用' }}
                </v-chip>
                <span>{{ getEventTypeDisplay(webhook.event_type) }}</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-form ref="webhookForms">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="webhook.event_type"
                      :items="eventTypeOptions"
                      item-title="text"
                      item-value="value"
                      label="事件类型"
                      required
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="webhook.is_active"
                      color="success"
                      label="启用"
                      hide-details
                    />
                  </v-col>
                </v-row>
                
                <v-text-field
                  v-model="webhook.url_template"
                  label="URL模板"
                  placeholder="https://example.com/webhook?ticket_id={ticket_id}"
                  hint="支持使用{ticket_id}、{ticket_title}等变量"
                  persistent-hint
                  required
                />
                
                <v-textarea
                  v-model="webhook.payload_template_str"
                  label="Payload模板 (JSON)"
                  placeholder='{"ticket_id": "{ticket_id}", "title": "{ticket_title}", "event": "{event_type}"}'
                  hint="JSON格式，支持使用{ticket_id}、{ticket_title}等变量"
                  persistent-hint
                  rows="5"
                />
                
                <v-textarea
                  v-model="webhook.headers_template_str"
                  label="Headers模板 (JSON)"
                  placeholder='{"Content-Type": "application/json", "X-API-Key": "your-api-key"}'
                  hint="JSON格式，默认会添加Content-Type: application/json"
                  persistent-hint
                  rows="3"
                />
                
                <v-row class="mt-4">
                  <v-col>
                    <v-btn
                      color="primary"
                      @click="saveWebhook(webhook, index)"
                      :loading="saving === index"
                    >
                      保存
                    </v-btn>
                    <v-btn
                      color="error"
                      class="ml-2"
                      @click="deleteWebhook(webhook, index)"
                      :loading="deleting === index"
                    >
                      删除
                    </v-btn>
                  </v-col>
                </v-row>
                
                <!-- Webhook测试区域 -->
                <v-divider class="my-4" />
                <h3 class="text-h6 mb-3">测试Webhook</h3>
                
                <v-alert
                  v-if="testResults[index]"
                  :type="testResults[index].success ? 'success' : 'error'"
                  class="mb-4"
                >
                  {{ testResults[index].message }}
                </v-alert>
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="testData[index].ticketId"
                      :items="availableTickets"
                      item-title="display"
                      item-value="id"
                      label="选择测试工单"
                      hint="选择一个现有工单进行测试"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-btn
                      color="info"
                      @click="testWebhook(webhook, index)"
                      :loading="testing === index"
                      :disabled="!testData[index].ticketId"
                    >
                      测试Webhook
                    </v-btn>
                  </v-col>
                </v-row>
                
                <v-expand-transition>
                  <div v-if="testResults[index] && testResults[index].details">
                    <v-divider class="my-3" />
                    <h4 class="text-subtitle-1 mb-2">测试详情</h4>
                    
                    <v-card outlined class="mb-3">
                      <v-card-title class="text-subtitle-2">请求URL</v-card-title>
                      <v-card-text class="pa-3 bg-grey-lighten-4">
                        <pre>{{ testResults[index].details.url }}</pre>
                      </v-card-text>
                    </v-card>
                    
                    <v-card outlined class="mb-3">
                      <v-card-title class="text-subtitle-2">请求Headers</v-card-title>
                      <v-card-text class="pa-3 bg-grey-lighten-4">
                        <pre>{{ JSON.stringify(testResults[index].details.headers, null, 2) }}</pre>
                      </v-card-text>
                    </v-card>
                    
                    <v-card outlined class="mb-3">
                      <v-card-title class="text-subtitle-2">请求Payload</v-card-title>
                      <v-card-text class="pa-3 bg-grey-lighten-4">
                        <pre>{{ JSON.stringify(testResults[index].details.payload, null, 2) }}</pre>
                      </v-card-text>
                    </v-card>
                    
                    <v-card outlined v-if="testResults[index].details.response">
                      <v-card-title class="text-subtitle-2">响应结果</v-card-title>
                      <v-card-text class="pa-3 bg-grey-lighten-4">
                        <pre>{{ JSON.stringify(testResults[index].details.response, null, 2) }}</pre>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-expand-transition>
              </v-form>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
    
    <!-- 添加Webhook对话框 -->
    <v-dialog v-model="showAddDialog" max-width="600px">
      <v-card>
        <v-card-title>添加新Webhook</v-card-title>
        <v-card-text>
          <v-form ref="newWebhookForm">
            <v-select
              v-model="newWebhook.event_type"
              :items="eventTypeOptions"
              item-title="text"
              item-value="value"
              label="事件类型"
              required
            />
            
            <v-text-field
              v-model="newWebhook.url_template"
              label="URL模板"
              placeholder="https://example.com/webhook?ticket_id={ticket_id}"
              hint="支持使用{ticket_id}、{ticket_title}等变量"
              persistent-hint
              required
            />
            
            <v-textarea
              v-model="newWebhook.payload_template_str"
              label="Payload模板 (JSON)"
              placeholder='{"ticket_id": "{ticket_id}", "title": "{ticket_title}", "event": "{event_type}"}'
              hint="JSON格式，支持使用{ticket_id}、{ticket_title}等变量"
              persistent-hint
              rows="5"
            />
            
            <v-textarea
              v-model="newWebhook.headers_template_str"
              label="Headers模板 (JSON)"
              placeholder='{"Content-Type": "application/json", "X-API-Key": "your-api-key"}'
              hint="JSON格式，默认会添加Content-Type: application/json"
              persistent-hint
              rows="3"
            />
            
            <v-switch
              v-model="newWebhook.is_active"
              color="success"
              label="启用"
              hide-details
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" text @click="showAddDialog = false">取消</v-btn>
          <v-btn 
            color="primary" 
            @click="createWebhook" 
            :loading="creating"
          >
            创建
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 全局提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
    >
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn
          color="white"
          text
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue';
import api from '@/api';

export default {
  name: 'WebhookConfig',
  props: {
    companyId: {
      type: [Number, String],
      required: true
    }
  },
  setup(props) {
    const company = ref(null);
    const webhooks = ref([]);
    const openPanel = ref(null);
    const showAddDialog = ref(false);
    const webhookForms = ref([]);
    const newWebhookForm = ref(null);
    
    // 加载状态
    const loading = ref(false);
    const saving = ref(null);
    const deleting = ref(null);
    const creating = ref(false);
    const testing = ref(null);
    
    // 测试相关
    const availableTickets = ref([]);
    const testData = reactive({});
    const testResults = reactive({});
    
    // 提示信息
    const snackbar = reactive({
      show: false,
      text: '',
      color: 'success',
      timeout: 3000
    });
    
    // 新Webhook模板
    const newWebhook = reactive({
      company: props.companyId,
      event_type: 'ticket_created',
      url_template: '',
      payload_template_str: '{"ticket_id": "{ticket_id}", "title": "{ticket_title}", "event": "{event_type}"}',
      headers_template_str: '{"Content-Type": "application/json"}',
      is_active: true
    });
    
    // 事件类型选项
    const eventTypeOptions = [
      { text: '工单创建', value: 'ticket_created' },
      { text: '工单状态变更', value: 'ticket_status_changed' },
      { text: '技术支持回复', value: 'support_replied' },
      { text: '客户跟进', value: 'customer_followed_up' }
    ];
    
    // 获取事件类型显示名称
    const getEventTypeDisplay = (eventType) => {
      const option = eventTypeOptions.find(opt => opt.value === eventType);
      return option ? option.text : eventType;
    };
    
    // 显示提示信息
    const showMessage = (text, color = 'success') => {
      snackbar.text = text;
      snackbar.color = color;
      snackbar.show = true;
    };
    
    // 获取公司信息
    const fetchCompany = async () => {
      try {
        const response = await api.get(`/companies/${props.companyId}/`);
        company.value = response.data;
      } catch (error) {
        console.error('获取公司信息失败:', error);
        showMessage('获取公司信息失败', 'error');
      }
    };
    
    // 获取Webhook列表
    const fetchWebhooks = async () => {
      loading.value = true;
      try {
        const response = await api.get(`/companies/${props.companyId}/webhook-templates/`);
        webhooks.value = response.data.map(webhook => ({
          ...webhook,
          payload_template_str: webhook.payload_template ? JSON.stringify(webhook.payload_template, null, 2) : '',
          headers_template_str: webhook.headers_template ? JSON.stringify(webhook.headers_template, null, 2) : ''
        }));
        
        // 初始化测试数据
        webhooks.value.forEach((_, index) => {
          testData[index] = { ticketId: null };
          testResults[index] = null;
        });
      } catch (error) {
        console.error('获取Webhook列表失败:', error);
        showMessage('获取Webhook列表失败', 'error');
      } finally {
        loading.value = false;
      }
    };
    
    // 获取可用于测试的工单列表
    const fetchTestTickets = async () => {
      try {
        const response = await api.get(`/companies/${props.companyId}/tickets/`, {
          params: { limit: 10, ordering: '-created_at' }
        });
        availableTickets.value = (response.data.results || []).map(ticket => ({
          id: ticket.id,
          display: `#${ticket.id} - ${ticket.title}`
        }));
      } catch (error) {
        console.error('获取测试工单列表失败:', error);
      }
    };
    
    // 保存Webhook
    const saveWebhook = async (webhook, index) => {
      saving.value = index;
      try {
        // 处理JSON字符串转换
        const payload = webhook.payload_template_str ? JSON.parse(webhook.payload_template_str) : null;
        const headers = webhook.headers_template_str ? JSON.parse(webhook.headers_template_str) : null;
        
        const data = {
          ...webhook,
          payload_template: payload,
          headers_template: headers
        };
        
        // 删除字符串版本的字段
        delete data.payload_template_str;
        delete data.headers_template_str;
        
        const response = await api.put(`/webhook-templates/${webhook.id}/`, data);
        
        // 更新本地数据
        webhooks.value[index] = {
          ...response.data,
          payload_template_str: response.data.payload_template ? JSON.stringify(response.data.payload_template, null, 2) : '',
          headers_template_str: response.data.headers_template ? JSON.stringify(response.data.headers_template, null, 2) : ''
        };
        
        showMessage('Webhook保存成功');
      } catch (error) {
        console.error('保存Webhook失败:', error);
        showMessage('保存Webhook失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        saving.value = null;
      }
    };
    
    // 删除Webhook
    const deleteWebhook = async (webhook, index) => {
      if (!confirm(`确定要删除"${getEventTypeDisplay(webhook.event_type)}"的Webhook吗？`)) {
        return;
      }
      
      deleting.value = index;
      try {
        await api.delete(`/webhook-templates/${webhook.id}/`);
        
        // 从列表中移除
        webhooks.value.splice(index, 1);
        
        // 更新测试数据
        Object.keys(testData).forEach(key => {
          if (parseInt(key) > index) {
            testData[parseInt(key) - 1] = testData[key];
            testResults[parseInt(key) - 1] = testResults[key];
            delete testData[key];
            delete testResults[key];
          }
        });
        
        showMessage('Webhook删除成功');
      } catch (error) {
        console.error('删除Webhook失败:', error);
        showMessage('删除Webhook失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        deleting.value = null;
      }
    };
    
    // 添加新Webhook
    const addNewWebhook = () => {
      // 重置表单
      newWebhook.url_template = '';
      newWebhook.payload_template_str = '{"ticket_id": "{ticket_id}", "title": "{ticket_title}", "event": "{event_type}"}';
      newWebhook.headers_template_str = '{"Content-Type": "application/json"}';
      newWebhook.event_type = 'ticket_created';
      newWebhook.is_active = true;
      
      showAddDialog.value = true;
    };
    
    // 创建Webhook
    const createWebhook = async () => {
      creating.value = true;
      try {
        // 处理JSON字符串转换
        const payload = newWebhook.payload_template_str ? JSON.parse(newWebhook.payload_template_str) : null;
        const headers = newWebhook.headers_template_str ? JSON.parse(newWebhook.headers_template_str) : null;
        
        const data = {
          ...newWebhook,
          company: props.companyId,
          payload_template: payload,
          headers_template: headers
        };
        
        // 删除字符串版本的字段
        delete data.payload_template_str;
        delete data.headers_template_str;
        
        const response = await api.post('/webhook-templates/', data);
        
        // 添加到列表
        webhooks.value.push({
          ...response.data,
          payload_template_str: response.data.payload_template ? JSON.stringify(response.data.payload_template, null, 2) : '',
          headers_template_str: response.data.headers_template ? JSON.stringify(response.data.headers_template, null, 2) : ''
        });
        
        // 初始化新的测试数据
        const newIndex = webhooks.value.length - 1;
        testData[newIndex] = { ticketId: null };
        testResults[newIndex] = null;
        
        showAddDialog.value = false;
        showMessage('Webhook创建成功');
        
        // 打开新创建的面板
        openPanel.value = newIndex;
      } catch (error) {
        console.error('创建Webhook失败:', error);
        showMessage('创建Webhook失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        creating.value = false;
      }
    };
    
    // 测试Webhook
    const testWebhook = async (webhook, index) => {
      if (!testData[index].ticketId) {
        showMessage('请选择一个测试工单', 'warning');
        return;
      }
      
      testing.value = index;
      try {
        // 处理JSON字符串转换
        const payload = webhook.payload_template_str ? JSON.parse(webhook.payload_template_str) : null;
        const headers = webhook.headers_template_str ? JSON.parse(webhook.headers_template_str) : null;
        
        const testPayload = {
          webhook_id: webhook.id,
          ticket_id: testData[index].ticketId,
          event_type: webhook.event_type,
          url_template: webhook.url_template,
          payload_template: payload,
          headers_template: headers
        };
        
        const response = await api.post(`/webhook-templates/${webhook.id}/test/`, testPayload);
        
        testResults[index] = {
          success: response.data.success,
          message: response.data.success ? 'Webhook测试成功！' : `Webhook测试失败: ${response.data.error}`,
          details: {
            url: response.data.url,
            headers: response.data.headers,
            payload: response.data.payload,
            response: response.data.response
          }
        };
      } catch (error) {
        console.error('测试Webhook失败:', error);
        testResults[index] = {
          success: false,
          message: '测试Webhook失败: ' + (error.response?.data?.detail || error.message)
        };
      } finally {
        testing.value = null;
      }
    };
    
    onMounted(async () => {
      await fetchCompany();
      await Promise.all([fetchWebhooks(), fetchTestTickets()]);
    });
    
    return {
      company,
      webhooks,
      openPanel,
      showAddDialog,
      webhookForms,
      newWebhookForm,
      loading,
      saving,
      deleting,
      creating,
      testing,
      availableTickets,
      testData,
      testResults,
      snackbar,
      newWebhook,
      eventTypeOptions,
      getEventTypeDisplay,
      fetchWebhooks,
      saveWebhook,
      deleteWebhook,
      addNewWebhook,
      createWebhook,
      testWebhook
    };
  }
};
</script>

<style scoped>
.webhook-config-container {
  max-width: 1200px;
  margin: 0 auto;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 0.9rem;
}
</style>
