<template>
  <v-container class="ticket-submit-container">
    <v-row justify="center">
      <v-col
        cols="12"
        md="10"
        lg="8"
      >
        <v-card class="ticket-submit-card">
          <v-card-title class="text-h5 text-center py-4">
            {{ companyName ? companyName + ' - ' : '' }}提交技术支持工单
          </v-card-title>
          <v-card-text>
            <v-form
              ref="ticketFormRef"
              v-model="validForm"
            >
              <v-text-field
                v-model="ticketForm.title"
                label="标题"
                :rules="rules.title"
                placeholder="请简要描述您的问题"
                required
                variant="outlined"
                density="compact"
              />

              <v-select
                v-model="ticketForm.category"
                label="问题类别"
                :items="categoryOptions"
                item-title="text"
                item-value="value"
                :rules="rules.category"
                placeholder="请选择问题类别"
                required
                variant="outlined"
                density="compact"
              />

              <v-textarea
                v-model="ticketForm.description"
                label="问题描述"
                :rules="rules.description"
                placeholder="请详细描述您遇到的问题，包括操作步骤、错误信息等"
                rows="6"
                required
                variant="outlined"
                density="compact"
              />

              <v-radio-group
                v-model="ticketForm.priority"
                label="优先级"
                :rules="rules.priority"
                inline
              >
                <v-radio
                  label="紧急"
                  :value="1"
                />
                <v-radio
                  label="高"
                  :value="2"
                />
                <v-radio
                  label="中"
                  :value="3"
                />
                <v-radio
                  label="低"
                  :value="4"
                />
                <v-radio
                  label="计划"
                  :value="5"
                />
              </v-radio-group>

              <v-select
                v-model="ticketForm.contact_method"
                label="联系方式"
                :items="contactMethodOptions"
                item-title="text"
                item-value="value"
                :rules="rules.contact_method"
                placeholder="请选择联系方式"
                required
                variant="outlined"
                density="compact"
              />

              <v-text-field
                v-model="ticketForm.contact_info"
                label="联系信息"
                :placeholder="contactPlaceholder"
                :rules="rules.contact_info"
                required
                variant="outlined"
                density="compact"
              />

              <v-file-input
                v-model="fileList"
                label="附件 (可选, 最多5个, 单个不超过10MB)"
                multiple
                chips
                show-size
                counter
                small-chips
                :rules="fileRules"
                accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt,.log,.zip,.rar"
                variant="outlined"
                density="compact"
              >
                <template #selection="{ fileNames }">
                  <template
                    v-for="fileName in fileNames"
                    :key="fileName"
                  >
                    <v-chip
                      small
                      label
                      color="primary"
                      class="me-2"
                    >
                      {{ fileName }}
                    </v-chip>
                  </template>
                </template>
              </v-file-input>

              <v-btn 
                color="primary" 
                block 
                :loading="loading" 
                :disabled="!validForm || loading" 
                class="mt-4"
                size="large"
                @click="submitForm"
              >
                提交工单
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
    >
      {{ snackbar.text }}
      <template #actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
// import axios from 'axios'; // Assuming global axios instance this.$axios

