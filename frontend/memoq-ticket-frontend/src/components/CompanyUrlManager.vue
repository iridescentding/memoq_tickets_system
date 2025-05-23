// 实现公司专属工单URL生成和工单直达功能

<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>{{ company ? `${company.name} - 工单URL管理` : '工单URL管理' }}</span>
      </v-card-title>
      
      <v-card-text>
        <v-alert
          type="info"
          class="mb-4"
          icon="mdi-information-outline"
        >
          您可以为该公司生成专属工单提交URL和工单查看URL，方便客户直接访问。
        </v-alert>
        
        <!-- 公司工单URL配置 -->
        <v-form ref="urlFormRef">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="companyConfig.ticket_submission_url_slug"
                label="工单提交URL标识"
                hint="用于生成公司专属工单提交URL，只能包含字母、数字和连字符"
                persistent-hint
                :rules="[v => !!v || '请输入URL标识', v => /^[a-z0-9-]+$/.test(v) || 'URL标识只能包含小写字母、数字和连字符']"
                required
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-btn
                color="primary"
                class="mt-2"
                @click="saveUrlConfig"
                :loading="saving"
              >
                保存配置
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
        
        <!-- 生成的URL展示 -->
        <v-card
          v-if="companyConfig.ticket_submission_url_slug"
          outlined
          class="mt-4"
        >
          <v-card-title>公司专属URL</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="loginUrl"
                  label="登录URL"
                  readonly
                  append-inner-icon="mdi-content-copy"
                  @click:append-inner="copyToClipboard(loginUrl)"
                  hint="客户可通过此URL登录系统"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="ticketSubmissionUrl"
                  label="工单提交URL"
                  readonly
                  append-inner-icon="mdi-content-copy"
                  @click:append-inner="copyToClipboard(ticketSubmissionUrl)"
                  hint="客户可通过此URL直接提交工单"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="ticketListUrl"
                  label="工单列表URL"
                  readonly
                  append-inner-icon="mdi-content-copy"
                  @click:append-inner="copyToClipboard(ticketListUrl)"
                  hint="客户可通过此URL查看所有工单"
                  persistent-hint
                />
              </v-col>
            </v-row>
            
            <v-divider class="my-4" />
            
            <h3 class="text-h6 mb-3">工单直达URL格式</h3>
            <p class="text-body-1 mb-2">
              每个工单都有一个唯一的直达URL，格式如下：
            </p>
            <v-text-field
              :value="`${baseUrl}/${companyConfig.ticket_submission_url_slug}/[工单ID]`"
              label="工单直达URL格式"
              readonly
              hint="将[工单ID]替换为实际工单ID即可访问特定工单"
              persistent-hint
            />
            
            <v-alert
              type="warning"
              class="mt-4"
              icon="mdi-alert-circle-outline"
            >
              注意：访问这些URL的用户仍需要进行身份验证。未登录用户将被重定向到登录页面。
            </v-alert>
          </v-card-text>
        </v-card>
        
        <!-- 二维码生成 -->
        <v-card
          v-if="companyConfig.ticket_submission_url_slug"
          outlined
          class="mt-4"
        >
          <v-card-title>URL二维码</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4" class="text-center">
                <h4 class="text-subtitle-1 mb-2">登录URL</h4>
                <div ref="loginQrCode" class="qr-code-container mx-auto"></div>
                <v-btn
                  color="primary"
                  size="small"
                  class="mt-2"
                  @click="downloadQrCode('login')"
                >
                  下载二维码
                </v-btn>
              </v-col>
              <v-col cols="12" md="4" class="text-center">
                <h4 class="text-subtitle-1 mb-2">工单提交URL</h4>
                <div ref="submissionQrCode" class="qr-code-container mx-auto"></div>
                <v-btn
                  color="primary"
                  size="small"
                  class="mt-2"
                  @click="downloadQrCode('submission')"
                >
                  下载二维码
                </v-btn>
              </v-col>
              <v-col cols="12" md="4" class="text-center">
                <h4 class="text-subtitle-1 mb-2">工单列表URL</h4>
                <div ref="listQrCode" class="qr-code-container mx-auto"></div>
                <v-btn
                  color="primary"
                  size="small"
                  class="mt-2"
                  @click="downloadQrCode('list')"
                >
                  下载二维码
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>
    
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
  </v-container>
</template>

<script>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue';
import api from '@/api';
import QRCode from 'qrcode';

