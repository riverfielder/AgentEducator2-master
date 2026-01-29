/**
 * 内容审核工具
 * 检测文本中是否包含不当内容
 */

// 敏感词汇列表（可根据需要扩展）
const SENSITIVE_WORDS = [
  // 脏话类
  '草泥马', '傻逼', '傻B', 'sb', 'SB', '尼玛', '你妈', '妈的', 'fuck', 'shit', 'damn',
  '死妈', '去死', '滚', '滚蛋', '混蛋', '白痴', '智障', '脑残', '废物', '垃圾', '艹', '靠', '卧槽', '我草', '我靠', '日你', '日狗', '狗屎', '狗逼',
  
  // 辱骂攻击类
  '蠢货', '蠢猪', '死猪', '猪头', '笨蛋', '弱智', '贱人', '贱货', '人渣', '败类',
  '恶心', '变态', '神经病', '有病', '找死', '活该', '该死', '去死吧',
  
  // 歧视类
  '残疾', '瞎子', '聋子', '哑巴', '瘸子', '矮子', '胖子', '丑八怪',
  
  // 政治敏感（基础版本）
  '法轮功', '六四', '天安门', '达赖', '台独', '藏独', '疆独',
  
  // 其他不当内容
  '色情', '黄色', '毒品', '吸毒', '自杀', '杀人', '爆炸', '恐怖主义'
]

// 将敏感词转换为正则表达式（忽略大小写）
const SENSITIVE_REGEX = new RegExp(
  SENSITIVE_WORDS.map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'),
  'gi'
)

/**
 * 检测文本是否包含敏感内容
 * @param text 要检测的文本
 * @returns 检测结果对象
 */
export interface ContentFilterResult {
  isValid: boolean      // 是否通过审核
  foundWords: string[]  // 发现的敏感词
  message: string       // 提示消息
}

export function checkContent(text: string): ContentFilterResult {
  if (!text || text.trim().length === 0) {
    return {
      isValid: true,
      foundWords: [],
      message: ''
    }
  }

  // 移除HTML标签和特殊字符，只检测纯文本
  const cleanText = text.replace(/<[^>]*>/g, '').replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, '')
  
  // 检测敏感词
  const matches = cleanText.match(SENSITIVE_REGEX)
  const foundWords = matches ? [...new Set(matches)] : []

  if (foundWords.length > 0) {
    return {
      isValid: false,
      foundWords,
      message: `检测到不当内容，请文明用语。发现的问题词汇：${foundWords.slice(0, 3).join(', ')}${foundWords.length > 3 ? ' 等' : ''}`
    }
  }

  return {
    isValid: true,
    foundWords: [],
    message: ''
  }
}

/**
 * 过滤敏感词汇，用*号替换
 * @param text 原文本
 * @returns 过滤后的文本
 */
export function filterContent(text: string): string {
  if (!text) return text
  
  return text.replace(SENSITIVE_REGEX, (match) => {
    return '*'.repeat(match.length)
  })
}

/**
 * 添加自定义敏感词
 * @param words 要添加的敏感词数组
 */
export function addSensitiveWords(words: string[]) {
  SENSITIVE_WORDS.push(...words)
  // 重新构建正则表达式（在实际应用中可能需要重新初始化）
} 