import apiClient from './index';

interface StudentData {
  name: string;
  email: string;
  courseId: string;
}

interface StudentImportData {
  name: string;
  email: string;
  courseId: string;
  courseName: string;
}

export default {
  /**
   * 获取学生列表
   * @param params 查询参数 (page, size, keyword, class等)
   */
  getStudents(params: Record<string, any> = {}) {
    return apiClient.get('/api/student_management/list', { params });
  },

  /**
   * 获取学生详情
   * @param studentId 学生ID
   */
  getStudentDetails(studentId: string) {
    return apiClient.get(`/api/student_management/${studentId}`);
  },

  /**
   * 添加学生到指定课程
   * @param studentData 学生数据 {name, email, courseId}
   */
  addStudent(studentData: StudentData) {
    return apiClient.post('/api/student_management/add', studentData);
  },

  /**
   * 更新学生信息
   * @param studentId 学生ID
   * @param studentData 学生数据
   */
  updateStudent(studentId: string, studentData: Record<string, any>) {
    return apiClient.put(`/api/student_management/${studentId}`, studentData);
  },

  /**
   * 删除学生
   * @param studentId 学生ID
   */
  deleteStudent(studentId: string) {
    return apiClient.delete(`/api/student_management/${studentId}`);
  },

  /**
   * 获取学生选修的课程
   * @param studentId 学生ID
   */
  getStudentCourses(studentId: string) {
    return apiClient.get(`/api/student_management/${studentId}/courses`);
  },

  /**
   * 为学生分配课程
   * @param studentId 学生ID
   * @param courseIds 课程ID数组
   */
  assignCourses(studentId: string, courseIds: string[]) {
    return apiClient.post(`/api/student_management/${studentId}/assign-courses`, { courseIds });
  },

  /**
   * 获取班级列表
   */
  getClassList() {
    return apiClient.get('/api/student_management/classes');
  },

  /**
   * 获取可选择的课程列表
   */
  getAvailableCourses() {
    return apiClient.get('/api/student_management/available-courses');
  },

  /**
   * 上传学生名单文件(Excel/CSV)
   * @param formData 包含文件的FormData对象
   */
  uploadStudentList(formData: FormData) {
    return apiClient.post('/api/student_management/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 批量导入学生到课程
   * @param data 包含学生数据数组的对象 { students: [{name, email, courseId, courseName}] }
   */
  importStudents(data: { students: StudentImportData[] }) {
    return apiClient.post('/api/student_management/import', data);
  },

  /**
   * 重置学生密码
   * @param studentId 学生ID
   */
  resetPassword(studentId: string) {
    return apiClient.post(`/api/student_management/${studentId}/reset-password`);
  }
};