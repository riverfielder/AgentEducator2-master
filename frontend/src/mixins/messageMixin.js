// 消息提示混入
export default {
  methods: {
    $message: {
      success(message) {
        // 使用Vue 3的全局属性或者Vuetify的snackbar
        if (this.$vuetify?.display) {
          // Vuetify 3
          this.$emit('show-snackbar', {
            message,
            color: 'success',
            timeout: 3000
          })
        } else {
          // 降级到控制台日志
          console.log('✅ Success:', message)
        }
      },
      
      error(message) {
        if (this.$vuetify?.display) {
          // Vuetify 3
          this.$emit('show-snackbar', {
            message,
            color: 'error',
            timeout: 5000
          })
        } else {
          // 降级到控制台日志
          console.error('❌ Error:', message)
        }
      },
      
      warning(message) {
        if (this.$vuetify?.display) {
          // Vuetify 3
          this.$emit('show-snackbar', {
            message,
            color: 'warning',
            timeout: 4000
          })
        } else {
          // 降级到控制台日志
          console.warn('⚠️ Warning:', message)
        }
      },
      
      info(message) {
        if (this.$vuetify?.display) {
          // Vuetify 3
          this.$emit('show-snackbar', {
            message,
            color: 'info',
            timeout: 3000
          })
        } else {
          // 降级到控制台日志
          console.info('ℹ️ Info:', message)
        }
      }
    }
  }
}