export default {
  name: 'TicketSubmit',
  setup() {
    const router = useRouter();
    const route = useRoute();
    const ticketFormRef = ref(null);
    const validForm = ref(false);
    const loading = ref(false);
    const companyName = ref('');
    const companyCode = ref('');

    const snackbar = reactive({
      show: false,
      text: '',
      color: 'success',
      timeout: 3000
    });

    const showSnackbar = (text, color = 'success', timeout = 3000) => {
      snackbar.text = text;
      snackbar.color = color;
      snackbar.timeout = timeout;
      snackbar.show = true;
    };

    const ticketForm = reactive({
      title: '',
      category: null,
      description: '',
      priority: 3,
      contact_method: 'email',
      contact_info: ''
    });

    const rules = {
      title: [
        v => !!v || '请输入工单标题',
        v => (v && v.length >= 5 && v.length <= 100) || '标题长度在5到100个字符之间'
      ],
      category: [v => !!v || '请选择问题类别'],
      description: [
        v => !!v || '请输入问题描述',
        v => (v && v.length >= 10) || '描述至少需要10个字符'
      ],
      priority: [v => v !== null || '请选择优先级'],
      contact_method: [v => !!v || '请选择联系方式'],
      contact_info: [v => !!v || '请输入联系信息']
    };

    const fileList = ref([]); // For v-file-input, this will hold File objects

    const fileRules = [
      (value) => !value || value.length <= 5 || '最多只能上传5个文件',
      (value) => {
        if (!value) return true;
        for (const file of value) {
          if (file.size > 10 * 1024 * 1024) return '单个文件不能超过10MB';
        }
        return true;
      }
    ];

    const categoryOptions = [
      { text: '软件安装', value: 'installation' },
      { text: '软件激活', value: 'activation' },
      { text: '功能使用', value: 'usage' },
      { text: '翻译问题', value: 'translation' },
      { text: '系统错误', value: 'error' },
      { text: '其他问题', value: 'other' }
    ];

    const contactMethodOptions = [
      { text: '邮箱', value: 'email' },
      { text: '微信', value: 'wechat' },
      { text: '企业微信', value: 'enterprise_wechat' },
      { text: '飞书', value: 'feishu' },
      { text: '电话', value: 'phone' }
    ];

    const contactPlaceholder = computed(() => {
      const placeholders = {
        email: '请输入您的邮箱地址',
        wechat: '请输入您的微信号',
        enterprise_wechat: '请输入您的企业微信ID',
        feishu: '请输入您的飞书ID',
        phone: '请输入您的电话号码'
      };
      return placeholders[ticketForm.contact_method] || '请输入联系信息';
    });

    const submitForm = async () => {
      // Vuetify form validation is typically handled by the :rules prop directly
      // and the form's v-model (validForm in this case)
      // const { valid } = await ticketFormRef.value.validate();
      // if (!valid) return;
      if (!validForm.value) {
        showSnackbar('请检查表单填写是否正确', 'error');
        return;
      }

      loading.value = true;
      const formData = new FormData();
      formData.append('title', ticketForm.title);
      formData.append('category', ticketForm.category);
      formData.append('description', ticketForm.description);
      formData.append('priority', ticketForm.priority);
      formData.append('contact_method', ticketForm.contact_method);
      formData.append('contact_info', ticketForm.contact_info);

      if (companyCode.value) {
        formData.append('company_code', companyCode.value);
      }

      if (fileList.value && fileList.value.length > 0) {
        fileList.value.forEach((file, index) => {
          formData.append(`attachments[${index}]file`, file); // Adjust field name based on backend expectations
          formData.append(`attachments[${index}]file_name`, file.name);
        });
      }
      
      try {
        // Assuming this.$axios is globally available
        const response = await this.$axios.post('tickets/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        showSnackbar('工单提交成功', 'success');
        router.push(`/tickets/${response.data.id}`);
      } catch (error) {
        console.error('工单提交失败:', error.response?.data || error.message);
        showSnackbar(error.response?.data?.detail || '工单提交失败，请稍后重试', 'error');
      } finally {
        loading.value = false;
      }
    };

    const getCompanyInfo = async () => {
      if (companyCode.value) {
        try {
          // Assuming this.$axios is globally available
          const response = await this.$axios.get(`companies/by-code/${companyCode.value}/`);
          companyName.value = response.data.name;
        } catch (error) {
          console.error('获取公司信息失败:', error);
          showSnackbar('无效的公司代码', 'error');
          router.push('/');
        }
      }
    };

    onMounted(() => {
      companyCode.value = route.params.companyCode;
      if (companyCode.value) {
        getCompanyInfo();
      }

      const userString = localStorage.getItem('user');
      if (userString) {
        try {
          const user = JSON.parse(userString);
          if (user.email && !ticketForm.contact_info) { // Only fill if not already set (e.g. by company specific link)
            ticketForm.contact_method = 'email';
            ticketForm.contact_info = user.email;
          }
          // You could also pre-fill other contact methods if available in user profile
        } catch (e) {
          console.error('Failed to parse user from localStorage for contact info', e);
        }
      }
    });

    return {
      companyName,
      ticketForm,
      rules,
      fileList,
      fileRules,
      loading,
      validForm,
      ticketFormRef,
      contactPlaceholder,
      categoryOptions,
      contactMethodOptions,
      submitForm,
      snackbar,
      showSnackbar
    };
  },
  // Inject axios if not globally available via provide/inject or app.config.globalProperties
  // inject: ['$axios'], 
};
</script>

<style scoped>
.ticket-submit-container {
  padding-top: 20px;
  padding-bottom: 20px;
}
/* Add any additional custom styles if Vuetify defaults aren't enough */
</style>
