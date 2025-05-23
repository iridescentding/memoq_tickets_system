<!-- 邮件系统配置组件 -->
<template>
  <div>
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>邮件系统配置</span>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          prepend-icon="mdi-email-check"
          @click="testEmailDialog = true"
          :disabled="!hasEmailConfig"
        >
          测试邮件发送
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-alert
          v-if="error"
          type="error"
          class="mb-4"
          dismissible
        >
          {{ error }}
        </v-alert>

        <v-alert
          v-if="success"
          type="success"
          class="mb-4"
          dismissible
        >
          {{ success }}
        </v-alert>

        <div v-if="loading" class="d-flex justify-center align-center my-4">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <v-form ref="form" v-model="valid" @submit.prevent="saveEmailConfig">
          <v-card-subtitle class="px-0 font-weight-bold">SMTP服务器配置</v-card-subtitle>
          
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="emailConfig.smtp_host"
                label="SMTP服务器地址"
                :rules="[v => !!v || 'SMTP服务器地址不能为空']"
                required
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="emailConfig.smtp_port"
                label="SMTP端口"
                type="number"
                :rules="[v => !!v || 'SMTP端口不能为空']"
                required
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="emailConfig.smtp_username"
                label="SMTP用户名"
                :rules="[v => !!v || 'SMTP用户名不能为空']"
                required
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="emailConfig.smtp_password"
                label="SMTP密码"
                type="password"
                :rules="[v => !!v || 'SMTP密码不能为空']"
                required
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-switch
                v-model="emailConfig.use_tls"
                label="使用TLS加密"
                color="primary"
              ></v-switch>
            </v-col>
            <v-col cols="12" md="6">
              <v-switch
                v-model="emailConfig.use_ssl"
                label="使用SSL加密"
                color="primary"
              ></v-switch>
            </v-col>
          </v-row>

          <v-card-subtitle class="px-0 font-weight-bold mt-4">发件人设置</v-card-subtitle>
          
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="emailConfig.from_email"
                label="发件人邮箱"
                :rules="[
                  v => !!v || '发件人邮箱不能为空',
                  v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || '请输入有效的邮箱地址'
                ]"
                required
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="emailConfig.from_name"
                label="发件人名称"
                :rules="[v => !!v || '发件人名称不能为空']"
                required
              ></v-text-field>
            </v-col>
          </v-row>

          <v-card-subtitle class="px-0 font-weight-bold mt-4">邮件通知设置</v-card-subtitle>
          
          <v-row>
            <v-col cols="12" md="6">
              <v-switch
                v-model="emailConfig.notify_on_ticket_created"
                label="工单创建时发送邮件"
                color="primary"
              ></v-switch>
            </v-col>
            <v-col cols="12" md="6">
              <v-switch
                v-model="emailConfig.notify_on_ticket_updated"
                label="工单更新时发送邮件"
                color="primary"
              ></v-switch>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" md="6">
              <v-switch
                v-model="emailConfig.notify_on_reply_added"
                label="新回复时发送邮件"
                color="primary"
              ></v-switch>
            </v-col>
            <v-col cols="12" md="6">
              <v-switch
                v-model="emailConfig.notify_on_status_changed"
                label="状态变更时发送邮件"
                color="primary"
              ></v-switch>
            </v-col>
          </v-row>

          <v-card-actions class="px-0 mt-4">
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              type="submit"
              :loading="submitting"
              :disabled="!valid || submitting"
            >
              保存配置
            </v-btn>
          </v-card-actions>
        </v-form>
      </v-card-text>
    </v-card>

    <!-- 邮件模板管理 -->
    <v-card class="mt-6">
      <v-card-title class="d-flex align-center">
        <span>邮件模板管理</span>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openTemplateDialog()"
          :disabled="!hasEmailConfig"
        >
          新建模板
        </v-btn>
      </v-card-title>

      <v-card-text>
        <div v-if="loadingTemplates" class="d-flex justify-center align-center my-4">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <v-data-table
          v-else
          :headers="templateHeaders"
          :items="emailTemplates"
          :items-per-page="5"
          class="elevation-1"
        >
          <template v-slot:item.template_type="{ item }">
            <v-chip :color="getTemplateTypeColor(item.template_type)" size="small">
              {{ item.template_type_display }}
            </v-chip>
          </template>
          <template v-slot:item.created_at="{ item }">
            {{ formatDate(item.created_at) }}
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              size="small"
              color="primary"
              @click="openTemplateDialog(item)"
            >
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              color="error"
              @click="openDeleteTemplateDialog(item)"
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 测试邮件发送对话框 -->
    <v-dialog v-model="testEmailDialog" max-width="600px">
      <v-card>
        <v-card-title>测试邮件发送</v-card-title>
        <v-card-text>
          <v-form ref="testEmailForm" v-model="validTestEmail">
            <v-text-field
              v-model="testEmail.to_email"
              label="收件人邮箱"
              :rules="[
                v => !!v || '收件人邮箱不能为空',
                v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || '请输入有效的邮箱地址'
              ]"
              required
            ></v-text-field>
            <v-text-field
              v-model="testEmail.subject"
              label="邮件主题"
              :rules="[v => !!v || '邮件主题不能为空']"
              required
            ></v-text-field>
            <v-textarea
              v-model="testEmail.content"
              label="邮件内容"
              :rules="[v => !!v || '邮件内容不能为空']"
              rows="5"
              required
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="testEmailDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            :loading="submitting"
            :disabled="!validTestEmail || submitting"
            @click="sendTestEmail"
          >
            发送测试邮件
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 邮件模板编辑对话框 -->
    <v-dialog v-model="templateDialog" max-width="800px">
      <v-card>
        <v-card-title>
          {{ editedTemplateIndex === -1 ? '新建邮件模板' : '编辑邮件模板' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="templateForm" v-model="validTemplate">
            <v-text-field
              v-model="editedTemplate.name"
              label="模板名称"
              :rules="[v => !!v || '模板名称不能为空']"
              required
            ></v-text-field>
            
            <v-select
              v-model="editedTemplate.template_type"
              :items="templateTypes"
              item-title="text"
              item-value="value"
              label="模板类型"
              :rules="[v => !!v || '请选择模板类型']"
              required
            ></v-select>
            
            <v-text-field
              v-model="editedTemplate.subject"
              label="邮件主题"
              :rules="[v => !!v || '邮件主题不能为空']"
              required
            ></v-text-field>
            
            <v-card-subtitle class="px-0">
              模板内容
              <v-tooltip location="top">
                <template v-slot:activator="{ props }">
                  <v-icon v-bind="props" size="small" class="ml-1">mdi-information-outline</v-icon>
                </template>
                <div>
                  <p>可用的变量：</p>
                  <ul>
                    <li>{{ticket_id}} - 工单ID</li>
                    <li>{{ticket_title}} - 工单标题</li>
                    <li>{{ticket_url}} - 工单链接</li>
                    <li>{{customer_name}} - 客户名称</li>
                    <li>{{support_name}} - 技术支持名称</li>
                    <li>{{company_name}} - 公司名称</li>
                    <li>{{reply_content}} - 回复内容</li>
                  </ul>
                </div>
              </v-tooltip>
            </v-card-subtitle>
            
            <v-textarea
              v-model="editedTemplate.content"
              label="HTML内容"
              :rules="[v => !!v || '模板内容不能为空']"
              rows="10"
              required
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="templateDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            :loading="submitting"
            :disabled="!validTemplate || submitting"
            @click="saveEmailTemplate"
          >
            保存模板
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除模板确认对话框 -->
    <v-dialog v-model="deleteTemplateDialog" max-width="400px">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          您确定要删除邮件模板 <strong>{{ editedTemplate.name }}</strong> 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="deleteTemplateDialog = false">取消</v-btn>
          <v-btn
            color="error"
            :loading="submitting"
            @click="deleteEmailTemplate"
          >
            确认删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';
import api from '@/api';
import { format } from 'date-fns';

export default {
  name: 'EmailSystemConfig',
  props: {
    companyId: {
      type: [Number, String],
      required: false,
      default: null
    }
  },
  setup(props) {
    const loading = ref(false);
    const loadingTemplates = ref(false);
    const error = ref(null);
    const success = ref(null);
    const submitting = ref(false);
    const valid = ref(false);
    const form = ref(null);
    
    // 邮件配置
    const emailConfig = reactive({
      smtp_host: '',
      smtp_port: 587,
      smtp_username: '',
      smtp_password: '',
      use_tls: true,
      use_ssl: false,
      from_email: '',
      from_name: '',
      notify_on_ticket_created: true,
      notify_on_ticket_updated: true,
      notify_on_reply_added: true,
      notify_on_status_changed: true
    });
    
    // 测试邮件
    const testEmailDialog = ref(false);
    const validTestEmail = ref(false);
    const testEmailForm = ref(null);
    const testEmail = reactive({
      to_email: '',
      subject: '测试邮件 - MemoQ工单系统',
      content: '这是一封测试邮件，用于验证MemoQ工单系统的邮件发送功能是否正常。'
    });
    
    // 邮件模板
    const templateDialog = ref(false);
    const deleteTemplateDialog = ref(false);
    const validTemplate = ref(false);
    const templateForm = ref(null);
    const emailTemplates = ref([]);
    const editedTemplate = reactive({
      id: null,
      name: '',
      template_type: '',
      subject: '',
      content: '',
      company: null
    });
    const editedTemplateIndex = ref(-1);
    
    // 模板类型选项
    const templateTypes = [
      { text: '工单创建通知', value: 'ticket_created' },
      { text: '工单更新通知', value: 'ticket_updated' },
      { text: '新回复通知', value: 'reply_added' },
      { text: '状态变更通知', value: 'status_changed' }
    ];
    
    // 模板表头
    const templateHeaders = [
      { title: '模板名称', key: 'name', sortable: true },
      { title: '模板类型', key: 'template_type', sortable: true },
      { title: '邮件主题', key: 'subject', sortable: false },
      { title: '创建时间', key: 'created_at', sortable: true },
      { title: '操作', key: 'actions', sortable: false }
    ];
    
    // 计算属性：是否有邮件配置
    const hasEmailConfig = computed(() => {
      return emailConfig.smtp_host && 
             emailConfig.smtp_username && 
             emailConfig.from_email;
    });
    
    // 获取邮件配置
    const fetchEmailConfig = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        let endpoint = '/email-config/';
        if (props.companyId) {
          endpoint = `/companies/${props.companyId}/email-config/`;
        }
        
        const response = await api.get(endpoint);
        if (response.data && Object.keys(response.data).length > 0) {
          Object.assign(emailConfig, response.data);
        }
      } catch (err) {
        console.error('获取邮件配置失败:', err);
        error.value = '获取邮件配置失败，请稍后重试';
      } finally {
        loading.value = false;
      }
    };
    
    // 保存邮件配置
    const saveEmailConfig = async () => {
      if (!valid.value) return;
      
      submitting.value = true;
      error.value = null;
      success.value = null;
      
      try {
        let endpoint = '/email-config/';
        if (props.companyId) {
          endpoint = `/companies/${props.companyId}/email-config/`;
        }
        
        await api.post(endpoint, emailConfig);
        success.value = '邮件配置保存成功';
      } catch (err) {
        console.error('保存邮件配置失败:', err);
        error.value = '保存邮件配置失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 发送测试邮件
    const sendTestEmail = async () => {
      if (!validTestEmail.value) return;
      
      submitting.value = true;
      error.value = null;
      success.value = null;
      
      try {
        let endpoint = '/email-config/test/';
        if (props.companyId) {
          endpoint = `/companies/${props.companyId}/email-config/test/`;
        }
        
        await api.post(endpoint, testEmail);
        success.value = '测试邮件发送成功，请检查收件箱';
        testEmailDialog.value = false;
      } catch (err) {
        console.error('发送测试邮件失败:', err);
        error.value = '发送测试邮件失败，请检查邮件配置';
      } finally {
        submitting.value = false;
      }
    };
    
    // 获取邮件模板列表
    const fetchEmailTemplates = async () => {
      loadingTemplates.value = true;
      
      try {
        let endpoint = '/email-templates/';
        if (props.companyId) {
          endpoint = `/companies/${props.companyId}/email-templates/`;
        }
        
        const response = await api.get(endpoint);
        emailTemplates.value = response.data.results || [];
      } catch (err) {
        console.error('获取邮件模板失败:', err);
        error.value = '获取邮件模板失败，请稍后重试';
      } finally {
        loadingTemplates.value = false;
      }
    };
    
    // 打开模板编辑对话框
    const openTemplateDialog = (template = null) => {
      if (template) {
        editedTemplateIndex.value = emailTemplates.value.indexOf(template);
        Object.assign(editedTemplate, template);
      } else {
        editedTemplateIndex.value = -1;
        editedTemplate.id = null;
        editedTemplate.name = '';
        editedTemplate.template_type = '';
        editedTemplate.subject = '';
        editedTemplate.content = '';
        editedTemplate.company = props.companyId || null;
      }
      
      templateDialog.value = true;
      
      // 等待DOM更新后重置表单验证
      setTimeout(() => {
        if (templateForm.value) templateForm.value.resetValidation();
      });
    };
    
    // 打开删除模板对话框
    const openDeleteTemplateDialog = (template) => {
      editedTemplateIndex.value = emailTemplates.value.indexOf(template);
      Object.assign(editedTemplate, template);
      deleteTemplateDialog.value = true;
    };
    
    // 保存邮件模板
    const saveEmailTemplate = async () => {
      if (!validTemplate.value) return;
      
      submitting.value = true;
      error.value = null;
      success.value = null;
      
      try {
        let endpoint = '/email-templates/';
        
        if (editedTemplateIndex.value > -1) {
          // 更新模板
          endpoint += `${editedTemplate.id}/`;
          await api.put(endpoint, editedTemplate);
        } else {
          // 创建模板
          await api.post(endpoint, editedTemplate);
        }
        
        success.value = '邮件模板保存成功';
        templateDialog.value = false;
        
        // 重新获取模板列表
        await fetchEmailTemplates();
      } catch (err) {
        console.error('保存邮件模板失败:', err);
        error.value = '保存邮件模板失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 删除邮件模板
    const deleteEmailTemplate = async () => {
      submitting.value = true;
      error.value = null;
      
      try {
        await api.delete(`/email-templates/${editedTemplate.id}/`);
        
        success.value = '邮件模板删除成功';
        deleteTemplateDialog.value = false;
        
        // 重新获取模板列表
        await fetchEmailTemplates();
      } catch (err) {
        console.error('删除邮件模板失败:', err);
        error.value = '删除邮件模板失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 获取模板类型颜色
    const getTemplateTypeColor = (type) => {
      const colors = {
        'ticket_created': 'blue',
        'ticket_updated': 'green',
        'reply_added': 'purple',
        'status_changed': 'orange'
      };
      return colors[type] || 'grey';
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '未知';
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    };
    
    onMounted(() => {
      fetchEmailConfig();
      fetchEmailTemplates();
    });
    
    return {
      loading,
      loadingTemplates,
      error,
      success,
      submitting,
      valid,
      form,
      emailConfig,
      hasEmailConfig,
      testEmailDialog,
      validTestEmail,
      testEmailForm,
      testEmail,
      templateDialog,
      deleteTemplateDialog,
      validTemplate,
      templateForm,
      emailTemplates,
      editedTemplate,
      editedTemplateIndex,
      templateTypes,
      templateHeaders,
      fetchEmailConfig,
      saveEmailConfig,
      sendTestEmail,
      openTemplateDialog,
      openDeleteTemplateDialog,
      saveEmailTemplate,
      deleteEmailTemplate,
      getTemplateTypeColor,
      formatDate
    };
  }
};
</script>
