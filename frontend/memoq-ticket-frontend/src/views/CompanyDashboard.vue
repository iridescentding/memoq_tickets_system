<!-- 公司用户Dashboard组件 -->
<template>
  <div>
    <!-- 面包屑导航 -->
    <v-breadcrumbs :items="breadcrumbs" class="pa-0 mb-4">
      <template v-slot:divider>
        <v-icon>mdi-chevron-right</v-icon>
      </template>
    </v-breadcrumbs>

    <v-card class="mb-6">
      <v-card-title class="text-h5">
        我的工单概览
        <v-spacer></v-spacer>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="navigateToCreateTicket">
          创建工单
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-card variant="outlined" class="text-center">
              <v-card-title class="text-h6">我的活跃工单</v-card-title>
              <v-card-text>
                <span class="text-h3 font-weight-bold">{{ myActiveTicketsCount }}</span>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card variant="outlined" class="text-center">
              <v-card-title class="text-h6">需要我关注的工单</v-card-title>
              <v-card-text>
                <span class="text-h3 font-weight-bold">{{ followingTicketsCount }}</span>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="4">
            <v-card variant="outlined" class="text-center">
              <v-card-title class="text-h6">公司所有工单</v-card-title>
              <v-card-text>
                <span class="text-h3 font-weight-bold">{{ companyTicketsCount }}</span>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 工单标签页 -->
    <v-tabs v-model="activeTab" bg-color="primary">
      <v-tab value="my-tickets">我的工单</v-tab>
      <v-tab value="following-tickets">需要我关注的工单</v-tab>
      <v-tab value="company-tickets">公司所有工单</v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <!-- 我的工单 -->
      <v-window-item value="my-tickets">
        <v-card flat>
          <v-card-text>
            <v-data-table
              :headers="ticketHeaders"
              :items="myTickets"
              :loading="loading"
              :items-per-page="10"
              class="elevation-1"
            >
              <template v-slot:item.title="{ item }">
                <router-link :to="{ name: 'TicketDetail', params: { id: item.id } }">
                  {{ item.title }}
                </router-link>
              </template>
              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ item.status_display }}
                </v-chip>
              </template>
              <template v-slot:item.urgency="{ item }">
                <v-chip :color="getUrgencyColor(item.urgency)" size="small">
                  {{ item.urgency_display }}
                </v-chip>
              </template>
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>
              <template v-slot:item.last_activity_at="{ item }">
                {{ formatDate(item.last_activity_at) }}
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- 需要我关注的工单 -->
      <v-window-item value="following-tickets">
        <v-card flat>
          <v-card-text>
            <v-data-table
              :headers="ticketHeaders"
              :items="followingTickets"
              :loading="loading"
              :items-per-page="10"
              class="elevation-1"
            >
              <template v-slot:item.title="{ item }">
                <router-link :to="{ name: 'TicketDetail', params: { id: item.id } }">
                  {{ item.title }}
                </router-link>
              </template>
              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ item.status_display }}
                </v-chip>
              </template>
              <template v-slot:item.urgency="{ item }">
                <v-chip :color="getUrgencyColor(item.urgency)" size="small">
                  {{ item.urgency_display }}
                </v-chip>
              </template>
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>
              <template v-slot:item.last_activity_at="{ item }">
                {{ formatDate(item.last_activity_at) }}
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- 公司所有工单 -->
      <v-window-item value="company-tickets">
        <v-card flat>
          <v-card-text>
            <v-data-table
              :headers="companyTicketHeaders"
              :items="companyTickets"
              :loading="loading"
              :items-per-page="10"
              class="elevation-1"
            >
              <template v-slot:item.title="{ item }">
                <router-link :to="{ name: 'TicketDetail', params: { id: item.id } }">
                  {{ item.title }}
                </router-link>
              </template>
              <template v-slot:item.submitted_by="{ item }">
                {{ item.submitted_by_details?.username || '未知' }}
              </template>
              <template v-slot:item.status="{ item }">
                <v-chip :color="getStatusColor(item.status)" size="small">
                  {{ item.status_display }}
                </v-chip>
              </template>
              <template v-slot:item.urgency="{ item }">
                <v-chip :color="getUrgencyColor(item.urgency)" size="small">
                  {{ item.urgency_display }}
                </v-chip>
              </template>
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>
              <template v-slot:item.last_activity_at="{ item }">
                {{ formatDate(item.last_activity_at) }}
              </template>
              <template v-slot:item.followers="{ item }">
                <v-chip-group>
                  <v-chip
                    v-for="follower in item.followers_data.slice(0, 2)"
                    :key="follower.id"
                    size="small"
                    color="info"
                  >
                    {{ follower.username }}
                  </v-chip>
                  <v-chip v-if="item.followers_data.length > 2" size="small" color="info">
                    +{{ item.followers_data.length - 2 }}
                  </v-chip>
                </v-chip-group>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import api from '@/api';
