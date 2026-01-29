/**
 * 全局消息提示工具
 * 用于在应用程序中显示消息通知
 */

/**
 * 显示消息通知
 * @param {Object|string} config 配置对象或消息文本
 * @param {string} config.message 消息文本
 * @param {string} config.color 消息颜色 (success, error, info, warning)
 * @param {number} config.timeout 消息显示时长(毫秒)
 */
function showSnackbar(config) {
  // 创建自定义事件
  const event = new CustomEvent('show-snackbar', { 
    detail: typeof config === 'string' ? { message: config } : config 
  });
  
  // 触发事件
  window.dispatchEvent(event);
}

// 便捷方法
const message = {
  /**
   * 显示成功消息
   * @param {string} text 消息内容
   * @param {number} timeout 显示时长(毫秒)
   */
  success(text, timeout = 3000) {
    showSnackbar({
      message: text,
      color: 'success',
      timeout: timeout
    });
  },
  
  /**
   * 显示错误消息
   * @param {string} text 消息内容
   * @param {number} timeout 显示时长(毫秒)
   */
  error(text, timeout = 5000) {
    showSnackbar({
      message: text,
      color: 'error',
      timeout: timeout
    });
  },
  
  /**
   * 显示警告消息
   * @param {string} text 消息内容
   * @param {number} timeout 显示时长(毫秒)
   */
  warning(text, timeout = 4000) {
    showSnackbar({
      message: text,
      color: 'warning',
      timeout: timeout
    });
  },
  
  /**
   * 显示信息消息
   * @param {string} text 消息内容
   * @param {number} timeout 显示时长(毫秒)
   */
  info(text, timeout = 3000) {
    showSnackbar({
      message: text,
      color: 'info',
      timeout: timeout
    });
  }
}

export default message;
