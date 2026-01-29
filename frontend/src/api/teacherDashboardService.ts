import apiClient from './index';

/**
 * 教师仪表板服务 - 处理教师相关的API请求
 */
class TeacherDashboardService {
  /**
   * 获取课程日程数据
   * @param {Object} params 查询参数
   * @param {string} params.start_date 开始日期
   * @param {string} params.end_date 结束日期
   * @param {string} params.view_type 视图类型（month, week, day）
   * @returns {Promise} 返回API响应
   */
  getSchedule(params = {}) {
    return apiClient.get('/api/teacher/schedule', {
      headers: this._getAuthHeader(),
      params: params
    });
  }

  /**
   * 获取教师消息列表
   * @param {Object} params 查询参数
   * @param {number} params.page 页码
   * @param {number} params.pageSize 每页数量
   * @param {string} params.status 消息状态筛选
   * @param {string} params.course_id 课程ID筛选
   * @param {string} params.keyword 知识点搜索
   * @returns {Promise} 返回API响应
   */
  getMessages(params = {}) {
    return apiClient.get('/api/teacher/messages', {
      headers: this._getAuthHeader(),
      params: params
    });
  }

  /**
   * 回复学生消息
   * @param {string} commentId 评论ID
   * @param {string} content 回复内容
   * @returns {Promise} 返回API响应
   */
  replyToMessage(commentId:string, content:string) {
    return apiClient.post(`/api/teacher/messages/${commentId}/reply`, 
      { content },
      { headers: this._getAuthHeader() }
    );
  }

  /**
   * 获取课程列表（用于筛选）
   * @returns {Promise} 返回API响应
   */
  getCourses() {
    return apiClient.get('/api/teacher/courses', {
      headers: this._getAuthHeader()
    });
  }
  /**
   * 获取教师主页数据
   * @returns {Promise} 返回API响应
   */
  getTeacherHomeData() {
    return apiClient.get('/api/statistics/teacher-home', {
      headers: this._getAuthHeader()
    });
  }

  /**
   * 获取认证头信息
   * @returns {Object} 包含Authorization的头信息对象
   * @private
   */
  _getAuthHeader() {
    const token = localStorage.getItem('wendao_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
}

export default new TeacherDashboardService();