import { format } from 'date-fns';

export default {
  name: 'CompanyDashboard',
  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const loading = ref(false);
    const activeTab = ref('my-tickets');
    
    // 工单数据
    const myTickets = ref([]);
    const followingTickets = ref([]);
    const companyTickets = ref([]);
    
    // 计算属性：工单数量
    const myActiveTicketsCount = computed(() => 
      myTickets.value.filter(ticket => 
        !['resolved', 'closed'].includes(ticket.status)
      ).length
    );
    const followingTicketsCount = computed(() => followingTickets.value.length);
    const companyTicketsCount = computed(() => companyTickets.value.length);
    
    // 面包屑导航
    const breadcrumbs = [
      {
        title: '首页',
        disabled: false,
        href: '/',
      },
      {
        title: '公司工单管理',
        disabled: true,
      },
    ];
    
    // 表头定义
    const ticketHeaders = [
      { title: '工单标题', key: 'title', sortable: true },
      { title: '状态', key: 'status', sortable: true },
      { title: '紧急度', key: 'urgency', sortable: true },
      { title: '创建时间', key: 'created_at', sortable: true },
      { title: '最近活动', key: 'last_activity_at', sortable: true },
    ];
    
    const companyTicketHeaders = [
      { title: '工单标题', key: 'title', sortable: true },
      { title: '提交人', key: 'submitted_by', sortable: true },
      { title: '状态', key: 'status', sortable: true },
      { title: '紧急度', key: 'urgency', sortable: true },
      { title: '创建时间', key: 'created_at', sortable: true },
      { title: '最近活动', key: 'last_activity_at', sortable: true },
      { title: '关注人', key: 'followers', sortable: false },
    ];
    
    // 获取我的工单
    const fetchMyTickets = async () => {
      try {
        const response = await api.get('/tickets/', {
          params: {
            created_by: authStore.userId,
            ordering: '-created_at'
          }
        });
        myTickets.value = response.data.results || [];
      } catch (error) {
        console.error('获取我的工单失败:', error);
      }
    };
    
    // 获取我关注的工单
    const fetchFollowingTickets = async () => {
      try {
        const response = await api.get('/tickets/following/');
        followingTickets.value = response.data.results || [];
      } catch (error) {
        console.error('获取关注工单失败:', error);
      }
    };
    
    // 获取公司所有工单
    const fetchCompanyTickets = async () => {
      try {
        const response = await api.get('/tickets/company/');
        companyTickets.value = response.data.results || [];
      } catch (error) {
        console.error('获取公司工单失败:', error);
      }
    };
    
    // 加载所有工单数据
    const fetchAllTickets = async () => {
      loading.value = true;
      try {
        await Promise.all([
          fetchMyTickets(),
          fetchFollowingTickets(),
          fetchCompanyTickets()
        ]);
      } catch (error) {
        console.error('加载工单数据失败:', error);
      } finally {
        loading.value = false;
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
    
    // 导航到创建工单页面
    const navigateToCreateTicket = () => {
      router.push({ name: 'CreateTicket' });
    };
    
    onMounted(() => {
      fetchAllTickets();
    });
    
    return {
      loading,
      activeTab,
      myTickets,
      followingTickets,
      companyTickets,
      myActiveTicketsCount,
      followingTicketsCount,
      companyTicketsCount,
      breadcrumbs,
      ticketHeaders,
      companyTicketHeaders,
      formatDate,
      getStatusColor,
      getUrgencyColor,
      navigateToCreateTicket
    };
  }
};
</script>

<style scoped>
.v-data-table a {
  text-decoration: none;
  color: var(--v-primary-base);
}
</style>
