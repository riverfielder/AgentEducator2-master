import request from './index';

export interface Assignment {
  id?: string;
  title: string;
  teacherId: string;
  courseId: string;
  dueDate: string;
  publishTime: string;
  status: 'draft' | 'published';
  teacherStatus?: 'draft' | 'scheduled' | 'published'; // 教师端显示状态
  questions: {
    type: 'single' | 'multiple' | 'blank' | 'essay';
    content: string;
    maxScore: number;
    options?: any[];
    answers?: string;
    reference?: string;
    explanation?: string;
    courseId?: string;
  }[];
  raw?: any;
}

//学生提交作业的接口类型定义
export interface StudentSubmission {
  student_id: string;
  assignment_id: string;
  questions_and_answers: Array<{
    question_id: string;
    question_type: 'single' | 'multiple' | 'blank' | 'essay';
    student_answer: string  // 根据题目类型可能是不同类型
  }>;
  submit_time: string;
}

const assignmentService = {
  // AI批改答案
  gradeAnswer(data: {
    // 兼容新旧两种调用方式
    question?: string;
    standard_answer?: string;
    student_answer: string;
    max_score?: number;
    grading_criteria?: string;
    question_id?: string;
  }) {
    return request({
      url: '/api/assignments/grade-answer',
      method: 'POST',
      data
    });
  },
  // 获取作业列表
  getAssignmentList(params?: {
    courseId?: string;
    status?: string;
    page?: number;
    pageSize?: number;
  }) {
    return request({
      url: '/api/assignments',
      method: 'GET',
      params
    });
  },

  // 获取作业详情
  getAssignmentDetail(id: string) {
    return request({
      url: `/api/assignments/${id}`,
      method: 'GET'
    });
  },

  // 创建作业草稿
  createDraft(data: Omit<Assignment, 'id' | 'status'>) {
    return request({
      url: '/api/assignments/draft',
      method: 'POST',
      data: {
        ...data,
        status: 'draft'
      }
    });
  },

  // 发布作业
  publishAssignment(data: Omit<Assignment, 'id' | 'status'>) {
    return request({
      url: '/api/assignments',
      method: 'POST',
      data: {
        ...data,
        status: 'published'
      }
    });
  },

  // 更新作业
  updateAssignment(id: string, data: Partial<Assignment>) {
    return request({
      url: `/api/assignments/${id}`,
      method: 'PUT',
      data
    });
  },

  // 删除作业
  deleteAssignment(id: string) {
    return request({
      url: `/api/assignments/${id}`,
      method: 'DELETE'
    });
  },

  getStudentAssignments: () => request.get('/api/assignments/student/list'),
  getStudentAssignmentDetail: (id: string) => request.get(`/api/assignments/student/detail?id=${id}`),

  // 修改：学生提交作业的接口
  submitStudentAssignment: (data: StudentSubmission) => {
    return request({
      url: '/api/assignments/student/submit',
      method: 'POST',
      data
    });
  },

  // 学生获取作业批改信息
  getAssignmentMarkingInfo: (assignmentId: string) => {
    return request({
      url: `/api/assignments/${assignmentId}/marking`,
      method: 'get'
    });
  },

  // 教师获取学生作业提交列表
  getStudentSubmissions: (submissionId: string) => {
    return request({
      url: `/api/assignments/${submissionId}/submissions`,
      method: 'get'
    });
  },

  // 保存批改进度
  saveMarkingProgress: (assignmentId: string, data: any) => {
    return request({
      url: `api/assignments/${assignmentId}/marking/save`,
      method: 'post',
      data
    });
  },

  // 提交批改结果
  submitMarking: (assignmentId: string, data: any) => {
    return request({
      url: `api/assignments/${assignmentId}/marking/submit`,
      method: 'post',
      data
    });
  },

  // 导出成绩
  exportGrades: (assignmentId: string) => {
    return request({
      url: `api/assignments/${assignmentId}/grades/export`,
      method: 'get',
      responseType: 'blob'
    });
  },
  // 智能批改
  aiGrading: (assignmentId: string, data: any) => {
    return request({
      url: `api/assignments/${assignmentId}/ai-grading`,
      method: 'post',
      data
    });
  },

  // 自动批改选择题
  autoGradeChoices: (assignmentId: string) => {
    return request({
      url: `/api/assignments/${assignmentId}/auto-grade-choices`,
      method: 'post'
    });
  },

  // 批改单个选择题
  gradeChoiceQuestion: (data: {
    question_type: string;
    options: any[];
    student_answer: any;
    max_score?: number;
  }) => {
    return request({
      url: '/api/assignments/grade-choice-question',
      method: 'post',
      data
    });
  },

  // 批改填空题
  gradeFillBlankQuestion: (data: {
    question?: string;
    standard_answer?: string;
    student_answer: string;
    max_score?: number;
    grading_criteria?: string;
    question_id?: string;
  }) => {
    return request({
      url: '/api/assignments/grade-fill-blank-question',
      method: 'post',
      data
    });
  },
  // 获取题目提取的知识点
  getExtractedKeywords: (questionId: string) => {
    return request({
      url: `/api/assignments/question/${questionId}/extract-keywords/result`,
      method: 'get'
    });
  },
};

export default assignmentService;