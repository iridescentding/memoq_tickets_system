<template>
  <div class="admin-dashboard">
    <v-container fluid>
      <!-- 面包屑导航 -->
      <v-breadcrumbs :items="breadcrumbs" class="pa-0 mb-4">
        <template v-slot:divider>
          <v-icon>mdi-chevron-right</v-icon>
        </template>
      </v-breadcrumbs>
      
      <h1 class="text-h4 mb-6">管理员仪表盘</h1>
      
      <!-- 待分配工单表格 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-ticket-account</v-icon>
          待分配工单
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="pa-0">
          <v-data-table
            :headers="pendingAssignmentHeaders"
            :items="pendingAssignmentTickets"
            :loading="loadingPendingAssignment"
            class="elevation-0"
          >
            <template v-slot:item.title="{ item }">
              <a @click.prevent="viewTicket(item)" class="ticket-title">{{ item.title }}</a>
            </template>
            
            <template v-slot:item.urgency="{ item }">
              <v-chip
                :color="getUrgencyColor(item.urgency)"
                size="small"
                label
              >
                {{ getUrgencyText(item.urgency) }}
              </v-chip>
            </template>
            
            <template v-slot:item.sla="{ item }">
              {{ formatSLA(item.sla_minutes) }}
            </template>
            
            <template v-slot:item.actions="{ item }">
              <v-select
                v-model="selectedSupportUser[item.id]"
                :items="supportUsers"
                item-title="username"
                item-value="id"
                label="选择技术支持"
                density="compact"
                variant="outlined"
                hide-details
                class="support-select"
              ></v-select>
              
              <v-btn
                size="small"
                color="primary"
                class="ml-2"
                :disabled="!selectedSupportUser[item.id]"
                @click="assignTicket(item)"
              >
                分配
              </v-btn>
            </template>
            
            <template v-slot:no-data>
              <div class="text-center pa-5">
                <v-icon size="large" color="success">mdi-check-circle</v-icon>
                <p class="mt-3 text-grey-darken-1">没有待分配的工单</p>
              </div>
            </template>
            
            <template v-slot:bottom>
              <div class="pa-4">
                <pagination-component
                  :current-page="pendingAssignmentPage"
                  :page-size="pendingAssignmentPageSize"
                  :total-items="totalPendingAssignmentTickets"
                  :page-size-options="[5, 10, 15, 20]"
                  @update:current-page="updatePendingAssignmentPage"
                  @update:page-size="updatePendingAssignmentPageSize"
                  @page-change="onPendingAssignmentPageChange"
                />
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <!-- 即将miss IR和已miss IR表格 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-timer-alert</v-icon>
          即将miss IR和已miss IR工单
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="pa-0">
          <v-data-table
            :headers="missIRHeaders"
            :items="missIRTickets"
            :loading="loadingMissIR"
            class="elevation-0"
          >
            <template v-slot:item.title="{ item }">
              <a @click.prevent="viewTicket(item)" class="ticket-title">{{ item.title }}</a>
            </template>
            
            <template v-slot:item.urgency="{ item }">
              <v-chip
                :color="getUrgencyColor(item.urgency)"
                size="small"
                label
              >
                {{ getUrgencyText(item.urgency) }}
              </v-chip>
            </template>
            
            <template v-slot:item.priority="{ item }">
              <v-chip
                :color="getPriorityColor(item.priority)"
                size="small"
                label
              >
                {{ getPriorityText(item.priority) }}
              </v-chip>
            </template>
            
            <template v-slot:item.time_to_miss_ir="{ item }">
              <span :class="{ 'text-red': item.is_missed_ir }">
                {{ item.is_missed_ir ? '已miss IR' : formatTimeRemaining(item.time_to_miss_ir_seconds) }}
              </span>
            </template>
            
            <template v-slot:no-data>
              <div class="text-center pa-5">
                <v-icon size="large" color="success">mdi-check-circle</v-icon>
                <p class="mt-3 text-grey-darken-1">没有即将miss IR的工单</p>
              </div>
            </template>
            
            <template v-slot:bottom>
              <div class="pa-4">
                <pagination-component
                  :current-page="missIRPage"
                  :page-size="missIRPageSize"
                  :total-items="totalMissIRTickets"
                  :page-size-options="[5, 15, 20, 50]"
                  @update:current-page="updateMissIRPage"
                  @update:page-size="updateMissIRPageSize"
                  @page-change="onMissIRPageChange"
                />
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <!-- 即将idle和已idle表格 -->
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-timer-sand</v-icon>
          即将idle和已idle工单
        </v-card-title>
        
        <v-divider></v-divider>
        
        <v-card-text class="pa-0">
          <v-data-table
            :headers="idleHeaders"
            :items="idleTickets"
            :loading="loadingIdle"
            class="elevation-0"
          >
            <template v-slot:item.title="{ item }">
              <a @click.prevent="viewTicket(item)" class="ticket-title">{{ item.title }}</a>
            </template>
            
            <template v-slot:item.urgency="{ item }">
              <v-chip
                :color="getUrgencyColor(item.urgency)"
                size="small"
                label
              >
                {{ getUrgencyText(item.urgency) }}
              </v-chip>
            </template>
            
            <template v-slot:item.priority="{ item }">
              <v-chip
                :color="getPriorityColor(item.priority)"
                size="small"
                label
              >
                {{ getPriorityText(item.priority) }}
              </v-chip>
            </template>
            
            <template v-slot:item.time_to_idle="{ item }">
              <span :class="{ 'text-red': item.is_idle }">
                {{ item.is_idle ? '已idle' : formatTimeRemaining(item.time_to_idle_seconds) }}
              </span>
            </template>
            
            <template v-slot:no-data>
              <div class="text-center pa-5">
                <v-icon size="large" color="success">mdi-check-circle</v-icon>
                <p class="mt-3 text-grey-darken-1">没有即将idle的工单</p>
              </div>
            </template>
            
            <template v-slot:bottom>
              <div class="pa-4">
                <pagination-component
                  :current-page="idlePage"
                  :page-size="idlePageSize"
                  :total-items="totalIdleTickets"
                  :page-size-options="[5, 15, 20, 50]"
                  @update:current-page="updateIdlePage"
                  @update:page-size="updateIdlePageSize"
                  @page-change="onIdlePageChange"
                />
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSnackbarStore } from '@/store/snackbar';
import api from '@/api';
import PaginationComponent from '@/components/PaginationComponent.vue';

