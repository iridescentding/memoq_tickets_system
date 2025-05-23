<template>
  <v-container
    fluid
    class="support-dashboard-container"
  >
    <v-card class="support-dashboard-card">
      <v-card-title class="text-h5">
        技术支持管理面板
      </v-card-title>

      <v-tabs
        v-model="activeTab"
        grow
        color="primary"
      >
        <v-tab value="active">
          活跃工单
        </v-tab>
        <v-tab value="sla">
          SLA监控
        </v-tab>
        <v-tab value="idle">
          闲置监控
        </v-tab>
        <v-tab value="my">
          我的工单
        </v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
        <!-- Active Tickets Tab -->
        <v-window-item value="active">
          <v-card-text>
            <h3 class="text-h6 mb-3">
              活跃工单
            </h3>
            <v-text-field
              v-model="search.active"
              append-inner-icon="mdi-magnify"
              label="搜索活跃工单 (工单号, 标题, 公司)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="activeTicketHeaders"
              :items="filteredActiveTickets"
              :loading="loading.active"
              class="elevation-1"
              items-per-page-text="每页条目数"
              hover
              @click:row="handleRowClick"
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
              <template #item.priority="{ item }">
                <v-chip
                  :color="getPriorityColor(item.raw.priority)"
                  small
                >
                  {{ getPriorityText(item.raw.priority) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.company_importance="{ item }">
                <v-chip
                  v-if="item.raw.company?.importance"
                  :color="getImportanceColor(item.raw.company?.importance)"
                  small
                >
                  {{ getImportanceText(item.raw.company.importance) }}
                </v-chip>
                <span v-else>-</span>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.created_at="{ item }">
                {{ formatDate(item.raw.created_at) }}
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无活跃工单数据。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- SLA Monitor Tab -->
        <v-window-item value="sla">
          <v-card-text>
            <h3 class="text-h6 mb-3">
              SLA风险工单
            </h3>
            <v-alert
              type="warning"
              prominent
              border="start"
              class="mb-4"
            >
              以下工单接近SLA超时，请优先处理。
            </v-alert>
            <v-text-field
              v-model="search.sla"
              append-inner-icon="mdi-magnify"
              label="搜索SLA风险工单 (工单号, 标题, 公司)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="slaTicketHeaders"
              :items="filteredSlaTickets"
              :loading="loading.sla"
              class="elevation-1"
              items-per-page-text="每页条目数"
              hover
              @click:row="handleRowClick"
            >
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.sla_type="{ item }">
                <v-chip
                  :color="item.raw.sla_type === 'response' ? 'deep-orange' : 'red-darken-2'"
                  small
                >
                  {{ item.raw.sla_type === 'response' ? '响应SLA' : '解决SLA' }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.sla_progress_display="{ item }">
                <v-progress-linear
                  :model-value="item.raw.sla_percentage"
                  :color="getSlaProgressColor(item.raw.sla_percentage)"
                  height="20"
                  rounded
                  striped
                >
                  <strong class="text-white">{{ item.raw.sla_percentage }}%</strong>
                </v-progress-linear>
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
              <template #item.company_importance="{ item }">
                <v-chip
                  v-if="item.raw.company?.importance"
                  :color="getImportanceColor(item.raw.company?.importance)"
                  small
                >
                  {{ getImportanceText(item.raw.company.importance) }}
                </v-chip>
                <span v-else>-</span>
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无SLA风险工单数据。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- Idle Monitor Tab -->
        <v-window-item value="idle">
          <v-card-text>
            <h3 class="text-h6 mb-3">
              闲置工单
            </h3>
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
              hover
              @click:row="handleRowClick"
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
              <template #item.idle_progress_display="{ item }">
                <v-progress-linear
                  :model-value="item.raw.idle_percentage"
                  :color="getIdleProgressColor(item.raw.idle_percentage)"
                  height="20"
                  rounded
                  striped
                >
                  <strong class="text-white">{{ item.raw.idle_percentage }}%</strong>
                </v-progress-linear>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.company_importance="{ item }">
                <v-chip
                  v-if="item.raw.company?.importance"
                  :color="getImportanceColor(item.raw.company?.importance)"
                  small
                >
                  {{ getImportanceText(item.raw.company.importance) }}
                </v-chip>
                <span v-else>-</span>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.last_activity_at="{ item }">
                {{ formatDate(item.raw.last_activity_at) }}
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无闲置工单数据。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- My Tickets Tab -->
        <v-window-item value="my">
          <v-card-text>
            <h3 class="text-h6 mb-3">
              分配给我的工单
            </h3>
            <v-text-field
              v-model="search.my"
              append-inner-icon="mdi-magnify"
              label="搜索我的工单 (工单号, 标题, 公司)"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-data-table
              :headers="myTicketHeaders"
              :items="filteredMyTickets"
              :loading="loading.my"
              class="elevation-1"
              items-per-page-text="每页条目数"
              hover
              @click:row="handleRowClick"
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
              <template #item.priority="{ item }">
                <v-chip
                  :color="getPriorityColor(item.raw.priority)"
                  small
                >
                  {{ getPriorityText(item.raw.priority) }}
                </v-chip>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.company_importance="{ item }">
                <v-chip
                  v-if="item.raw.company?.importance"
                  :color="getImportanceColor(item.raw.company?.importance)"
                  small
                >
                  {{ getImportanceText(item.raw.company.importance) }}
                </v-chip>
                <span v-else>-</span>
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.created_at="{ item }">
                {{ formatDate(item.raw.created_at) }}
              </template>
              <!-- eslint-disable-next-line vue/valid-v-slot -->
              <template #item.last_activity_at="{ item }">
                {{ formatDate(item.raw.last_activity_at) }}
              </template>
              <template #loading>
                <v-skeleton-loader type="table-row@5" />
              </template>
              <template #no-data>
                <v-alert
                  type="info"
                  class="ma-4"
                >
                  暂无分配给您的工单数据。
                </v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="top right"
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

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/api';

const router = useRouter();
const activeTab = ref('active');
const activeTickets = ref([]);
const slaTickets = ref([]);
const idleTickets = ref([]);
const myTickets = ref([]);

const search = reactive({
    active: '',
    sla: '',
    idle: '',
    my: ''
});

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

const loading = reactive({
  active: false,
  sla: false,
  idle: false,
  my: false
});

const companyImportanceHeader = { title: '客户重要性', key: 'company_importance', width: '120px' };

const commonTicketHeaders = [
  { title: '工单号', key: 'id', width: '90px' },
  { title: '标题', key: 'title', minWidth: '200px' },
  { title: '公司', key: 'company.name', width: '150px' },
  companyImportanceHeader,
  { title: '状态', key: 'status', width: '140px' },
  { title: '优先级', key: 'priority', width: '110px' },
];

const activeTicketHeaders = [
  ...commonTicketHeaders,
  { title: '创建时间', key: 'created_at', width: '180px' },
  { title: '负责人', key: 'assigned_to_username', width: '120px' }
];

const slaTicketHeaders = [
  { title: '工单号', key: 'id', width: '90px' },
  { title: '标题', key: 'title', minWidth: '200px' },
  { title: '公司', key: 'company.name', width: '150px' },
  companyImportanceHeader,
  { title: 'SLA类型', key: 'sla_type', width: '120px' },
  { title: 'SLA进度', key: 'sla_progress_display', width: '200px', sortable: false },
  { title: '优先级', key: 'priority', width: '110px' },
  { title: '负责人', key: 'assigned_to_username', width: '120px' }
];

const idleTicketHeaders = [
  { title: '工单号', key: 'id', width: '90px' },
  { title: '标题', key: 'title', minWidth: '200px' },
  { title: '公司', key: 'company.name', width: '150px' },
  companyImportanceHeader,
  { title: '状态', key: 'status', width: '140px' },
  { title: '闲置进度', key: 'idle_progress_display', width: '200px', sortable: false },
  { title: '最后活动', key: 'last_activity_at', width: '180px' },
  { title: '负责人', key: 'assigned_to_username', width: '120px' }
];

const myTicketHeaders = [
  ...commonTicketHeaders,
  { title: '创建时间', key: 'created_at', width: '180px' },
  { title: '最后活动', key: 'last_activity_at', width: '180px' }
];

const fetchData = async (endpoint, dataRef, loadingKey) => {
  loading[loadingKey] = true;
  try {
    const response = await api.getTickets({ params: { view: endpoint } });
    dataRef.value = response.data.results || response.data;
  } catch (error) {
    console.error(`获取${loadingKey}数据失败:`, error.response?.data || error.message);
    showSnackbar(`获取${loadingKey}数据失败，请稍后重试`, 'error');
  } finally {
    loading[loadingKey] = false;
  }
};

const loadActiveTickets = () => fetchData('active_tickets', activeTickets, 'active');
const loadSlaTickets = () => fetchData('sla_monitor', slaTickets, 'sla');
const loadIdleTickets = () => fetchData('idle_monitor', idleTickets, 'idle');
const loadMyTickets = () => fetchData('assigned_to_me', myTickets, 'my');

const filterTickets = (tickets, searchTerm) => {
    if (!searchTerm) return tickets;
    const lowerSearchTerm = searchTerm.toLowerCase();
    return tickets.filter(ticket =>
        ticket.id.toString().includes(lowerSearchTerm) ||
        ticket.title.toLowerCase().includes(lowerSearchTerm) ||
        (ticket.company && ticket.company.name.toLowerCase().includes(lowerSearchTerm))
    );
};

const filteredActiveTickets = computed(() => filterTickets(activeTickets.value, search.active));
const filteredSlaTickets = computed(() => filterTickets(slaTickets.value, search.sla));
const filteredIdleTickets = computed(() => filterTickets(idleTickets.value, search.idle));
const filteredMyTickets = computed(() => filterTickets(myTickets.value, search.my));

const handleRowClick = (event, { item }) => {
  router.push(`/tickets/${item.raw.id}`);
};

const statusColors = {
    new_issue: 'blue-grey',
    in_progress: 'amber-darken-2',
    waiting_for_customer: 'light-blue-darken-1',
    customer_follow_up: 'deep-purple-lighten-1',
    resolved: 'green-darken-1',
    closed: 'grey-darken-1'
};
const statusTexts = {
    new_issue: '新问题',
    in_progress: '处理中',
    waiting_for_customer: '等待客户回复',
    customer_follow_up: '客户追问',
    resolved: '已解决',
    closed: '已关闭'
};

const priorityColors = {
    low: 'blue-grey-lighten-2',
    medium: 'blue-lighten-1',
    high: 'orange-darken-2',
    urgent: 'red-darken-2'
};
const priorityTexts = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
};

const importanceColors = {
    low: 'green-lighten-3',
    medium: 'yellow-lighten-2',
    high: 'red-lighten-2'
};
const importanceTexts = {
    low: '一般',
    medium: '重要',
    high: '非常重要'
};

const getStatusColor = (status) => statusColors[status] || 'grey';
const getStatusText = (status) => statusTexts[status] || status;
const getPriorityColor = (priority) => priorityColors[priority] || 'grey';
const getPriorityText = (priority) => priorityTexts[priority] || priority;
const getImportanceColor = (importance) => importanceColors[importance] || 'grey';
const getImportanceText = (importance) => importanceTexts[importance] || importance;

const getSlaProgressColor = (percentage) => {
  if (percentage > 90) return 'red-darken-2';
  if (percentage > 75) return 'deep-orange';
  return 'amber-darken-1';
};

const getIdleProgressColor = (percentage) => {
  if (percentage > 90) return 'orange-darken-3';
  if (percentage > 75) return 'orange-lighten-1';
  return 'yellow-lighten-2';
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(dateString).toLocaleDateString(undefined, options);
};

watch(activeTab, (newTab) => {
  if (newTab === 'active' && !activeTickets.value.length) loadActiveTickets();
  else if (newTab === 'sla' && !slaTickets.value.length) loadSlaTickets();
  else if (newTab === 'idle' && !idleTickets.value.length) loadIdleTickets();
  else if (newTab === 'my' && !myTickets.value.length) loadMyTickets();
});

onMounted(() => {
  loadActiveTickets(); // Load active tickets by default
});

</script>

<style scoped>
.support-dashboard-container {
  padding: 24px;
}

.support-dashboard-card {
  border-radius: 8px;
}

.text-h5 {
  font-weight: 500;
  padding: 16px 24px;
  background-color: rgb(var(--v-theme-primary));
  color: white;
}

.text-h6 {
  font-weight: 500;
  color: #333;
}

.v-data-table {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.v-chip {
  font-weight: 500;
}

.v-progress-linear strong {
  font-size: 0.8rem;
}

.v-alert {
  border-radius: 4px;
}
</style>