export default {
  name: 'CompanyUrlManager',
  props: {
    companyId: {
      type: [Number, String],
      required: true
    }
  },
  setup(props) {
    const company = ref(null);
    const companyConfig = reactive({
      ticket_submission_url_slug: '',
      company: props.companyId
    });
    const urlFormRef = ref(null);
    const saving = ref(false);
    
    // QR码引用
    const loginQrCode = ref(null);
    const submissionQrCode = ref(null);
    const listQrCode = ref(null);
    
    // 提示信息
    const snackbar = reactive({
      show: false,
      text: '',
      color: 'success',
      timeout: 3000
    });
    
    // 基础URL
    const baseUrl = computed(() => {
      return window.location.origin;
    });
    
    // 生成的URL
    const loginUrl = computed(() => {
      return `${baseUrl.value}/login/${companyConfig.ticket_submission_url_slug}`;
    });
    
    const ticketSubmissionUrl = computed(() => {
      return `${baseUrl.value}/submit-ticket/${companyConfig.ticket_submission_url_slug}`;
    });
    
    const ticketListUrl = computed(() => {
      return `${baseUrl.value}/tickets?company=${companyConfig.ticket_submission_url_slug}`;
    });
    
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
        
        // 如果公司有URL标识，则填充到表单
        if (company.value.ticket_submission_url_slug) {
          companyConfig.ticket_submission_url_slug = company.value.ticket_submission_url_slug;
        }
      } catch (error) {
        console.error('获取公司信息失败:', error);
        showMessage('获取公司信息失败', 'error');
      }
    };
    
    // 保存URL配置
    const saveUrlConfig = async () => {
      if (!urlFormRef.value.validate()) {
        return;
      }
      
      saving.value = true;
      try {
        const response = await api.patch(`/companies/${props.companyId}/`, {
          ticket_submission_url_slug: companyConfig.ticket_submission_url_slug
        });
        
        company.value = response.data;
        showMessage('URL配置保存成功');
        
        // 重新生成二维码
        generateQrCodes();
      } catch (error) {
        console.error('保存URL配置失败:', error);
        showMessage('保存URL配置失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        saving.value = false;
      }
    };
    
    // 复制到剪贴板
    const copyToClipboard = (text) => {
      navigator.clipboard.writeText(text)
        .then(() => {
          showMessage('已复制到剪贴板');
        })
        .catch(err => {
          console.error('复制失败:', err);
          showMessage('复制失败', 'error');
        });
    };
    
    // 生成二维码
    const generateQrCodes = async () => {
      if (!companyConfig.ticket_submission_url_slug) return;
      
      await nextTick();
      
      try {
        if (loginQrCode.value) {
          QRCode.toCanvas(loginQrCode.value, loginUrl.value, {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#ffffff'
            }
          });
        }
        
        if (submissionQrCode.value) {
          QRCode.toCanvas(submissionQrCode.value, ticketSubmissionUrl.value, {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#ffffff'
            }
          });
        }
        
        if (listQrCode.value) {
          QRCode.toCanvas(listQrCode.value, ticketListUrl.value, {
            width: 200,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#ffffff'
            }
          });
        }
      } catch (error) {
        console.error('生成二维码失败:', error);
      }
    };
    
    // 下载二维码
    const downloadQrCode = (type) => {
      let canvas;
      let filename;
      
      switch (type) {
        case 'login':
          canvas = loginQrCode.value;
          filename = `${company.value.name}-登录二维码.png`;
          break;
        case 'submission':
          canvas = submissionQrCode.value;
          filename = `${company.value.name}-工单提交二维码.png`;
          break;
        case 'list':
          canvas = listQrCode.value;
          filename = `${company.value.name}-工单列表二维码.png`;
          break;
        default:
          return;
      }
      
      if (!canvas) return;
      
      const link = document.createElement('a');
      link.download = filename;
      link.href = canvas.toDataURL('image/png');
      link.click();
    };
    
    // 监听URL标识变化，重新生成二维码
    watch(() => companyConfig.ticket_submission_url_slug, () => {
      if (companyConfig.ticket_submission_url_slug) {
        nextTick(() => {
          generateQrCodes();
        });
      }
    });
    
    onMounted(async () => {
      await fetchCompany();
      nextTick(() => {
        generateQrCodes();
      });
    });
    
    return {
      company,
      companyConfig,
      urlFormRef,
      saving,
      loginQrCode,
      submissionQrCode,
      listQrCode,
      snackbar,
      baseUrl,
      loginUrl,
      ticketSubmissionUrl,
      ticketListUrl,
      fetchCompany,
      saveUrlConfig,
      copyToClipboard,
      generateQrCodes,
      downloadQrCode
    };
  }
};
</script>

<style scoped>
.qr-code-container {
  width: 200px;
  height: 200px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
}
</style>
