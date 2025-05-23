<!-- 工单暂停状态管理组件 -->
<template>
  <div>
    <!-- 暂停工单对话框 -->
    <v-dialog v-model="pauseDialog" max-width="500px">
      <v-card>
        <v-card-title>暂停工单</v-card-title>
        <v-card-text>
          <v-alert
            v-if="error"
            type="error"
            class="mb-4"
            dismissible
          >
            {{ error }}
          </v-alert>
          
          <p class="mb-4">暂停工单将取消所有关于idle、SLA等方面的提醒，直到工单被恢复或客户回复。</p>
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
          <v-btn color="grey" @click="cancelPause">取消</v-btn>
          <v-btn
            color="amber"
            :loading="submitting"
            :disabled="!validPauseForm || submitting"
            @click="confirmPause"
          >
            确认暂停
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 恢复工单确认对话框 -->
    <v-dialog v-model="resumeDialog" max-width="400px">
      <v-card>
        <v-card-title>恢复工单</v-card-title>
        <v-card-text>
          <v-alert
            v-if="error"
            type="error"
            class="mb-4"
            dismissible
          >
            {{ error }}
          </v-alert>
          
          <p>您确定要恢复此工单吗？恢复后，SLA和idle计时将重新开始。</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="resumeDialog = false">取消</v-btn>
          <v-btn
            color="success"
            :loading="submitting"
            @click="confirmResume"
          >
            确认恢复
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, reactive } from 'vue';
import api from '@/api';

export default {
  name: 'TicketPauseManager',
  props: {
    ticketId: {
      type: [Number, String],
      required: true
    },
    isPaused: {
      type: Boolean,
      default: false
    }
  },
  emits: ['ticket-paused', 'ticket-resumed', 'error'],
  setup(props, { emit }) {
    const pauseDialog = ref(false);
    const resumeDialog = ref(false);
    const error = ref(null);
    const submitting = ref(false);
    
    // 暂停表单
    const pauseFormRef = ref(null);
    const validPauseForm = ref(false);
    const pauseForm = reactive({
      pause_reason: ''
    });
    
    // 打开暂停对话框
    const openPauseDialog = () => {
      pauseForm.pause_reason = '';
      pauseDialog.value = true;
      
      // 等待DOM更新后重置表单验证
      setTimeout(() => {
        if (pauseFormRef.value) pauseFormRef.value.resetValidation();
      });
    };
    
    // 取消暂停
    const cancelPause = () => {
      pauseDialog.value = false;
      pauseForm.pause_reason = '';
    };
    
    // 确认暂停
    const confirmPause = async () => {
      if (!validPauseForm.value) return;
      
      submitting.value = true;
      error.value = null;
      
      try {
        await api.post(`/tickets/${props.ticketId}/pause/`, pauseForm);
        
        pauseDialog.value = false;
        emit('ticket-paused');
      } catch (err) {
        console.error('暂停工单失败:', err);
        error.value = '暂停工单失败，请稍后重试';
        emit('error', '暂停工单失败，请稍后重试');
      } finally {
        submitting.value = false;
      }
    };
    
    // 打开恢复对话框
    const openResumeDialog = () => {
      resumeDialog.value = true;
    };
    
    // 确认恢复
    const confirmResume = async () => {
      submitting.value = true;
      error.value = null;
      
      try {
        await api.post(`/tickets/${props.ticketId}/resume/`);
        
        resumeDialog.value = false;
        emit('ticket-resumed');
      } catch (err) {
        console.error('恢复工单失败:', err);
        error.value = '恢复工单失败，请稍后重试';
        emit('error', '恢复工单失败，请稍后重试');
      } finally {
        submitting.value = false;
      }
    };
    
    // 暂停/恢复工单
    const togglePauseStatus = () => {
      if (props.isPaused) {
        openResumeDialog();
      } else {
        openPauseDialog();
      }
    };
    
    return {
      pauseDialog,
      resumeDialog,
      error,
      submitting,
      pauseFormRef,
      validPauseForm,
      pauseForm,
      openPauseDialog,
      cancelPause,
      confirmPause,
      openResumeDialog,
      confirmResume,
      togglePauseStatus
    };
  }
};
</script>