export default {
  name: 'AdminDashboard',
  components: {
    PaginationComponent
  },
  
  setup() {
    const router = useRouter();
    const snackbarStore = useSnackbarStore();
    
    // 面包屑导航
    const breadcrumbs = [
      {
        title: '首页',
        disabled: false,
        href: '/'
      },
      {
        title: '管理员仪表盘',
        disabled: true
      }
    ];
    
    // 待分配工单
    const pendingAssignmentTickets = ref([]);
    const loadingPendingAssignment = ref(false);
    const totalPendingAssignmentTickets = ref(0);
    const pendingAssignmentPage = ref(1);
    const pendingAssignmentPageSize = ref(10); // 默认每页10条
    
    // 即将miss IR和已miss IR工单
    const missIRTickets = ref([]);
    const loadingMissIR = ref(false);
    const totalMissIRTickets = ref(0);
    const missIRPage = ref(1);
    const missIRPageSize = ref(15); // 默认每页15条
    
    // 即将idle和已idle工单
    const idleTickets = ref([]);
    const loadingIdle = ref(false);
    const totalIdleTickets = ref(0);
    const idlePage = ref(1);
    const idlePageSize = ref(15); // 默认每页15条
    
    // 技术支持用户列表
    const supportUsers = ref([]);
    const loadingSupportUsers = ref(false);
    
    // 选中的技术支持用户（用于分配工单）
    const selectedSupportUser = reactive({});
    
    // 表头
    const pendingAssignmentHeaders = [
      { title: '工单ID', key: 'id', sortable: true },
      { title: '标题', key: 'title', sortable: true },
      { title: '公司', key: 'company.name', sortable: true },
      { title: '提交人', key: 'submitted_by.username', sortable: true },
      { title: '紧急度', key: 'urgency', sortable: true },
      { title: 'SLA', key: 'sla', sortable: true },
      { title: '操作', key: 'actions', sortable: false }
    ];
    
    const missIRHeaders = [
      { title: '工单ID', key: 'id', sortable: true },
      { title: '标题', key: 'title', sortable: true },
      { title: '公司', key: 'company.name', sortable: true },
      { title: '提交人', key: 'submitted_by.username', sortable: true },
      { title: '紧急度', key: 'urgency', sortable: true },
      { title: '优先级', key: 'priority', sortable: true },
      { title: '距离miss IR时间', key: 'time_to_miss_ir', sortable: true }
    ];
    
    const idleHeaders = [
      { title: '工单ID', key: 'id', sortable: true },
      { title: '标题', key: 'title', sortable: true },
      { title: '公司', key: 'company.name', sortable: true },
      { title: '提交人', key: 'submitted_by.username', sortable: true },
      { title: '紧急度', key: 'urgency', sortable: true },
      { title: '优先级', key: 'priority', sortable: true },
      { title: '距离idle时间', key: 'time_to_idle', sortable: true }
    ];
    
    // 方法
    const fetchPendingAssignmentTickets = async () => {
      loadingPendingAssignment.value = true;
      
      try {
        const response = await api.get('/admin/dashboard/pending-assignment-tickets/', {
          params: {
            page: pendingAssignmentPage.value,
            page_size: pendingAssignmentPageSize.value
          }
        });
        
        pendingAssignmentTickets.value = response.data.results;
        totalPendingAssignmentTickets.value = response.data.count;
      } catch (error) {
        console.error('获取待分配工单失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '获取待分配工单失败，请稍后重试',
          color: 'error'
        });
      } finally {
        loadingPendingAssignment.value = false;
      }
    };
    
    const fetchMissIRTickets = async () => {
      loadingMissIR.value = true;
      
      try {
        const response = await api.get('/admin/dashboard/miss-ir-tickets/', {
          params: {
            page: missIRPage.value,
            page_size: missIRPageSize.value
          }
        });
        
        missIRTickets.value = response.data.results;
        totalMissIRTickets.value = response.data.count;
      } catch (error) {
        console.error('获取miss IR工单失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '获取miss IR工单失败，请稍后重试',
          color: 'error'
        });
      } finally {
        loadingMissIR.value = false;
      }
    };
    
    const fetchIdleTickets = async () => {
      loadingIdle.value = true;
      
      try {
        const response = await api.get('/admin/dashboard/idle-tickets/', {
          params: {
            page: idlePage.value,
            page_size: idlePageSize.value
          }
        });
        
        idleTickets.value = response.data.results;
        totalIdleTickets.value = response.data.count;
      } catch (error) {
        console.error('获取idle工单失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '获取idle工单失败，请稍后重试',
          color: 'error'
        });
      } finally {
        loadingIdle.value = false;
      }
    };
    
    const fetchSupportUsers = async () => {
      loadingSupportUsers.value = true;
      
      try {
        const response = await api.get('/users/support-users/');
        supportUsers.value = response.data;
      } catch (error) {
        console.error('获取技术支持用户失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '获取技术支持用户失败，请稍后重试',
          color: 'error'
        });
      } finally {
        loadingSupportUsers.value = false;
      }
    };
    
    const assignTicket = async (ticket) => {
      const supportUserId = selectedSupportUser[ticket.id];
      if (!supportUserId) return;
      
      try {
        await api.post(`/tickets/${ticket.id}/assign/`, {
          support_user_id: supportUserId
        });
        
        // 更新待分配工单列表
        fetchPendingAssignmentTickets();
        
        // 清除选中的技术支持用户
        selectedSupportUser[ticket.id] = null;
        
        snackbarStore.setSnackbar({
          show: true,
          text: `工单 #${ticket.id} 已成功分配`,
          color: 'success'
        });
      } catch (error) {
        console.error('分配工单失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '分配工单失败，请稍后重试',
          color: 'error'
        });
      }
    };
    
    const viewTicket = (ticket) => {
      router.push({ name: 'TicketDetail', params: { id: ticket.id } });
    };
    
    // 分页方法
    const updatePendingAssignmentPage = (page) => {
      pendingAssignmentPage.value = page;
    };
    
    const updatePendingAssignmentPageSize = (size) => {
      pendingAssignmentPageSize.value = size;
    };
    
    const onPendingAssignmentPageChange = () => {
      fetchPendingAssignmentTickets();
    };
    
    const updateMissIRPage = (page) => {
      missIRPage.value = page;
    };
    
    const updateMissIRPageSize = (size) => {
      missIRPageSize.value = size;
    };
    
    const onMissIRPageChange = () => {
      fetchMissIRTickets();
    };
    
    const updateIdlePage = (page) => {
      idlePage.value = page;
    };
    
    const updateIdlePageSize = (size) => {
      idlePageSize.value = size;
    };
    
    const onIdlePageChange = () => {
      fetchIdleTickets();
    };
    
    // 辅助方法
    const getUrgencyColor = (urgency) => {
      const urgencyColors = {
        'low': 'green',
        'medium': 'orange',
        'high': 'red',
        'critical': 'deep-purple'
      };
      return urgencyColors[urgency] || 'grey';
    };
    
    const getUrgencyText = (urgency) => {
      const urgencyTexts = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'critical': '紧急'
      };
      return urgencyTexts[urgency] || urgency;
    };
    
    const getPriorityColor = (priority) => {
      const priorityColors = {
        'low': 'green',
        'medium': 'blue',
        'high': 'orange',
        'critical': 'red'
      };
      return priorityColors[priority] || 'grey';
    };
    
    const getPriorityText = (priority) => {
      const priorityTexts = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'critical': '紧急'
      };
      return priorityTexts[priority] || priority;
    };
    
    const formatSLA = (minutes) => {
      if (!minutes) return '无';
      
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      
      if (hours > 0) {
        return `${hours}小时${remainingMinutes > 0 ? ` ${remainingMinutes}分钟` : ''}`;
      } else {
        return `${minutes}分钟`;
      }
    };
    
    const formatTimeRemaining = (seconds) => {
      if (!seconds) return '无';
      
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      
      if (hours > 0) {
        return `${hours}小时${remainingMinutes > 0 ? ` ${remainingMinutes}分钟` : ''}`;
      } else if (minutes > 0) {
        return `${minutes}分钟`;
      } else {
        return `${seconds}秒`;
      }
    };
    
    // 定时刷新数据
    let refreshInterval = null;
    
    const startRefreshInterval = () => {
      // 每60秒刷新一次数据
      refreshInterval = setInterval(() => {
        fetchPendingAssignmentTickets();
        fetchMissIRTickets();
        fetchIdleTickets();
      }, 60000);
    };
    
    // 生命周期钩子
    onMounted(() => {
      fetchPendingAssignmentTickets();
      fetchMissIRTickets();
      fetchIdleTickets();
      fetchSupportUsers();
      startRefreshInterval();
    });
    
    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    });
    
    return {
      breadcrumbs,
      pendingAssignmentTickets,
      loadingPendingAssignment,
      totalPendingAssignmentTickets,
      pendingAssignmentPage,
      pendingAssignmentPageSize,
      missIRTickets,
      loadingMissIR,
      totalMissIRTickets,
      missIRPage,
      missIRPageSize,
      idleTickets,
      loadingIdle,
      totalIdleTickets,
      idlePage,
      idlePageSize,
      supportUsers,
      selectedSupportUser,
      pendingAssignmentHeaders,
      missIRHeaders,
      idleHeaders,
      assignTicket,
      viewTicket,
      updatePendingAssignmentPage,
      updatePendingAssignmentPageSize,
      onPendingAssignmentPageChange,
      updateMissIRPage,
      updateMissIRPageSize,
      onMissIRPageChange,
      updateIdlePage,
      updateIdlePageSize,
      onIdlePageChange,
      getUrgencyColor,
      getUrgencyText,
      getPriorityColor,
      getPriorityText,
      formatSLA,
      formatTimeRemaining
    };
  }
};
</script>

<style scoped>
.admin-dashboard {
  padding: 16px;
}

.ticket-title {
  color: var(--v-primary-base);
  text-decoration: none;
  cursor: pointer;
}

.ticket-title:hover {
  text-decoration: underline;
}

.support-select {
  max-width: 200px;
  display: inline-block;
}

.text-red {
  color: #ff5252 !important;
  font-weight: bold;
}
</style>
