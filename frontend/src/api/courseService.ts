import apiClient from './index';

export default {
  /**
   * 获取课程列表
   * @param params 查询参数
   */
  getCourses(params = {}) {
    return apiClient.get('/api/courses/list', { params });
  },

  /**
   * 获取全平台课程列表（用于题库等功能的筛选）
   * @param params 查询参数
   */
  getAllCourses(params = {}) {
    return apiClient.get('/api/courses/all', { params });
  },

  /**
   * 获取课程详情
   * @param courseId 课程ID
   */
  getCourseDetails(courseId: string) {
    return apiClient.get(`/api/courses/detail/${courseId}`);
  },

  /**
   * 获取包含章节结构的课程详情
   * @param courseId 课程ID
   */
  getCourseDetailsWithChapters(courseId: string) {
    return apiClient.get(`/api/courses/detail-with-chapters/${courseId}`);
  },

  /**
   * 创建新课程
   * @param courseData 课程数据
   */
  createCourse(courseData: any) {
    return apiClient.post('/api/courses/add', courseData);
  },

  /**
   * 更新课程信息
   * @param courseId 课程ID
   * @param courseData 课程数据
   */
  updateCourse(courseId: string, courseData: any) {
    return apiClient.put(`/api/courses/edit/${courseId}`, courseData);
  },

  /**
   * 删除课程
   * @param courseId 课程ID
   */
  deleteCourse(courseId: string) {
    return apiClient.delete(`/api/courses/delete/${courseId}`);
  },
  /**
   * 获取课程统计数据
   */
  getCourseStats() {
    return apiClient.get('/api/courses/stats');
  },

  /**
   * 获取教师统计数据总览
   * @param params 查询参数 { course_id, time_period }
   */
  getStatisticsOverview(params = {}) {
    return apiClient.get('/api/statistics/overview', { params });
  },
  /**
   * 获取教师课程列表
   */
  getTeacherCourses() {
    return apiClient.get('/api/statistics/courses');
  },

  /**
   * 获取教师主页数据
   * 包含：教师信息、统计数据、课程进度、最近活动
   */
  getTeacherHomeData() {
    return apiClient.get('/api/statistics/teacher-home');
  },
  
  /**
   * 获取学生可访问的课程列表
   * @param params 查询参数
   */
  getStudentCourses(params = {}) {
    return apiClient.get('/api/students/courses', { params }); // 这里需要从'/api/student/courses'修改为'/api/students/courses'
  },
  
  /**
   * 获取推荐课程
   */
  getRecommendedCourses() {
    return apiClient.get('/api/students/recommended-courses'); // 这里需要从'/api/student/recommended-courses'修改
  },
  
  /**
   * 获取首页数据
   * 包含：大家都在学、继续学习、从上次中断的地方继续
   */
  getHomepageData() {
    return apiClient.get('/api/students/homepage-data');
  },

  /**
   * 获取学习进度数据
   * 包含：在学课程数、学习时长、已获证书、平均评分、课程进度列表
   */
  getLearningProgress() {
    return apiClient.get('/api/students/learning-progress');
  },

  /**
   * 获取课程下所有视频
   * @param courseId 课程ID
   */
  getCourseVideos(courseId: string) {
    return apiClient.get(`/api/courses/${courseId}/videos`);
  },
  
  /**
   * 获取课程知识点掌握情况
   * @param courseId 课程ID
   */
  getCourseKnowledgeMastery(courseId: string) {
    return apiClient.get(`/api/statistics/knowledge-mastery/${courseId}`);
  },
  
};
