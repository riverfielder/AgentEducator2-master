import apiClient from './index';

export default {
  /**
   * 获取视频处理任务列表
   * @param params 查询参数
   */
  getTasksList(params = {}) {
    return apiClient.get('/api/task_logs/list', { params });
  },

  /**
   * 获取特定任务的日志
   * @param taskId 任务ID
   */
  getTaskLogs(taskId: string) {
    return apiClient.get(`/api/task_logs/logs/${taskId}`);
  },

  /**
   * 获取特定任务的信息
   * @param taskId 任务ID
   */
  getTaskInfo(taskId: string) {
    return apiClient.get(`/api/task_logs/task/${taskId}`);
  },

  /**
   * 删除任务及其日志
   * 如果任务正在运行，会尝试终止进程
   * @param taskId 任务ID
   */
  deleteTask(taskId: string) {
    return apiClient.delete(`/api/task_logs/task/${taskId}`);
  }
};
