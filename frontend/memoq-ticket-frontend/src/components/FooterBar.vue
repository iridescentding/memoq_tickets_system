<template>
  <v-footer app class="mt-auto footer-container">
    <v-container fluid class="pa-0">
      <v-card flat tile width="100%" class="footer-card">
        <v-card-text class="d-flex justify-center align-center py-2">
          <span class="footer-text">
            &copy; {{ currentYear }} memoQ中国区客户技术支持工单系统 | 技术支持：
            <a
              href="mailto:support@memoq.cn"
              class="text-decoration-none font-weight-medium primary-link"
            >
              support@memoq.cn
            </a>
          </span>
        </v-card-text>
      </v-card>
    </v-container>
  </v-footer>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'FooterBar',
  setup() {
    const currentYear = computed(() => new Date().getFullYear());
    return {
      currentYear
    };
  }
};
</script>

<style scoped>
.footer-container {
  background-color: #f5f5f5;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.footer-card {
  background-color: transparent !important;
}

.footer-text {
  color: rgba(0, 0, 0, 0.7);
  font-size: 0.875rem;
}

.primary-link {
  color: var(--v-theme-primary);
  transition: opacity 0.2s ease;
}

.primary-link:hover {
  opacity: 0.8;
}
</style>
