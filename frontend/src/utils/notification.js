/**
 * 全局消息通知辅助函数
 */

/**
 * 显示消息通知
 * @param {Object|string} config 配置或消息文本
 */
export function showSnackbar(config) {
  // 使用自定义事件触发全局消息通知
  const event = new CustomEvent('show-snackbar', {
    detail: config
  });
  window.dispatchEvent(event);
}

/**
 * 显示成功消息
 * @param {string} message 消息文本
 * @param {number} timeout 显示时间，单位毫秒
 */
export function showSuccessMessage(message, timeout = 3000) {
  showSnackbar({
    message,
    color: 'success',
    timeout
  });
}

/**
 * 显示错误消息
 * @param {string} message 消息文本
 * @param {number} timeout 显示时间，单位毫秒
 */
export function showErrorMessage(message, timeout = 5000) {
  showSnackbar({
    message,
    color: 'error',
    timeout
  });
}

/**
 * 显示警告消息
 * @param {string} message 消息文本
 * @param {number} timeout 显示时间，单位毫秒
 */
export function showWarningMessage(message, timeout = 4000) {
  showSnackbar({
    message,
    color: 'warning',
    timeout
  });
}

/**
 * 显示信息消息
 * @param {string} message 消息文本
 * @param {number} timeout 显示时间，单位毫秒
 */
export function showInfoMessage(message, timeout = 3000) {
  showSnackbar({
    message,
    color: 'info',
    timeout
  });
}

export default {
  showSnackbar,
  showSuccessMessage,
  showErrorMessage,
  showWarningMessage,
  showInfoMessage
};
