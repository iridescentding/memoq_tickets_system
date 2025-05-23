<!-- 工单列表页面集成分页组件 -->
<template>
  <div class="ticket-list">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center flex-wrap">
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-ticket</v-icon>
          <span>工单列表</span>
        </div>
        <v-text-field
          v-model="search"
          append-icon="mdi-magnify"
          label="搜索工单"
          single-line
          hide-details
          density="compact"
          variant="outlined"
          class="search-field"
        ></v-text-field>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text class="pa-0">
        <v-data-table
          :headers="headers"
          :items="tickets"
          :loading="loading"
          class="elevation-0"
        >
          <template v-slot:item.title="{ item }">
            <a @click.prevent="viewTicket(item)" class="ticket-title">{{ item.title }}</a>
          </template>
          
          <template v-slot:item.status="{ item }">
            <v-chip
              :color="getStatusColor(item.status)"
              size="small"
              label
            >
              {{ getStatusText(item.status) }}
            </v-chip>
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
          
          <template v-slot:item.created_at="{ item }">
            {{ formatDate(item.created_at) }}
          </template>
          
          <template v-slot:item.actions="{ item }">
            <v-btn
              size="small"
              variant="text"
              color="primary"
              @click="viewTicket(item)"
            >
              <v-icon size="small">mdi-eye</v-icon>
              查看
            </v-btn>
          </template>
          
          <template v-slot:no-data>
            <div class="text-center pa-5">
              <v-icon size="large" color="grey-lighten-1">mdi-ticket-outline</v-icon>
              <p class="mt-3 text-grey-darken-1">暂无工单数据</p>
            </div>
          </template>
          
          <template v-slot:bottom>
            <div class="pa-4">
              <pagination-component
                :current-page="currentPage"
                :page-size="pageSize"
                :total-items="totalTickets"
                :page-size-options="[10, 15, 20, 50, 100]"
                @update:current-page="updatePage"
                @update:page-size="updatePageSize"
                @page-change="onPageChange"
              />
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useSnackbarStore } from '@/store/snackbar';
import api from '@/api';
import PaginationComponent from '@/components/PaginationComponent.vue';

export default {
  name: 'TicketList',
  components: {
    PaginationComponent
  },
  
  setup() {
    const router = useRouter();
    const snackbarStore = useSnackbarStore();
    
    // 状态
    const tickets = ref([]);
    const loading = ref(false);
    const totalTickets = ref(0);
    const search = ref('');
    const currentPage = ref(1);
    const pageSize = ref(20); // 默认每页20条
    
    // 表头
    const headers = [
      { title: '工单ID', key: 'id', sortable: true },
      { title: '标题', key: 'title', sortable: true },
      { title: '公司', key: 'company.name', sortable: true },
      { title: '提交人', key: 'submitted_by.username', sortable: true },
      { title: '状态', key: 'status', sortable: true },
      { title: '紧急度', key: 'urgency', sortable: true },
      { title: '创建时间', key: 'created_at', sortable: true },
      { title: '操作', key: 'actions', sortable: false }
    ];
    
    // 计算属性
    const queryParams = computed(() => {
      const params = {
        page: currentPage.value,
        page_size: pageSize.value,
        ordering: '-created_at' // 默认按创建时间降序
      };
      
      // 添加搜索
      if (search.value) {
        params.search = search.value;
      }
      
      return params;
    });
    
    // 方法
    const fetchTickets = async () => {
      loading.value = true;
      
      try {
        const response = await api.get('/tickets/', { params: queryParams.value });
        tickets.value = response.data.results;
        totalTickets.value = response.data.count;
      } catch (error) {
        console.error('获取工单列表失败:', error);
        snackbarStore.setSnackbar({
          show: true,
          text: '获取工单列表失败，请稍后重试',
          color: 'error'
        });
      } finally {
        loading.value = false;
      }
    };
    
    const viewTicket = (ticket) => {
      router.push({ name: 'TicketDetail', params: { id: ticket.id } });
    };
    
    const updatePage = (page) => {
      currentPage.value = page;
    };
    
    const updatePageSize = (size) => {
      pageSize.value = size;
    };
    
    const onPageChange = () => {
      fetchTickets();
    };
    
    const getStatusColor = (status) => {
      const statusColors = {
        'open': 'blue',
        'in_progress': 'orange',
        'resolved': 'green',
        'closed': 'grey',
        'pending': 'purple',
        'paused': 'cyan'
      };
      return statusColors[status] || 'grey';
    };
    
    const getStatusText = (status) => {
      const statusTexts = {
        'open': '待处理',
        'in_progress': '处理中',
        'resolved': '已解决',
        'closed': '已关闭',
        'pending': '待回复',
        'paused': '已暂停'
      };
      return statusTexts[status] || status;
    };
    
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
    
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    // 监听搜索变化
    const debouncedSearch = () => {
      const timer = ref(null);
      return () => {
        clearTimeout(timer.value);
        timer.value = setTimeout(() => {
          currentPage.value = 1; // 重置到第一页
          fetchTickets();
        }, 500);
      };
    };
    
    const handleSearch = debouncedSearch();
    
    // 监听搜索变化
    watch(search, () => {
      handleSearch();
    });
    
    // 生命周期钩子
    onMounted(() => {
      fetchTickets();
    });
    
    return {
      tickets,
      loading,
      totalTickets,
      search,
      currentPage,
      pageSize,
      headers,
      fetchTickets,
      viewTicket,
      updatePage,
      updatePageSize,
      onPageChange,
      getStatusColor,
      getStatusText,
      getUrgencyColor,
      getUrgencyText,
      formatDate
    };
  }
};
</script>

<style scoped>
.ticket-list {
  padding: 16px;
}

.search-field {
  max-width: 300px;
}

.ticket-title {
  color: var(--v-primary-base);
  text-decoration: none;
  cursor: pointer;
}

.ticket-title:hover {
  text-decoration: underline;
}

@media (max-width: 600px) {
  .v-card-title {
    flex-direction: column;
    align-items: stretch !important;
  }
  
  .search-field {
    max-width: 100%;
    margin-top: 16px;
  }
}
</style>
