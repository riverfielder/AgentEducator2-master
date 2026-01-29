import apiClient, { uploadClient } from './index';

export interface QuestionData {
  id?: string;
  content: string;
  question_type: 'single' | 'multiple' | 'blank' | 'essay';
  options?: string[];
  answer: string | string[];
  explanation?: string;
  course_id: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  tags?: string[];
  remark?: string;
  keyword_ids?: string[];
}

export interface QuestionListParams {
  page?: number;
  pageSize?: number;
  course_id?: string;
  type?: string;
  difficulty?: string;
  tag?: string;
  keyword?: string;
}

export interface ImportPreviewParams {
  file: File;
  number_format?: string;
}

export interface ImportCommitParams {
  questions: QuestionData[];
  course_id: string;
}

export default {
  /**
   * 获取题库题目列表
   * @param params 查询参数
   */
  getQuestions(params: QuestionListParams = {}) {
    return apiClient.get('/api/question_bank/', { params });
  },

  /**
   * 分页获取题库题目列表
   * @param params 查询参数
   */
  getQuestionsPaginated(params: QuestionListParams = {}) {
    return apiClient.get('/api/question_bank/list', { params });
  },

  /**
   * 添加题目
   * @param questionData 题目数据
   */
  addQuestion(questionData: QuestionData) {
    return apiClient.post('/api/question_bank/', questionData);
  },

  /**
   * 更新题目
   * @param questionId 题目ID
   * @param questionData 题目数据
   */
  updateQuestion(questionId: string, questionData: QuestionData) {
    return apiClient.put(`/api/question_bank/${questionId}`, questionData);
  },

  /**
   * 删除题目
   * @param questionId 题目ID
   */
  deleteQuestion(questionId: string) {
    return apiClient.delete(`/api/question_bank/${questionId}`);
  },

  /**
   * 导入题目预览
   * @param params 导入参数
   */
  importPreview(params: ImportPreviewParams) {
    const formData = new FormData();
    formData.append('file', params.file);
    if (params.number_format) {
      formData.append('number_format', params.number_format);
    }
    return uploadClient.post('/api/question_bank/import/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 提交导入题目
   * @param params 导入参数
   */
  importCommit(params: ImportCommitParams) {
    return apiClient.post('/api/question_bank/import/commit', params);
  },
  /**
   * 批量导入题目（预留接口）
   */
  importQuestions() {
    return apiClient.post('/api/question_bank/import');
  },

  /**
   * 获取单个题目详情（学生端使用）
   * @param questionId 题目ID
   */
  getQuestionDetail(questionId: string) {
    return apiClient.get(`/api/question_bank/${questionId}/detail`);
  }
};