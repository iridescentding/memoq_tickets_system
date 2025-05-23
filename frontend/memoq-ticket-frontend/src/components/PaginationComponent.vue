<template>
  <div class="pagination-wrapper">
    <v-pagination
      v-model="currentPageModel"
      :length="totalPages"
      :total-visible="7"
      rounded
      @update:model-value="onPageChange"
    ></v-pagination>
    
    <div class="d-flex align-center ms-4">
      <span class="text-caption text-medium-emphasis me-2">每页显示:</span>
      <v-select
        v-model="pageSizeModel"
        :items="pageSizeOptions"
        variant="outlined"
        density="compact"
        hide-details
        class="pagination-select"
        @update:model-value="onPageSizeChange"
      ></v-select>
      <span class="text-caption text-medium-emphasis ms-4">
        共 {{ totalItems }} 条记录，当前显示 {{ startItem }}-{{ endItem }}
      </span>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch } from 'vue';

export default {
  name: 'PaginationComponent',
  props: {
    currentPage: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 10
    },
    totalItems: {
      type: Number,
      required: true
    },
    pageSizeOptions: {
      type: Array,
      default: () => [10, 15, 20, 50, 100]
    }
  },
  emits: ['update:currentPage', 'update:pageSize', 'page-change'],
  setup(props, { emit }) {
    // 使用本地状态跟踪当前页和每页大小，以避免直接修改props
    const currentPageModel = ref(props.currentPage);
    const pageSizeModel = ref(props.pageSize);
    
    // 计算总页数
    const totalPages = computed(() => {
      return Math.ceil(props.totalItems / pageSizeModel.value) || 1;
    });
    
    // 计算当前页显示的记录范围
    const startItem = computed(() => {
      if (props.totalItems === 0) return 0;
      return (currentPageModel.value - 1) * pageSizeModel.value + 1;
    });
    
    const endItem = computed(() => {
      if (props.totalItems === 0) return 0;
      return Math.min(currentPageModel.value * pageSizeModel.value, props.totalItems);
    });
    
    // 监听props变化，更新本地状态
    watch(() => props.currentPage, (newVal) => {
      currentPageModel.value = newVal;
    });
    
    watch(() => props.pageSize, (newVal) => {
      pageSizeModel.value = newVal;
    });
    
    // 当页码变化时触发事件
    const onPageChange = (page) => {
      emit('update:currentPage', page);
      emit('page-change', { page, pageSize: pageSizeModel.value });
    };
    
    // 当每页大小变化时触发事件
    const onPageSizeChange = (size) => {
      // 计算新的页码，尽量保持当前查看的记录在视图中
      const firstItemIndex = (currentPageModel.value - 1) * props.pageSize;
      const newPage = Math.floor(firstItemIndex / size) + 1;
      
      // 更新本地状态和触发事件
      currentPageModel.value = newPage;
      emit('update:pageSize', size);
      emit('update:currentPage', newPage);
      emit('page-change', { page: newPage, pageSize: size });
    };
    
    return {
      currentPageModel,
      pageSizeModel,
      totalPages,
      startItem,
      endItem,
      onPageChange,
      onPageSizeChange
    };
  }
};
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  padding: 8px 0;
}

.pagination-select {
  width: 80px;
}

@media (max-width: 600px) {
  .pagination-wrapper {
    flex-direction: column;
    align-items: center;
  }
  
  .pagination-wrapper > div {
    margin-top: 12px;
    margin-left: 0 !important;
  }
}
</style>
