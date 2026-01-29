import apiClient from './index';

export default {
  /**
   * 用户登录
   * @param email 邮箱
   * @param password 密码
   */
  login(email: string, password: string) {
    return apiClient.post('/api/auth/login', { email, password });
  },

  /**
   * 用户注册
   * @param userData 用户注册数据
   */
  register(userData: any) {
    return apiClient.post('/api/auth/register', userData);
  },

  /**
   * 获取当前用户信息
   */
  getUserInfo() {
    return apiClient.get('/api/auth/user/info');
  },

  /**
   * 修改密码
   * @param oldPassword 旧密码
   * @param newPassword 新密码
   */
  changePassword(oldPassword: string, newPassword: string) {
    return apiClient.post('/api/auth/change-password', {
      oldPassword,
      newPassword
    });
  },

  /**
   * 更新用户资料
   * @param userData 用户资料数据
   */
  updateUserProfile(userData: any) {
    return apiClient.post('/api/auth/update-profile', userData);
  },

  /**
   * 退出登录
   */
  logout() {
    return apiClient.post('/api/auth/logout');
  },

  /**
   * 根据用户ID获取用户信息
   * @param userId 用户ID
   */
  getUserById(userId: string) {
    return apiClient.get(`/api/auth/user/${userId}`);
  }
};
