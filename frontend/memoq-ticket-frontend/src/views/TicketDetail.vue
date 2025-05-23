<!-- 工单详情页面，集成Timeline组件展示工单处理进度 -->
<template>
  <div>
    <!-- 面包屑导航 -->
    <v-breadcrumbs :items="breadcrumbs" class="pa-0 mb-4">
      <template v-slot:divider>
        <v-icon>mdi-chevron-right</v-icon>
      </template>
    </v-breadcrumbs>

    <v-alert
      v-if="error"
      type="error"
      class="mb-4"
    >
      {{ error }}
    </v-alert>

    <div v-if="loading" class="d-flex justify-center align-center my-8">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <template v-else-if="ticket">
      <v-row>
        <!-- 工单详情 -->
        <v-col cols="12" md="8">
          <v-card class="mb-4">
            <v-card-title class="d-flex align-center">
              <div>
                <div class="text-h5">{{ ticket.title }}</div>
                <div class="text-subtitle-1 text-grey">工单 #{{ ticket.id }}</div>
              </div>
              <v-spacer></v-spacer>
              <v-chip :color="getStatusColor(ticket.status)" class="mr-2">
                {{ ticket.status_display }}
              </v-chip>
              <v-chip :color="getUrgencyColor(ticket.urgency)">
                {{ ticket.urgency_display }}
              </v-chip>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text>
              <div class="mb-4">
                <div class="text-subtitle-2 font-weight-bold mb-1">描述</div>
                <div class="text-body-1">{{ ticket.description }}</div>
              </div>

              <v-row>
                <v-col cols="12" sm="6">
                  <div class="text-subtitle-2 font-weight-bold mb-1">提交人</div>
                  <div class="text-body-2">{{ ticket.submitted_by_details?.username || '未知' }}</div>
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="text-subtitle-2 font-weight-bold mb-1">创建时间</div>
                  <div class="text-body-2">{{ formatDate(ticket.created_at) }}</div>
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="text-subtitle-2 font-weight-bold mb-1">负责人</div>
                  <div class="text-body-2">{{ ticket.assigned_to_details?.username || '未分配' }}</div>
                </v-col>
                <v-col cols="12" sm="6">
                  <div class="text-subtitle-2 font-weight-bold mb-1">最近活动</div>
                  <div class="text-body-2">{{ formatDate(ticket.last_activity_at) }}</div>
                </v-col>
                <v-col cols="12" sm="6" v-if="ticket.ticket_type_details">
                  <div class="text-subtitle-2 font-weight-bold mb-1">工单类型</div>
                  <div class="text-body-2">{{ ticket.ticket_type_details.name }}</div>
                </v-col>
                <v-col cols="12" sm="6" v-if="ticket.labels_data && ticket.labels_data.length > 0">
                  <div class="text-subtitle-2 font-weight-bold mb-1">标签</div>
                  <v-chip-group>
                    <v-chip
                      v-for="label in ticket.labels_data"
                      :key="label.id"
                      :color="label.color"
                      size="small"
                      label
                    >
                      {{ label.name }}
                    </v-chip>
                  </v-chip-group>
                </v-col>
              </v-row>

              <div v-if="ticket.attachments_data && ticket.attachments_data.length > 0" class="mt-4">
                <div class="text-subtitle-2 font-weight-bold mb-1">附件</div>
                <v-list density="compact">
                  <v-list-item
                    v-for="attachment in ticket.attachments_data"
                    :key="attachment.id"
                    :href="attachment.file_url"
                    target="_blank"
                    :prepend-icon="getFileIcon(attachment.file_type)"
                  >
                    <v-list-item-title>{{ attachment.file_name }}</v-list-item-title>
                    <v-list-item-subtitle>{{ formatFileSize(attachment.file_size) }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>
            </v-card-text>

            <v-divider></v-divider>

            <v-card-actions>
              <v-btn
                v-if="canReplyToTicket"
                color="primary"
                @click="replyDialog = true"
              >
                回复
              </v-btn>
              <v-btn
                v-if="canFollowTicket"
                :color="isFollowing ? 'warning' : 'info'"
                @click="toggleFollowTicket"
              >
                {{ isFollowing ? '取消关注' : '关注工单' }}
              </v-btn>
              <v-btn
                v-if="canPauseTicket"
                :color="ticket.status === 'paused' ? 'success' : 'grey'"
                @click="ticket.status === 'paused' ? resumeTicket() : pauseDialog = true"
              >
                {{ ticket.status === 'paused' ? '恢复工单' : '暂停工单' }}
              </v-btn>
              <v-btn
                v-if="canTransferTicket"
                color="blue-grey"
                @click="transferDialog = true"
              >
                转移工单
              </v-btn>
            </v-card-actions>
          </v-card>

          <!-- 工单回复列表 -->
          <v-card>
            <v-card-title>工单回复</v-card-title>
            <v-card-text v-if="ticket.replies_data.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey-lighten-1">mdi-forum-outline</v-icon>
              <div class="text-h6 text-grey mt-2">暂无回复</div>
            </v-card-text>
            <template v-else>
              <v-list>
                <v-list-item
                  v-for="reply in ticket.replies_data"
                  :key="reply.id"
                  :class="reply.is_internal ? 'bg-grey-lighten-4' : ''"
                >
                  <template v-slot:prepend>
                    <v-avatar color="primary" class="mr-3">
                      <span class="text-h6 text-white">{{ reply.user_info.username.charAt(0).toUpperCase() }}</span>
                    </v-avatar>
                  </template>

                  <v-list-item-title>
                    {{ reply.user_info.username }}
                    <span class="text-caption text-grey ml-2">{{ formatDate(reply.created_at) }}</span>
                    <v-chip v-if="reply.is_internal" size="x-small" color="grey" class="ml-2">内部备注</v-chip>
                    <v-chip v-if="reply.email_sent" size="x-small" color="blue" class="ml-2">已发送邮件</v-chip>
                  </v-list-item-title>

                  <v-list-item-subtitle class="mt-2 text-body-1 text-black">
                    {{ reply.content }}
                  </v-list-item-subtitle>

                  <div v-if="reply.attachments_data && reply.attachments_data.length > 0" class="mt-2">
                    <v-chip
                      v-for="attachment in reply.attachments_data"
                      :key="attachment.id"
                      :prepend-icon="getFileIcon(attachment.file_type)"
                      class="mr-2 mb-2"
                      size="small"
                      :href="attachment.file_url"
                      target="_blank"
                    >
                      {{ attachment.file_name }}
                    </v-chip>
                  </div>
                </v-list-item>
              </v-list>
            </template>
          </v-card>
        </v-col>

        <!-- 工单时间线和关注人 -->
        <v-col cols="12" md="4">
          <!-- 关注人卡片 -->
          <v-card class="mb-4">
            <v-card-title>关注人</v-card-title>
            <v-card-text v-if="ticket.followers_data.length === 0" class="text-center py-4">
              <v-icon size="40" color="grey-lighten-1">mdi-account-multiple-outline</v-icon>
              <div class="text-body-1 text-grey mt-2">暂无关注人</div>
            </v-card-text>
            <v-list v-else density="compact">
              <v-list-item
                v-for="follower in ticket.followers_data"
                :key="follower.id"
              >
                <template v-slot:prepend>
                  <v-avatar size="32" color="info" class="mr-2">
                    <span class="text-caption text-white">{{ follower.username.charAt(0).toUpperCase() }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title>{{ follower.username }}</v-list-item-title>
                <v-list-item-subtitle>{{ follower.email }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card>

          <!-- 工单时间线 -->
          <v-card>
            <v-card-title>工单处理进度</v-card-title>
            <v-card-text>
              <v-timeline align="start" line-thickness="2">
                <!-- 工单创建 -->
                <v-timeline-item
                  dot-color="primary"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(ticket.created_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">工单创建</div>
                  <div class="text-body-2">
                    由 {{ ticket.created_by_details.username }} 创建
                  </div>
                </v-timeline-item>

                <!-- 状态变更历史 -->
                <v-timeline-item
                  v-for="(history, index) in ticket.status_history_data"
                  :key="index"
                  :dot-color="getStatusColor(history.new_status)"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(history.created_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">状态变更</div>
                  <div class="text-body-2">
                    从 <strong>{{ history.old_status_display }}</strong> 变更为 <strong>{{ history.new_status_display }}</strong>
                  </div>
                  <div class="text-body-2">
                    操作人: {{ history.changed_by_username }}
                  </div>
                  <div v-if="history.reason" class="text-body-2 mt-1">
                    原因: {{ history.reason }}
                  </div>
                </v-timeline-item>

                <!-- 工单转移历史 -->
                <v-timeline-item
                  v-for="(transfer, index) in ticket.transfer_history_data"
                  :key="`transfer-${index}`"
                  dot-color="blue-grey"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(transfer.created_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">工单转移</div>
                  <div class="text-body-2">
                    从 <strong>{{ transfer.transferred_from_username || '未分配' }}</strong> 转移给 <strong>{{ transfer.transferred_to_username }}</strong>
                  </div>
                  <div class="text-body-2">
                    操作人: {{ transfer.transferred_by_username }}
                  </div>
                  <div class="text-body-2 mt-1">
                    原因: {{ transfer.reason }}
                  </div>
                </v-timeline-item>

                <!-- 首次回复 -->
                <v-timeline-item
                  v-if="ticket.first_replied_at"
                  dot-color="green"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(ticket.first_replied_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">首次回复</div>
                  <div class="text-body-2">
                    技术支持首次回复工单
                  </div>
                </v-timeline-item>

                <!-- 工单解决 -->
                <v-timeline-item
                  v-if="ticket.resolved_at"
                  dot-color="teal"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(ticket.resolved_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">工单解决</div>
                  <div class="text-body-2">
                    工单已标记为已解决
                  </div>
                </v-timeline-item>

                <!-- 工单关闭 -->
                <v-timeline-item
                  v-if="ticket.closed_at"
                  dot-color="grey"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(ticket.closed_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">工单关闭</div>
                  <div class="text-body-2">
                    工单已关闭
                    <span v-if="ticket.closing_reason_type_display">
                      ({{ ticket.closing_reason_type_display }})
                    </span>
                  </div>
                  <div v-if="ticket.closing_reason_detail" class="text-body-2 mt-1">
                    原因: {{ ticket.closing_reason_detail }}
                  </div>
                </v-timeline-item>

                <!-- 工单暂停 -->
                <v-timeline-item
                  v-if="ticket.paused_at"
                  dot-color="amber"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption">{{ formatDate(ticket.paused_at) }}</div>
                  </template>
                  <div class="text-subtitle-2">工单暂停</div>
                  <div class="text-body-2">
                    工单已暂停处理
                  </div>
                  <div v-if="ticket.pause_reason" class="text-body-2 mt-1">
                    原因: {{ ticket.pause_reason }}
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- 回复对话框 -->
    <v-dialog v-model="replyDialog" max-width="600px">
      <v-card>
        <v-card-title>回复工单</v-card-title>
        <v-card-text>
          <v-form ref="replyFormRef" v-model="validReplyForm">
            <v-textarea
              v-model="replyForm.content"
              label="回复内容"
              :rules="[v => !!v || '请输入回复内容']"
              rows="5"
              required
            ></v-textarea>
            <v-checkbox
              v-if="isSupport"
              v-model="replyForm.is_internal"
              label="内部备注（客户不可见）"
            ></v-checkbox>
            <v-file-input
              v-model="replyForm.attachments"
              label="附件"
              multiple
              prepend-icon="mdi-paperclip"
              show-size
              truncate-length="15"
            ></v-file-input>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="replyDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            :loading="submitting"
            :disabled="!validReplyForm || submitting"
            @click="submitReply"
          >
            提交回复
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 暂停工单对话框 -->
    <v-dialog v-model="pauseDialog" max-width="500px">
      <v-card>
        <v-card-title>暂停工单</v-card-title>
        <v-card-text>
          <p class="mb-4">暂停工单将取消所有关于idle、SLA等方面的提醒。</p>
          <v-form ref="pauseFormRef" v-model="validPauseForm">
            <v-textarea
              v-model="pauseForm.pause_reason"
              label="暂停原因"
              :rules="[v => !!v || '请输入暂停原因']"
              rows="3"
              required
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="pauseDialog = false">取消</v-btn>
          <v-btn
            color="amber"
            :loading="submitting"
            :disabled="!validPauseForm || submitting"
            @click="pauseTicket"
          >
            确认暂停
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 转移工单对话框 -->
    <v-dialog v-model="transferDialog" max-width="500px">
      <v-card>
        <v-card-title>转移工单</v-card-title>
        <v-card-text>
          <v-form ref="transferFormRef" v-model="validTransferForm">
            <v-select
              v-model="transferForm.transferred_to_id"
              :items="supportUsers"
              item-title="username"
              item-value="id"
              label="转移给"
              :rules="[v => !!v || '请选择转移对象']"
              required
            ></v-select>
            <v-textarea
              v-model="transferForm.reason"
              label="转移原因"
              :rules="[v => !!v || '请输入转移原因']"
              rows="3"
              required
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="transferDialog = false">取消</v-btn>
          <v-btn
            color="blue-grey"
            :loading="submitting"
            :disabled="!validTransferForm || submitting"
            @click="transferTicket"
          >
            确认转移
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import api from '@/api';
import { format } from 'date-fns';

export default {
  name: 'TicketDetail',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const authStore = useAuthStore();
    
    const loading = ref(true);
    const error = ref(null);
    const ticket = ref(null);
    const supportUsers = ref([]);
    
    // 对话框状态
    const replyDialog = ref(false);
    const pauseDialog = ref(false);
    const transferDialog = ref(false);
    const submitting = ref(false);
    
    // 表单引用和验证状态
    const replyFormRef = ref(null);
    const pauseFormRef = ref(null);
    const transferFormRef = ref(null);
    const validReplyForm = ref(false);
    const validPauseForm = ref(false);
    const validTransferForm = ref(false);
    
    // 表单数据
    const replyForm = ref({
      content: '',
      is_internal: false,
      attachments: []
    });
    
    const pauseForm = ref({
      pause_reason: ''
    });
    
    const transferForm = ref({
      transferred_to_id: null,
      reason: ''
    });
    
    // 面包屑导航
    const breadcrumbs = computed(() => [
      {
        title: '首页',
        disabled: false,
        href: '/',
      },
      {
        title: '工单管理',
        disabled: false,
        href: authStore.userRole === 'customer' ? '/company-dashboard' : '/tickets',
      },
      {
        title: `工单 #${route.params.id}`,
        disabled: true,
      },
    ]);
    
    // 计算属性：用户角色和权限
    const isSupport = computed(() => 
      ['support', 'technical_support_admin', 'system_admin'].includes(authStore.userRole)
    );
    
    const isCustomer = computed(() => authStore.userRole === 'customer');
    
    const isTicketCreator = computed(() => 
      ticket.value && ticket.value.created_by === authStore.userId
    );
    
    const isTicketSubmitter = computed(() => 
      ticket.value && ticket.value.submitted_by === authStore.userId
    );
    
    const isFollowing = computed(() => 
      ticket.value && ticket.value.followers_data.some(f => f.id === authStore.userId)
    );
    
    const isAssignedSupport = computed(() => 
      ticket.value && ticket.value.assigned_to === authStore.userId
    );
    
    // 权限控制
    const canReplyToTicket = computed(() => {
      if (isSupport.value) return true;
      if (isCustomer.value) {
        return isTicketCreator.value || isTicketSubmitter.value || isFollowing.value;
      }
      return false;
    });
    
    const canFollowTicket = computed(() => {
      return isCustomer.value && !isTicketCreator.value && !isTicketSubmitter.value && !isFollowing.value;
    });
    
    const canPauseTicket = computed(() => {
      if (ticket.value && ticket.value.status === 'paused') {
        return isSupport.value || isTicketCreator.value || isTicketSubmitter.value;
      }
      return isSupport.value || isTicketCreator.value || isTicketSubmitter.value;
    });
    
    const canTransferTicket = computed(() => {
      return isSupport.value && isAssignedSupport.value;
    });
    
    // 获取工单详情
    const fetchTicket = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await api.get(`/tickets/${route.params.id}/`);
        ticket.value = response.data;
      } catch (err) {
        console.error('获取工单详情失败:', err);
        error.value = '获取工单详情失败，请稍后重试';
      } finally {
        loading.value = false;
      }
    };
    
    // 获取技术支持用户列表（用于工单转移）
    const fetchSupportUsers = async () => {
      try {
        const response = await api.get('/users/', {
          params: {
            role: 'support'
          }
        });
        supportUsers.value = response.data.results || [];
      } catch (err) {
        console.error('获取技术支持用户列表失败:', err);
      }
    };
    
    // 提交工单回复
    const submitReply = async () => {
      if (!validReplyForm.value) return;
      
      submitting.value = true;
      try {
        const formData = new FormData();
        formData.append('ticket', ticket.value.id);
        formData.append('content', replyForm.value.content);
        formData.append('is_internal', replyForm.value.is_internal);
        
        // 添加附件
        if (replyForm.value.attachments && replyForm.value.attachments.length > 0) {
          for (const file of replyForm.value.attachments) {
            formData.append('attachments', file);
          }
        }
        
        await api.post('/ticket-replies/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        // 重新获取工单详情
        await fetchTicket();
        
        // 重置表单
        replyForm.value = {
          content: '',
          is_internal: false,
          attachments: []
        };
        replyDialog.value = false;
      } catch (err) {
        console.error('提交回复失败:', err);
        error.value = '提交回复失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 暂停工单
    const pauseTicket = async () => {
      if (!validPauseForm.value) return;
      
      submitting.value = true;
      try {
        await api.post(`/tickets/${ticket.value.id}/pause/`, pauseForm.value);
        
        // 重新获取工单详情
        await fetchTicket();
        
        // 重置表单
        pauseForm.value = {
          pause_reason: ''
        };
        pauseDialog.value = false;
      } catch (err) {
        console.error('暂停工单失败:', err);
        error.value = '暂停工单失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 恢复工单
    const resumeTicket = async () => {
      submitting.value = true;
      try {
        await api.post(`/tickets/${ticket.value.id}/resume/`);
        
        // 重新获取工单详情
        await fetchTicket();
      } catch (err) {
        console.error('恢复工单失败:', err);
        error.value = '恢复工单失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 转移工单
    const transferTicket = async () => {
      if (!validTransferForm.value) return;
      
      submitting.value = true;
      try {
        await api.post(`/tickets/${ticket.value.id}/transfer/`, transferForm.value);
        
        // 重新获取工单详情
        await fetchTicket();
        
        // 重置表单
        transferForm.value = {
          transferred_to_id: null,
          reason: ''
        };
        transferDialog.value = false;
      } catch (err) {
        console.error('转移工单失败:', err);
        error.value = '转移工单失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 关注/取消关注工单
    const toggleFollowTicket = async () => {
      submitting.value = true;
      try {
        if (isFollowing.value) {
          await api.post(`/tickets/${ticket.value.id}/unfollow/`);
        } else {
          await api.post(`/tickets/${ticket.value.id}/follow/`, {
            user_id: authStore.userId
          });
        }
        
        // 重新获取工单详情
        await fetchTicket();
      } catch (err) {
        console.error('关注/取消关注工单失败:', err);
        error.value = '操作失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '未知';
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    };
    
    // 获取状态颜色
    const getStatusColor = (status) => {
      const statusColors = {
        'new_issue': 'blue',
        'pending_assignment': 'orange',
        'in_progress': 'green',
        'waiting_for_customer': 'purple',
        'customer_follow_up': 'deep-purple',
        'resolved': 'teal',
        'closed': 'grey',
        'paused': 'amber'
      };
      return statusColors[status] || 'grey';
    };
    
    // 获取紧急度颜色
    const getUrgencyColor = (urgency) => {
      const urgencyColors = {
        1: 'red', // 紧急
        2: 'orange', // 高
        3: 'blue', // 中
        4: 'green' // 低
      };
      return urgencyColors[urgency] || 'grey';
    };
    
    // 获取文件图标
    const getFileIcon = (fileType) => {
      if (fileType.includes('image')) return 'mdi-file-image';
      if (fileType.includes('pdf')) return 'mdi-file-pdf';
      if (fileType.includes('word') || fileType.includes('document')) return 'mdi-file-word';
      if (fileType.includes('excel') || fileType.includes('sheet')) return 'mdi-file-excel';
      if (fileType.includes('zip') || fileType.includes('compressed')) return 'mdi-zip-box';
      return 'mdi-file';
    };
    
    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
      return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };
    
    onMounted(() => {
      fetchTicket();
      if (isSupport.value) {
        fetchSupportUsers();
      }
    });
    
    return {
      loading,
      error,
      ticket,
      supportUsers,
      breadcrumbs,
      replyDialog,
      pauseDialog,
      transferDialog,
      submitting,
      replyFormRef,
      pauseFormRef,
      transferFormRef,
      validReplyForm,
      validPauseForm,
      validTransferForm,
      replyForm,
      pauseForm,
      transferForm,
      isSupport,
      isCustomer,
      isTicketCreator,
      isTicketSubmitter,
      isFollowing,
      isAssignedSupport,
      canReplyToTicket,
      canFollowTicket,
      canPauseTicket,
      canTransferTicket,
      submitReply,
      pauseTicket,
      resumeTicket,
      transferTicket,
      toggleFollowTicket,
      formatDate,
      getStatusColor,
      getUrgencyColor,
      getFileIcon,
      formatFileSize
    };
  }
};
</script>

<style scoped>
.v-timeline-item__body {
  padding-bottom: 16px;
}
</style>
