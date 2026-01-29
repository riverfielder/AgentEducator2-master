/**
 * Course相关的工具函数
 */

/**
 * 课程描述数据接口
 */
export interface CourseDescriptionData {
  description: string;
  category: string[];
}

/**
 * 自适应解析课程描述字段
 * @param description - 课程描述字段，可能是JSON字符串或纯文本
 * @returns 解析后的描述数据对象
 */
export function parseCourseDescription(description: string | null | undefined): CourseDescriptionData {
  // 处理空值情况
  if (!description) {
    return {
      description: '',
      category: []
    };
  }

  // 尝试解析为JSON
  try {
    const parsed = JSON.parse(description);
    
    // 验证解析结果是否为对象且包含预期字段
    if (typeof parsed === 'object' && parsed !== null) {
      return {
        description: parsed.description || '',
        category: Array.isArray(parsed.category) ? parsed.category : []
      };
    } else {
      // 如果解析结果不是对象，当作纯文本处理
      return {
        description: description,
        category: []
      };
    }
  } catch {
    // JSON解析失败，当作纯文本处理
    return {
      description: description,
      category: []
    };
  }
}

/**
 * 将课程描述数据转换为JSON字符串
 * @param data - 课程描述数据对象
 * @returns JSON字符串
 */
export function stringifyCourseDescription(data: CourseDescriptionData): string {
  return JSON.stringify({
    description: data.description || '',
    category: data.category || []
  });
}

/**
 * 从课程对象中提取描述信息
 * @param course - 课程对象
 * @returns 解析后的描述数据
 */
export function extractCourseDescription(course: any): CourseDescriptionData {
  return parseCourseDescription(course?.description);
}