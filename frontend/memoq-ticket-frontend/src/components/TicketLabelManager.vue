<!-- 工单标签管理组件 -->
<template>
  <div>
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>工单标签管理</span>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          新建标签
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-alert
          v-if="error"
          type="error"
          class="mb-4"
          dismissible
        >
          {{ error }}
        </v-alert>

        <div v-if="loading" class="d-flex justify-center align-center my-4">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <v-data-table
          v-else
          :headers="headers"
          :items="labels"
          :items-per-page="10"
          class="elevation-1"
        >
          <template v-slot:item.name="{ item }">
            <div class="d-flex align-center">
              <v-chip
                :color="item.color"
                size="small"
                class="mr-2"
              >
                {{ item.name }}
              </v-chip>
            </div>
          </template>
          <template v-slot:item.created_at="{ item }">
            {{ formatDate(item.created_at) }}
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              size="small"
              color="primary"
              @click="openEditDialog(item)"
            >
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              color="error"
              @click="openDeleteDialog(item)"
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 创建/编辑标签对话框 -->
    <v-dialog
      v-model="dialog"
      max-width="500px"
    >
      <v-card>
        <v-card-title>
          {{ editedIndex === -1 ? '新建标签' : '编辑标签' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form" v-model="valid">
            <v-text-field
              v-model="editedItem.name"
              label="标签名称"
              :rules="[v => !!v || '标签名称不能为空']"
              required
            ></v-text-field>
            <v-textarea
              v-model="editedItem.description"
              label="标签描述"
              rows="3"
            ></v-textarea>
            <v-color-picker
              v-model="editedItem.color"
              hide-inputs
              show-swatches
              swatches-max-height="200"
            ></v-color-picker>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            text
            @click="closeDialog"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            :disabled="!valid || submitting"
            :loading="submitting"
            @click="saveLabel"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除标签确认对话框 -->
    <v-dialog
      v-model="deleteDialog"
      max-width="400px"
    >
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          您确定要删除标签 <strong>{{ editedItem.name }}</strong> 吗？此操作不可撤销，且会影响所有使用此标签的工单。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            text
            @click="deleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            :loading="submitting"
            @click="deleteLabel"
          >
            确认删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import api from '@/api';
import { format } from 'date-fns';

export default {
  name: 'TicketLabelManager',
  setup() {
    const loading = ref(false);
    const error = ref(null);
    const labels = ref([]);
    const dialog = ref(false);
    const deleteDialog = ref(false);
    const valid = ref(false);
    const form = ref(null);
    const submitting = ref(false);
    
    const headers = [
      { title: '标签名称', key: 'name', sortable: true },
      { title: '描述', key: 'description', sortable: false },
      { title: '创建时间', key: 'created_at', sortable: true },
      { title: '操作', key: 'actions', sortable: false }
    ];
    
    const defaultItem = {
      name: '',
      description: '',
      color: '#1976D2' // 默认蓝色
    };
    
    const editedItem = reactive({...defaultItem});
    const editedIndex = ref(-1);
    
    // 获取所有标签
    const fetchLabels = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await api.get('/ticket-labels/');
        labels.value = response.data.results || [];
      } catch (err) {
        console.error('获取标签失败:', err);
        error.value = '获取标签列表失败，请稍后重试';
      } finally {
        loading.value = false;
      }
    };
    
    // 打开创建标签对话框
    const openCreateDialog = () => {
      editedIndex.value = -1;
      Object.assign(editedItem, defaultItem);
      dialog.value = true;
      
      // 等待DOM更新后重置表单验证
      setTimeout(() => {
        if (form.value) form.value.resetValidation();
      });
    };
    
    // 打开编辑标签对话框
    const openEditDialog = (item) => {
      editedIndex.value = labels.value.indexOf(item);
      Object.assign(editedItem, item);
      dialog.value = true;
      
      // 等待DOM更新后重置表单验证
      setTimeout(() => {
        if (form.value) form.value.resetValidation();
      });
    };
    
    // 打开删除标签对话框
    const openDeleteDialog = (item) => {
      editedIndex.value = labels.value.indexOf(item);
      Object.assign(editedItem, item);
      deleteDialog.value = true;
    };
    
    // 关闭对话框
    const closeDialog = () => {
      dialog.value = false;
      // 等待对话框关闭动画完成后重置表单
      setTimeout(() => {
        editedIndex.value = -1;
        Object.assign(editedItem, defaultItem);
      }, 300);
    };
    
    // 保存标签
    const saveLabel = async () => {
      if (!valid.value) return;
      
      submitting.value = true;
      try {
        if (editedIndex.value > -1) {
          // 更新标签
          await api.put(`/ticket-labels/${editedItem.id}/`, editedItem);
        } else {
          // 创建标签
          await api.post('/ticket-labels/', editedItem);
        }
        
        // 重新获取标签列表
        await fetchLabels();
        closeDialog();
      } catch (err) {
        console.error('保存标签失败:', err);
        error.value = '保存标签失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 删除标签
    const deleteLabel = async () => {
      submitting.value = true;
      try {
        await api.delete(`/ticket-labels/${editedItem.id}/`);
        
        // 重新获取标签列表
        await fetchLabels();
        deleteDialog.value = false;
      } catch (err) {
        console.error('删除标签失败:', err);
        error.value = '删除标签失败，请稍后重试';
      } finally {
        submitting.value = false;
      }
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '未知';
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    };
    
    onMounted(() => {
      fetchLabels();
    });
    
    return {
      loading,
      error,
      labels,
      dialog,
      deleteDialog,
      valid,
      form,
      submitting,
      headers,
      editedItem,
      editedIndex,
      openCreateDialog,
      openEditDialog,
      openDeleteDialog,
      closeDialog,
      saveLabel,
      deleteLabel,
      formatDate
    };
  }
};
</script>
