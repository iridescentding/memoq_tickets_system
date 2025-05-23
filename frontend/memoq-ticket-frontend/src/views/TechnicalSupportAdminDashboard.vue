// 实现技术支持Admin管理面板中的待分配工单、Miss IR和Idle工单表格

<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="text-h5">
        技术支持管理面板
      </v-card-title>

      <v-tabs
        v-model="activeTab"
        grow
        color="primary"
      >
        <v-tab value="pending">待分配工单</v-tab>
        <v-tab value="miss_ir">SLA监控</v-tab>
        <v-tab value="idle">闲置监控</v-tab>
        <v-tab value="support_users">技术支持管理</v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
        <!-- 待分配工单 Tab -->
        <v-window-item value="pending">
          <v-card-text>
            <h3 class="text-h6 mb-3">待分配工单</h3>
            <v-text-field
              v-model="search.pending"
              append-inner-icon="mdi-magnify"
              label="搜索待分配工单 (工单号, 标题, 公司)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="pendingTicketHeaders"
              :items="filteredPendingTickets"
              :loading="loading.pending"
              class="elevation-1"
              items-per-page-text="每页条目数"
            >
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.status="{ item }">
                <v-chip
                  :color="getStatusColor(item.raw.status)"
                  small
                >
                  {{ getStatusText(item.raw.status) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.urgency="{ item }">
                <v-chip
                  :color="getUrgencyColor(item.raw.urgency)"
                  small
                >
                  {{ getUrgencyText(item.raw.urgency) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.sla="{ item }">
                {{ getSlaText(item.raw) }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.created_at="{ item }">
                {{ formatDate(item.raw.created_at) }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.actions="{ item }">
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn
                      color="primary"
                      v-bind="props"
                      size="small"
                    >
                      分配
                    </v-btn>
                  </template>
                  <v-list>
                    <v-list-item
                      v-for="support in supportUsers"
                      :key="support.id"
                      @click="assignTicket(item.raw, support)"
                    >
                      <v-list-item-title>{{ support.username }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
                <v-btn
                  icon="mdi-eye"
                  variant="text"
                  color="info"
                  size="small"
                  class="ml-2"
                  @click="viewTicket(item.raw)"
                />
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无待分配工单。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- SLA监控 Tab -->
        <v-window-item value="miss_ir">
          <v-card-text>
            <h3 class="text-h6 mb-3">SLA监控</h3>
            <v-alert
              type="warning"
              prominent
              border="start"
              class="mb-4"
            >
              以下工单接近或已超过初始响应SLA，请优先处理。
            </v-alert>
            <v-text-field
              v-model="search.missIr"
              append-inner-icon="mdi-magnify"
              label="搜索SLA风险工单 (工单号, 标题, 公司)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="missIrTicketHeaders"
              :items="filteredMissIrTickets"
              :loading="loading.missIr"
              class="elevation-1"
              items-per-page-text="每页条目数"
            >
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.company_name="{ item }">
                {{ item.raw.company_name }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.submitted_by_username="{ item }">
                {{ item.raw.submitted_by_username }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.urgency="{ item }">
                <v-chip
                  :color="getUrgencyColor(item.raw.urgency)"
                  small
                >
                  {{ getUrgencyText(item.raw.urgency) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.priority="{ item }">
                <v-chip
                  :color="getPriorityColor(item.raw.priority)"
                  small
                >
                  {{ getPriorityText(item.raw.priority) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.time_to_miss_ir="{ item }">
                <span
                  :class="{ 'text-red': item.raw.is_missed_ir }"
                  :style="{ fontWeight: item.raw.is_missed_ir ? 'bold' : 'normal' }"
                >
                  {{ item.raw.is_missed_ir ? 'Miss IR' : formatTimeRemaining(item.raw.time_to_miss_ir_seconds) }}
                </span>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.actions="{ item }">
                <v-menu v-if="!item.raw.assigned_to">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      color="primary"
                      v-bind="props"
                      size="small"
                    >
                      分配
                    </v-btn>
                  </template>
                  <v-list>
                    <v-list-item
                      v-for="support in supportUsers"
                      :key="support.id"
                      @click="assignTicket(item.raw, support)"
                    >
                      <v-list-item-title>{{ support.username }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
                <v-btn
                  icon="mdi-eye"
                  variant="text"
                  color="info"
                  size="small"
                  class="ml-2"
                  @click="viewTicket(item.raw)"
                />
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无SLA风险工单。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- 闲置监控 Tab -->
        <v-window-item value="idle">
          <v-card-text>
            <h3 class="text-h6 mb-3">闲置工单监控</h3>
            <v-alert
              type="info"
              prominent
              border="start"
              class="mb-4"
            >
              以下工单长时间未活动，请检查状态。
            </v-alert>
            <v-text-field
              v-model="search.idle"
              append-inner-icon="mdi-magnify"
              label="搜索闲置工单 (工单号, 标题, 公司)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="idleTicketHeaders"
              :items="filteredIdleTickets"
              :loading="loading.idle"
              class="elevation-1"
              items-per-page-text="每页条目数"
            >
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.company_name="{ item }">
                {{ item.raw.company_name }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.submitted_by_username="{ item }">
                {{ item.raw.submitted_by_username }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.urgency="{ item }">
                <v-chip
                  :color="getUrgencyColor(item.raw.urgency)"
                  small
                >
                  {{ getUrgencyText(item.raw.urgency) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.priority="{ item }">
                <v-chip
                  :color="getPriorityColor(item.raw.priority)"
                  small
                >
                  {{ getPriorityText(item.raw.priority) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.time_to_idle="{ item }">
                <span
                  :class="{ 'text-red': item.raw.is_idle }"
                  :style="{ fontWeight: item.raw.is_idle ? 'bold' : 'normal' }"
                >
                  {{ item.raw.is_idle ? '已闲置' : formatTimeRemaining(item.raw.time_to_idle_seconds) }}
                </span>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.actions="{ item }">
                <v-btn
                  icon="mdi-eye"
                  variant="text"
                  color="info"
                  size="small"
                  @click="viewTicket(item.raw)"
                />
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无闲置工单。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- 技术支持管理 Tab -->
        <v-window-item value="support_users">
          <v-card-text>
            <div class="d-flex justify-space-between align-center mb-4">
              <h3 class="text-h6">技术支持人员管理</h3>
              <v-btn
                color="primary"
                @click="showAddSupportDialog"
              >
                添加技术支持
              </v-btn>
            </div>
            <v-text-field
              v-model="search.supportUsers"
              append-inner-icon="mdi-magnify"
              label="搜索技术支持 (用户名, 邮箱)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="supportUserHeaders"
              :items="filteredSupportUsers"
              :loading="loading.supportUsers"
              class="elevation-1"
              items-per-page-text="每页条目数"
            >
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.role="{ item }">
                <v-chip
                  :color="getRoleColor(item.raw.role)"
                  small
                >
                  {{ getRoleText(item.raw.role) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.is_active="{ item }">
                <v-chip
                  :color="item.raw.is_active ? 'success' : 'error'"
                  small
                >
                  {{ item.raw.is_active ? '激活' : '禁用' }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.actions="{ item }">
                <v-btn
                  icon="mdi-pencil"
                  variant="text"
                  color="info"
                  size="small"
                  @click="editSupportUser(item.raw)"
                />
                <v-btn
                  icon="mdi-key"
                  variant="text"
                  color="warning"
                  size="small"
                  class="ml-2"
                  @click="resetPassword(item.raw)"
                />
                <v-btn
                  :icon="item.raw.is_active ? 'mdi-account-off' : 'mdi-account-check'"
                  variant="text"
                  :color="item.raw.is_active ? 'error' : 'success'"
                  size="small"
                  class="ml-2"
                  @click="toggleUserStatus(item.raw)"
                />
                <v-btn
                  icon="mdi-delete"
                  variant="text"
                  color="error"
                  size="small"
                  class="ml-2"
                  @click="deleteSupportUser(item.raw)"
                />
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无技术支持人员数据。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- 添加技术支持对话框 -->
    <v-dialog v-model="dialogs.addSupport" max-width="600px">
      <v-card>
        <v-card-title>添加技术支持人员</v-card-title>
        <v-card-text>
          <v-form ref="supportFormRef" v-model="validSupportForm">
            <v-text-field
              v-model="supportForm.username"
              label="用户名"
              required
              :rules="[v => !!v || '请输入用户名']"
            />
            <v-text-field
              v-model="supportForm.email"
              label="邮箱"
              type="email"
              required
              :rules="[
                v => !!v || '请输入邮箱',
                v => /.+@.+\..+/.test(v) || '请输入有效的邮箱地址'
              ]"
            />
            <v-text-field
              v-model="supportForm.password"
              label="密码"
              type="password"
              required
              :rules="[v => !!v || '请输入密码', v => v.length >= 8 || '密码长度至少为8位']"
            />
            <v-text-field
              v-model="supportForm.first_name"
              label="名"
            />
            <v-text-field
              v-model="supportForm.last_name"
              label="姓"
            />
            <v-select
              v-model="supportForm.role"
              :items="[
                { text: '技术支持', value: 'support' },
                { text: '技术支持管理员', value: 'technical_support_admin' }
              ]"
              label="角色"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" text @click="dialogs.addSupport = false">取消</v-btn>
          <v-btn
            color="primary"
            @click="createSupportUser"
            :loading="loading.createSupport"
            :disabled="!validSupportForm"
          >
            创建
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑技术支持对话框 -->
    <v-dialog v-model="dialogs.editSupport" max-width="600px">
      <v-card>
        <v-card-title>编辑技术支持人员</v-card-title>
        <v-card-text>
          <v-form ref="editSupportFormRef" v-model="validEditSupportForm">
            <v-text-field
              v-model="editSupportForm.username"
              label="用户名"
              required
              :rules="[v => !!v || '请输入用户名']"
              disabled
            />
            <v-text-field
              v-model="editSupportForm.email"
              label="邮箱"
              type="email"
              required
              :rules="[
                v => !!v || '请输入邮箱',
                v => /.+@.+\..+/.test(v) || '请输入有效的邮箱地址'
              ]"
            />
            <v-text-field
              v-model="editSupportForm.first_name"
              label="名"
            />
            <v-text-field
              v-model="editSupportForm.last_name"
              label="姓"
            />
            <v-select
              v-model="editSupportForm.role"
              :items="[
                { text: '技术支持', value: 'support' },
                { text: '技术支持管理员', value: 'technical_support_admin' }
              ]"
              label="角色"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" text @click="dialogs.editSupport = false">取消</v-btn>
          <v-btn
            color="primary"
            @click="updateSupportUser"
            :loading="loading.updateSupport"
            :disabled="!validEditSupportForm"
          >
            更新
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 重置密码对话框 -->
    <v-dialog v-model="dialogs.resetPassword" max-width="500px">
      <v-card>
        <v-card-title>重置密码</v-card-title>
        <v-card-text>
          <p>您正在为用户 <strong>{{ resetPasswordUser?.username }}</strong> 重置密码。</p>
          <v-form ref="resetPasswordFormRef" v-model="validResetPasswordForm">
            <v-text-field
              v-model="resetPasswordForm.new_password"
              label="新密码"
              type="password"
              required
              :rules="[v => !!v || '请输入新密码', v => v.length >= 8 || '密码长度至少为8位']"
            />
            <v-text-field
              v-model="resetPasswordForm.confirm_password"
              label="确认密码"
              type="password"
              required
              :rules="[
                v => !!v || '请确认密码',
                v => v === resetPasswordForm.new_password || '两次输入的密码不一致'
              ]"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" text @click="dialogs.resetPassword = false">取消</v-btn>
          <v-btn
            color="warning"
            @click="confirmResetPassword"
            :loading="loading.resetPassword"
            :disabled="!validResetPasswordForm"
          >
            重置密码
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
  </v-container>
</template>

<script>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { format, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import api from '@/api';

export default {
  name: 'TechnicalSupportAdminDashboard',
  setup() {
    const router = useRouter();
    const activeTab = ref('pending');
    
    // 数据
    const pendingTickets = ref([]);
    const missIrTickets = ref([]);
    const idleTickets = ref([]);
    const supportUsers = ref([]);
    
    // 搜索
    const search = reactive({
      pending: '',
      missIr: '',
      idle: '',
      supportUsers: ''
    });
    
    // 加载状态
    const loading = reactive({
      pending: false,
      missIr: false,
      idle: false,
      supportUsers: false,
      createSupport: false,
      updateSupport: false,
      resetPassword: false
    });
    
    // 对话框状态
    const dialogs = reactive({
      addSupport: false,
      editSupport: false,
      resetPassword: false
    });
    
    // 表单
    const supportFormRef = ref(null);
    const editSupportFormRef = ref(null);
    const resetPasswordFormRef = ref(null);
    const validSupportForm = ref(false);
    const validEditSupportForm = ref(false);
    const validResetPasswordForm = ref(false);
    
    const supportForm = reactive({
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      role: 'support'
    });
    
    const editSupportForm = reactive({
      id: null,
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      role: ''
    });
    
    const resetPasswordForm = reactive({
      new_password: '',
      confirm_password: ''
    });
    
    const resetPasswordUser = ref(null);
    
    // 提示信息
    const snackbar = reactive({
      show: false,
      text: '',
      color: 'success',
      timeout: 3000
    });
    
    // 表头
    const pendingTicketHeaders = [
      { title: '工单号', key: 'id', width: '90px' },
      { title: '标题', key: 'title', minWidth: '200px' },
      { title: '公司', key: 'company.name', width: '150px' },
      { title: '提交人', key: 'submitted_by.username', width: '120px' },
      { title: '状态', key: 'status', width: '120px' },
      { title: '紧急度', key: 'urgency', width: '100px' },
      { title: 'SLA', key: 'sla', width: '120px' },
      { title: '创建时间', key: 'created_at', width: '150px' },
      { title: '操作', key: 'actions', width: '120px', sortable: false }
    ];
    
    const missIrTicketHeaders = [
      { title: '工单号', key: 'id', width: '90px' },
      { title: '标题', key: 'title', minWidth: '200px' },
      { title: '公司', key: 'company_name', width: '150px' },
      { title: '提交人', key: 'submitted_by_username', width: '120px' },
      { title: '紧急度', key: 'urgency', width: '100px' },
      { title: '优先级', key: 'priority', width: '100px' },
      { title: '距离Miss IR', key: 'time_to_miss_ir', width: '120px' },
      { title: '操作', key: 'actions', width: '120px', sortable: false }
    ];
    
    const idleTicketHeaders = [
      { title: '工单号', key: 'id', width: '90px' },
      { title: '标题', key: 'title', minWidth: '200px' },
      { title: '公司', key: 'company_name', width: '150px' },
      { title: '提交人', key: 'submitted_by_username', width: '120px' },
      { title: '紧急度', key: 'urgency', width: '100px' },
      { title: '优先级', key: 'priority', width: '100px' },
      { title: '距离Idle', key: 'time_to_idle', width: '120px' },
      { title: '操作', key: 'actions', width: '120px', sortable: false }
    ];
    
    const supportUserHeaders = [
      { title: '用户名', key: 'username', width: '150px' },
      { title: '邮箱', key: 'email', minWidth: '200px' },
      { title: '姓名', key: 'full_name', width: '150px' },
      { title: '角色', key: 'role', width: '150px' },
      { title: '状态', key: 'is_active', width: '100px' },
      { title: '创建时间', key: 'date_joined', width: '150px' },
      { title: '操作', key: 'actions', width: '180px', sortable: false }
    ];
    
    // 过滤后的数据
    const filteredPendingTickets = computed(() => {
      if (!search.pending) return pendingTickets.value;
      const searchTerm = search.pending.toLowerCase();
      return pendingTickets.value.filter(ticket => 
        ticket.id.toString().includes(searchTerm) ||
        ticket.title.toLowerCase().includes(searchTerm) ||
        (ticket.company?.name && ticket.company.name.toLowerCase().includes(searchTerm))
      );
    });
    
    const filteredMissIrTickets = computed(() => {
      if (!search.missIr) return missIrTickets.value;
      const searchTerm = search.missIr.toLowerCase();
      return missIrTickets.value.filter(ticket => 
        ticket.id.toString().includes(searchTerm) ||
        ticket.title.toLowerCase().includes(searchTerm) ||
        (ticket.company_name && ticket.company_name.toLowerCase().includes(searchTerm))
      );
    });
    
    const filteredIdleTickets = computed(() => {
      if (!search.idle) return idleTickets.value;
      const searchTerm = search.idle.toLowerCase();
      return idleTickets.value.filter(ticket => 
        ticket.id.toString().includes(searchTerm) ||
        ticket.title.toLowerCase().includes(searchTerm) ||
        (ticket.company_name && ticket.company_name.toLowerCase().includes(searchTerm))
      );
    });
    
    const filteredSupportUsers = computed(() => {
      if (!search.supportUsers) return supportUsers.value;
      const searchTerm = search.supportUsers.toLowerCase();
      return supportUsers.value.filter(user => 
        user.username.toLowerCase().includes(searchTerm) ||
        user.email.toLowerCase().includes(searchTerm) ||
        (user.full_name && user.full_name.toLowerCase().includes(searchTerm))
      );
    });
    
    // 显示提示信息
    const showMessage = (text, color = 'success') => {
      snackbar.text = text;
      snackbar.color = color;
      snackbar.show = true;
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '';
      return format(parseISO(dateString), 'yyyy-MM-dd HH:mm', { locale: zhCN });
    };
    
    // 格式化剩余时间
    const formatTimeRemaining = (seconds) => {
      if (seconds === undefined || seconds === null) return '';
      
      const absSeconds = Math.abs(seconds);
      const hours = Math.floor(absSeconds / 3600);
      const minutes = Math.floor((absSeconds % 3600) / 60);
      
      if (seconds < 0) {
        return `超时 ${hours}小时${minutes}分钟`;
      } else {
        return `剩余 ${hours}小时${minutes}分钟`;
      }
    };
    
    // 获取状态颜色
    const getStatusColor = (status) => {
      const statusColors = {
        new_issue: 'blue',
        pending_assignment: 'amber',
        in_progress: 'green',
        waiting_for_customer: 'purple',
        customer_follow_up: 'deep-purple',
        resolved: 'teal',
        closed: 'grey'
      };
      return statusColors[status] || 'grey';
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusTexts = {
        new_issue: '新工单',
        pending_assignment: '待分配',
        in_progress: '处理中',
        waiting_for_customer: '等待客户',
        customer_follow_up: '客户跟进',
        resolved: '已解决',
        closed: '已关闭'
      };
      return statusTexts[status] || status;
    };
    
    // 获取紧急度颜色
    const getUrgencyColor = (urgency) => {
      const urgencyColors = {
        low: 'green',
        medium: 'blue',
        high: 'orange',
        urgent: 'red'
      };
      return urgencyColors[urgency] || 'grey';
    };
    
    // 获取紧急度文本
    const getUrgencyText = (urgency) => {
      const urgencyTexts = {
        low: '低',
        medium: '中',
        high: '高',
        urgent: '紧急'
      };
      return urgencyTexts[urgency] || urgency;
    };
    
    // 获取优先级颜色
    const getPriorityColor = (priority) => {
      const priorityColors = {
        1: 'red',
        2: 'orange',
        3: 'blue',
        4: 'green'
      };
      return priorityColors[priority] || 'grey';
    };
    
    // 获取优先级文本
    const getPriorityText = (priority) => {
      const priorityTexts = {
        1: 'P1',
        2: 'P2',
        3: 'P3',
        4: 'P4'
      };
      return priorityTexts[priority] || priority;
    };
    
    // 获取角色颜色
    const getRoleColor = (role) => {
      const roleColors = {
        system_admin: 'red',
        technical_support_admin: 'purple',
        support: 'blue',
        customer: 'green'
      };
      return roleColors[role] || 'grey';
    };
    
    // 获取角色文本
    const getRoleText = (role) => {
      const roleTexts = {
        system_admin: '系统管理员',
        technical_support_admin: '技术支持管理员',
        support: '技术支持',
        customer: '客户'
      };
      return roleTexts[role] || role;
    };
    
    // 获取SLA文本
    const getSlaText = (ticket) => {
      if (!ticket.company?.config?.sla_response_minutes) return '未设置';
      
      const slaMinutes = ticket.company.config.sla_response_minutes;
      const slaHours = Math.floor(slaMinutes / 60);
      const slaRemainingMinutes = slaMinutes % 60;
      
      return `${slaHours}小时${slaRemainingMinutes > 0 ? slaRemainingMinutes + '分钟' : ''}`;
    };
    
    // 获取待分配工单
    const fetchPendingTickets = async () => {
      loading.pending = true;
      try {
        const response = await api.get('/tickets/admin-dashboard-tables/');
        pendingTickets.value = response.data.pending_assignment_tickets || [];
      } catch (error) {
        console.error('获取待分配工单失败:', error);
        showMessage('获取待分配工单失败', 'error');
      } finally {
        loading.pending = false;
      }
    };
    
    // 获取SLA监控工单
    const fetchMissIrTickets = async () => {
      loading.missIr = true;
      try {
        const response = await api.get('/tickets/admin-dashboard-tables/');
        missIrTickets.value = response.data.miss_ir_tickets || [];
        
        // 按照是否已Miss IR和剩余时间排序
        missIrTickets.value.sort((a, b) => {
          if (a.is_missed_ir && !b.is_missed_ir) return -1;
          if (!a.is_missed_ir && b.is_missed_ir) return 1;
          return a.time_to_miss_ir_seconds - b.time_to_miss_ir_seconds;
        });
      } catch (error) {
        console.error('获取SLA监控工单失败:', error);
        showMessage('获取SLA监控工单失败', 'error');
      } finally {
        loading.missIr = false;
      }
    };
    
    // 获取闲置工单
    const fetchIdleTickets = async () => {
      loading.idle = true;
      try {
        const response = await api.get('/tickets/admin-dashboard-tables/');
        idleTickets.value = response.data.idle_tickets || [];
        
        // 按照是否已闲置和剩余时间排序
        idleTickets.value.sort((a, b) => {
          if (a.is_idle && !b.is_idle) return -1;
          if (!a.is_idle && b.is_idle) return 1;
          return a.time_to_idle_seconds - b.time_to_idle_seconds;
        });
      } catch (error) {
        console.error('获取闲置工单失败:', error);
        showMessage('获取闲置工单失败', 'error');
      } finally {
        loading.idle = false;
      }
    };
    
    // 获取技术支持人员
    const fetchSupportUsers = async () => {
      loading.supportUsers = true;
      try {
        const response = await api.get('/users/support-users/');
        supportUsers.value = response.data.map(user => ({
          ...user,
          full_name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || '-'
        }));
      } catch (error) {
        console.error('获取技术支持人员失败:', error);
        showMessage('获取技术支持人员失败', 'error');
      } finally {
        loading.supportUsers = false;
      }
    };
    
    // 分配工单
    const assignTicket = async (ticket, support) => {
      try {
        await api.post(`/tickets/${ticket.id}/assign/`, {
          assigned_to_id: support.id
        });
        
        showMessage(`工单已分配给 ${support.username}`);
        
        // 刷新数据
        fetchPendingTickets();
        fetchMissIrTickets();
        fetchIdleTickets();
      } catch (error) {
        console.error('分配工单失败:', error);
        showMessage('分配工单失败', 'error');
      }
    };
    
    // 查看工单
    const viewTicket = (ticket) => {
      router.push(`/tickets/${ticket.id}`);
    };
    
    // 显示添加技术支持对话框
    const showAddSupportDialog = () => {
      // 重置表单
      supportForm.username = '';
      supportForm.email = '';
      supportForm.password = '';
      supportForm.first_name = '';
      supportForm.last_name = '';
      supportForm.role = 'support';
      
      dialogs.addSupport = true;
    };
    
    // 创建技术支持用户
    const createSupportUser = async () => {
      if (!supportFormRef.value.validate()) return;
      
      loading.createSupport = true;
      try {
        const response = await api.post('/users/support-users/', supportForm);
        
        // 添加到列表
        supportUsers.value.push({
          ...response.data,
          full_name: `${response.data.first_name || ''} ${response.data.last_name || ''}`.trim() || '-'
        });
        
        dialogs.addSupport = false;
        showMessage('技术支持人员创建成功');
      } catch (error) {
        console.error('创建技术支持人员失败:', error);
        showMessage('创建技术支持人员失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        loading.createSupport = false;
      }
    };
    
    // 编辑技术支持用户
    const editSupportUser = (user) => {
      editSupportForm.id = user.id;
      editSupportForm.username = user.username;
      editSupportForm.email = user.email;
      editSupportForm.first_name = user.first_name || '';
      editSupportForm.last_name = user.last_name || '';
      editSupportForm.role = user.role;
      
      dialogs.editSupport = true;
    };
    
    // 更新技术支持用户
    const updateSupportUser = async () => {
      if (!editSupportFormRef.value.validate()) return;
      
      loading.updateSupport = true;
      try {
        const response = await api.put(`/users/support-users/${editSupportForm.id}/`, {
          email: editSupportForm.email,
          first_name: editSupportForm.first_name,
          last_name: editSupportForm.last_name,
          role: editSupportForm.role
        });
        
        // 更新列表
        const index = supportUsers.value.findIndex(user => user.id === editSupportForm.id);
        if (index !== -1) {
          supportUsers.value[index] = {
            ...response.data,
            full_name: `${response.data.first_name || ''} ${response.data.last_name || ''}`.trim() || '-'
          };
        }
        
        dialogs.editSupport = false;
        showMessage('技术支持人员更新成功');
      } catch (error) {
        console.error('更新技术支持人员失败:', error);
        showMessage('更新技术支持人员失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        loading.updateSupport = false;
      }
    };
    
    // 重置密码
    const resetPassword = (user) => {
      resetPasswordUser.value = user;
      resetPasswordForm.new_password = '';
      resetPasswordForm.confirm_password = '';
      
      dialogs.resetPassword = true;
    };
    
    // 确认重置密码
    const confirmResetPassword = async () => {
      if (!resetPasswordFormRef.value.validate()) return;
      
      loading.resetPassword = true;
      try {
        await api.post(`/users/support-users/${resetPasswordUser.value.id}/reset-password/`, {
          new_password: resetPasswordForm.new_password
        });
        
        dialogs.resetPassword = false;
        showMessage('密码重置成功');
      } catch (error) {
        console.error('重置密码失败:', error);
        showMessage('重置密码失败: ' + (error.response?.data?.detail || error.message), 'error');
      } finally {
        loading.resetPassword = false;
      }
    };
    
    // 切换用户状态
    const toggleUserStatus = async (user) => {
      const newStatus = !user.is_active;
      const confirmMessage = newStatus
        ? `确定要激活用户 ${user.username} 吗？`
        : `确定要禁用用户 ${user.username} 吗？`;
      
      if (!confirm(confirmMessage)) return;
      
      try {
        const response = await api.patch(`/users/support-users/${user.id}/`, {
          is_active: newStatus
        });
        
        // 更新列表
        const index = supportUsers.value.findIndex(u => u.id === user.id);
        if (index !== -1) {
          supportUsers.value[index] = {
            ...response.data,
            full_name: `${response.data.first_name || ''} ${response.data.last_name || ''}`.trim() || '-'
          };
        }
        
        showMessage(`用户${newStatus ? '激活' : '禁用'}成功`);
      } catch (error) {
        console.error(`${newStatus ? '激活' : '禁用'}用户失败:`, error);
        showMessage(`${newStatus ? '激活' : '禁用'}用户失败`, 'error');
      }
    };
    
    // 删除技术支持用户
    const deleteSupportUser = async (user) => {
      if (!confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复。`)) return;
      
      try {
        await api.delete(`/users/support-users/${user.id}/`);
        
        // 从列表中移除
        supportUsers.value = supportUsers.value.filter(u => u.id !== user.id);
        
        showMessage('用户删除成功');
      } catch (error) {
        console.error('删除用户失败:', error);
        showMessage('删除用户失败: ' + (error.response?.data?.detail || error.message), 'error');
      }
    };
    
    // 监听标签页变化，加载对应数据
    watch(activeTab, (newTab) => {
      if (newTab === 'pending' && !pendingTickets.value.length) {
        fetchPendingTickets();
      } else if (newTab === 'miss_ir' && !missIrTickets.value.length) {
        fetchMissIrTickets();
      } else if (newTab === 'idle' && !idleTickets.value.length) {
        fetchIdleTickets();
      } else if (newTab === 'support_users' && !supportUsers.value.length) {
        fetchSupportUsers();
      }
    });
    
    // 定时刷新数据
    const setupRefreshInterval = () => {
      const refreshInterval = setInterval(() => {
        if (activeTab.value === 'pending') {
          fetchPendingTickets();
        } else if (activeTab.value === 'miss_ir') {
          fetchMissIrTickets();
        } else if (activeTab.value === 'idle') {
          fetchIdleTickets();
        }
      }, 60000); // 每分钟刷新一次
      
      return refreshInterval;
    };
    
    onMounted(() => {
      // 初始加载数据
      fetchPendingTickets();
      fetchSupportUsers();
      
      // 设置定时刷新
      const refreshInterval = setupRefreshInterval();
      
      // 组件卸载时清除定时器
      return () => {
        clearInterval(refreshInterval);
      };
    });
    
    return {
      activeTab,
      pendingTickets,
      missIrTickets,
      idleTickets,
      supportUsers,
      search,
      loading,
      dialogs,
      supportFormRef,
      editSupportFormRef,
      resetPasswordFormRef,
      validSupportForm,
      validEditSupportForm,
      validResetPasswordForm,
      supportForm,
      editSupportForm,
      resetPasswordForm,
      resetPasswordUser,
      snackbar,
      pendingTicketHeaders,
      missIrTicketHeaders,
      idleTicketHeaders,
      supportUserHeaders,
      filteredPendingTickets,
      filteredMissIrTickets,
      filteredIdleTickets,
      filteredSupportUsers,
      formatDate,
      formatTimeRemaining,
      getStatusColor,
      getStatusText,
      getUrgencyColor,
      getUrgencyText,
      getPriorityColor,
      getPriorityText,
      getRoleColor,
      getRoleText,
      getSlaText,
      assignTicket,
      viewTicket,
      showAddSupportDialog,
      createSupportUser,
      editSupportUser,
      updateSupportUser,
      resetPassword,
      confirmResetPassword,
      toggleUserStatus,
      deleteSupportUser
    };
  }
};
</script>

<style scoped>
.text-red {
  color: #f44336 !important;
}
</style>
