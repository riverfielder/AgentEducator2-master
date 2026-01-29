import apiClient from './index';

/**
 * 获取所有课程分类
 */
export function getCategories() {
  return apiClient.get<string[]>('/api/category/list');
}

export default {
  getCategories,
  getCategoryList() {
    // Use the correct API endpoint
    return apiClient.get('/api/category/list');
  }
}
