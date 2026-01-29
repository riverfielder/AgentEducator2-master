<template>;
  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    :timeout="snackbar.timeout"
    location="top"
    :style="{top: '24px'}"
  >;
    {{ snackbar.text }}
    
    <template v-slot:actions>;
      <v-btn
        icon="mdi-close"
        variant="text"
        @click="snackbar.show = false"
      >;</v-btn>;
    </template>;
  </v-snackbar>;
</template>;

<script>;
export default {
  name: 'GlobalSnackbar',
  data() {
    return {
      snackbar: {
        show: false,
        text: '',
        color: 'success',
        timeout: 3000
      }
    }
  },
  created() {
    // 全局事件总线
    this.$router.app.config.globalProperties.$showSnackbar = this.showSnackbar
    
    // 添加事件监听
    window.addEventListener('show-snackbar', this.handleShowSnackbarEvent)
  },
  beforeUnmount() {
    // 移除事件监听
    window.removeEventListener('show-snackbar', this.handleShowSnackbarEvent)
  },
  methods: {
    /**
     * 显示消息通知
     * @param {Object|string} config 配置或消息文本
     */
    showSnackbar(config) {
      if (typeof config === 'string') {
        this.snackbar = {
          show: true,
          text: config,
          color: 'info',
          timeout: 3000
        }
      } else {
        this.snackbar = {
          show: true,
          text: config.message || '',
          color: config.color || 'info',
          timeout: config.timeout || 3000
        }
      }
    },
    
    /**
     * 处理自定义事件
     * @param {CustomEvent} event 事件对象
     */
    handleShowSnackbarEvent(event) {
      if (event && event.detail) {
        this.showSnackbar(event.detail)
      }
    }
  }
}
</script>;
