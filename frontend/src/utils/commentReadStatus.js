/**
 * 评论已读状态管理工具
 * 用于在本地存储中管理已读评论ID
 */

const STORAGE_KEY = 'wendao_read_comments';

/**
 * 获取已读评论ID列表
 * @returns {Array} 已读评论ID数组
 */
function getReadCommentIds() {
  try {
    const storedIds = localStorage.getItem(STORAGE_KEY);
    return storedIds ? JSON.parse(storedIds) : [];
  } catch (error) {
    console.error('获取已读评论失败:', error);
    return [];
  }
}

/**
 * 标记评论为已读
 * @param {string} commentId 评论ID
 */
function markCommentAsRead(commentId) {
  try {
    const readIds = getReadCommentIds();
    if (!readIds.includes(commentId)) {
      readIds.push(commentId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(readIds));
    }
  } catch (error) {
    console.error('标记评论已读失败:', error);
  }
}

/**
 * 标记多个评论为已读
 * @param {Array} commentIds 评论ID数组
 */
function markCommentsAsRead(commentIds) {
  try {
    if (!Array.isArray(commentIds) || commentIds.length === 0) return;
    
    let readIds = getReadCommentIds();
    let hasNewIds = false;
    
    commentIds.forEach(id => {
      if (!readIds.includes(id)) {
        readIds.push(id);
        hasNewIds = true;
      }
    });
    
    if (hasNewIds) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(readIds));
    }
  } catch (error) {
    console.error('批量标记评论已读失败:', error);
  }
}

/**
 * 检查评论是否已读
 * @param {string} commentId 评论ID
 * @returns {boolean} 是否已读
 */
function isCommentRead(commentId) {
  const readIds = getReadCommentIds();
  return readIds.includes(commentId);
}

/**
 * 清除过期的已读评论记录
 * @param {number} days 保留的天数，默认为30天
 */
function clearOldReadComments(days = 30) {
  try {
    // 此处可以添加过期清理逻辑
    // 如果评论系统包含时间戳，可以清除超过一定时间的记录
  } catch (error) {
    console.error('清除过期评论记录失败:', error);
  }
}

export default {
  getReadCommentIds,
  markCommentAsRead,
  markCommentsAsRead, 
  isCommentRead,
  clearOldReadComments
};
