<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-card :loading="loadingTicket || submitting">
          <v-card-title class="text-h5 text-center py-4">
            <v-icon left class="mr-2">mdi-star-circle-outline</v-icon>
            工单满意度评价
          </v-card-title>
          <v-divider></v-divider>

          <template v-if="loadingTicket">
            <v-skeleton-loader type="article, actions"></v-skeleton-loader>
          </template>
          <template v-else-if="!ticket">
             <v-alert type="error" prominent class="ma-4">
                无法加载工单信息，或此工单不符合评价条件。
             </v-alert>
          </template>
          <template v-else-if="ticket.satisfaction_rating_data">
            <v-alert type="success" prominent class="ma-4">
                <v-icon left>mdi-check-circle</v-icon>
                感谢您的评价！此工单已评价。
            </v-alert>
            <v-card-text class="text-center">
                <p>您的评分: <v-rating :model-value="ticket.satisfaction_rating_data.rating" color="amber" density="compact" readonly half-increments></v-rating></p>
                <p v-if="ticket.satisfaction_rating_data.comment">您的评论: {{ ticket.satisfaction_rating_data.comment }}</p>
                <v-btn color="primary" @click="goToTicketDetail" class="mt-4">返回工单详情</v-btn>
            </v-card-text>
          </template>
          <template v-else>
            <v-card-text>
              <p class="mb-2">您好，<strong>{{ authStore.currentUser?.username }}</strong>！</p>
              <p class="mb-1">我们希望了解您对工单 <strong>#{{ ticketId }} - {{ ticket.title }}</strong> 的处理是否满意。</p>
              <p class="mb-4">请为本次服务打分：</p>
              
              <div class="text-center mb-4">
                <v-rating
                  v-model="rating"
                  hover
                  half-increments
                  clearable
                  :length="5"
                  :item-labels="['很不满意', '不满意', '一般', '满意', '非常满意']"
                  item-label-position="top"
                  color="amber"
                  active-color="amber"
                  size="x-large"
                >
                  <template v-slot:item-label="props">
                    <span
                      :class="`text-${props.isFilled ? 'amber' : 'grey'}`"
                      class="caption"
                    >
                      {{ props.label }}
                    </span>
                  </template>
                </v-rating>
              </div>

              <v-textarea
                v-model="comment"
                label="您的宝贵意见 (可选)"
                rows="4"
                variant="outlined"
                placeholder="如果您有其他建议或意见，请告诉我们。"
                clearable
              ></v-textarea>
            </v-card-text>

            <v-card-actions class="pa-4">
              <v-btn 
                variant="text" 
                @click="closeWithoutRating"
                :disabled="submitting"
              >
                暂不评价并关闭工单
              </v-btn>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                @click="submitRating"
                :loading="submitting"
                :disabled="rating === 0"
                size="large"
                variant="elevated"
              >
                <v-icon left>mdi-send</v-icon>
                提交评价
              </v-btn>
            </v-card-actions>
          </template>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/api';
import { useSnackbarStore } from '@/store/snackbar';
import { useAuthStore } from '@/store/auth';

const route = useRoute();
const router = useRouter();
const snackbarStore = useSnackbarStore();
const authStore = useAuthStore();

const ticketId = ref(route.params.ticketId);
const ticket = ref(null);
const loadingTicket = ref(true);
const submitting = ref(false);

const rating = ref(5); // Default to 5 stars
const comment = ref('');

async function fetchTicketDetails() {
  if (!ticketId.value) return;
  loadingTicket.value = true;
  try {
    const response = await api.get(`/tickets/${ticketId.value}/`);
    ticket.value = response.data;
    if (ticket.value.status !== 'resolved' && ticket.value.status !== 'closed') {
        // Or if already rated, redirect or show message
        // For now, just log. Frontend should ideally only route here if eligible.
        console.warn("工单状态不符合评价条件。");
    }
    if (ticket.value.satisfaction_rating_data) {
        console.log("此工单已评价。");
    }
  } catch (error) {
    console.error("获取工单详情失败:", error);
    snackbarStore.setSnackbar({ text: `获取工单详情失败: ${error.message || error}`, color: 'error' });
  } finally {
    loadingTicket.value = false;
  }
}

async function submitRating() {
  if (rating.value === 0) {
    snackbarStore.setSnackbar({ text: '请至少选择1颗星进行评价。', color: 'warning' });
    return;
  }
  submitting.value = true;
  try {
    const payload = {
      ticket: ticketId.value,
      rating: rating.value,
      comment: comment.value || null, // Send null if empty
    };
    await api.post(`/tickets/${ticketId.value}/rate_ticket/`, payload); // Assuming this action exists
    // Or use the dedicated endpoint: await api.post(`/ticket-satisfaction-ratings/`, payload);
    
    snackbarStore.setSnackbar({ text: '感谢您的评价！工单已关闭。', color: 'success' });
    // Optionally close the ticket if not already closed by rating
    if (ticket.value && ticket.value.status !== 'closed') {
        await api.patch(`/tickets/${ticketId.value}/`, { status: 'closed', closing_reason_type: 'customer_completed' });
    }
    router.push({ name: 'TicketDetail', params: { id: ticketId.value } });
  } catch (error) {
    console.error("提交评价失败:", error.response?.data || error.message);
    snackbarStore.setSnackbar({ text: `提交评价失败: ${error.response?.data?.detail || error.message || error}`, color: 'error' });
  } finally {
    submitting.value = false;
  }
}

async function closeWithoutRating() {
  // This function implies closing the ticket with a default rating or no rating.
  // Backend should handle default rating if ticket is closed without explicit rating.
  // For now, we'll just close the ticket and navigate away.
  submitting.value = true;
  try {
    if (ticket.value && ticket.value.status !== 'closed') {
      // Create a default 5-star rating with no comment
      const payload = {
        ticket: ticketId.value,
        rating: 5, // Default 5 stars
        comment: null,
      };
      // Attempt to submit default rating. If it fails (e.g., already rated), it's okay.
      try {
        await api.post(`/tickets/${ticketId.value}/rate_ticket/`, payload);
      } catch (ratingError) {
        console.warn("创建默认评价失败 (可能已评价):", ratingError.response?.data || ratingError.message);
      }
      // Then close the ticket
      await api.patch(`/tickets/${ticketId.value}/`, { status: 'closed', closing_reason_type: 'customer_completed', closing_reason_detail: '客户直接关闭，未提供评价。' });
    }
    snackbarStore.setSnackbar({ text: '工单已关闭。', color: 'info' });
    router.push({ name: 'TicketDetail', params: { id: ticketId.value } }); // Or to ticket list
  } catch (error) {
    console.error("关闭工单失败:", error.response?.data || error.message);
    snackbarStore.setSnackbar({ text: `关闭工单失败: ${error.response?.data?.detail || error.message || error}`, color: 'error' });
  } finally {
    submitting.value = false;
  }
}

function goToTicketDetail() {
    router.push({ name: 'TicketDetail', params: { id: ticketId.value } });
}


onMounted(() => {
  if (authStore.isCustomer || authStore.isSystemAdmin) { // Allow admin to see/test form
    fetchTicketDetails();
  } else {
    snackbarStore.setSnackbar({ text: '您没有权限访问此页面。', color: 'error' });
    router.push({ name: 'Home' }); // Or appropriate redirect
  }
});
</script>

<style scoped>
.v-rating .v-icon {
  padding: 0 4px; /* Adjust spacing between stars */
}
</style>
