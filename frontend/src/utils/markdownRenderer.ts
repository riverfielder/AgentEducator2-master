// @ts-ignore
import MarkdownIt from 'markdown-it';
// @ts-ignore  
import markdownSup from 'markdown-it-sup';

// 创建实例
const md = new MarkdownIt({
  html: true,        // 启用HTML标签
  breaks: true,      // 转换'\n'为<br>
  linkify: true,     // 自动将URL转为链接
  typographer: true, // 开启一些语言中立的替换和引号
  xhtmlOut: true,    // 使用XHTML兼容的输出
})
.use(markdownSup);  // 启用上标插件

// 自定义段落渲染规则，确保段落间有适当的间距
md.renderer.rules.paragraph_open = function(tokens: any, idx: any, _options: any, env: any, self: any) {
  return '<p class="markdown-paragraph">';
};

// 自定义换行规则，确保单个换行也能正确显示
md.renderer.rules.softbreak = function(tokens: any, idx: any, options: any, env: any, self: any) {
  return '<br class="markdown-break">\n';
};

// 自定义硬换行规则
md.renderer.rules.hardbreak = function(tokens: any, idx: any, options: any, env: any, self: any) {
  return '<br class="markdown-hardbreak">\n';
};

// 自定义列表渲染，确保列表格式正确
md.renderer.rules.bullet_list_open = function(tokens: any, idx: any, _options: any, env: any, self: any) {
  return '<ul class="markdown-list">\n';
};

md.renderer.rules.ordered_list_open = function(tokens: any, idx: any, _options: any, env: any, self: any) {
  return '<ol class="markdown-list">\n';
};

// 自定义渲染规则，保护已有的引用标记 [1], [2] 等不被解析为Markdown链接
const defaultLinkOpenRender = md.renderer.rules.link_open || 
  function(tokens: any, idx: any, options: any, env: any, self: any) {
    return self.renderToken(tokens, idx, options);
  };

md.renderer.rules.link_open = function(tokens: any, idx: any, options: any, env: any, self: any) {
  const token = tokens[idx];
  const href = token.attrGet('href');
  
  // 检查是否是类似 [1] 这样的引用链接
  if (href && /^\[\d+\]$/.test(href)) {
    // 将其保留为纯文本，不渲染为链接
    return `<span class="citation-ref" data-index="${href.replace(/[\[\]]/g, '')}">${href}</span>`;
  }
  
  return defaultLinkOpenRender(tokens, idx, options, env, self);
};

// 导出渲染函数
export function renderMarkdown(content: string): string {
  if (!content) return '';
  
  // 保护引用标记 [1], [2] 等，避免被当作Markdown链接处理
  content = content.replace(/\[(\d+)\]/g, (match, index) => {
    return `<span class="citation-ref" data-index="${index}">${match}</span>`;
  });
  
  // 渲染Markdown
  return md.render(content);
}

// 处理引用标记和Markdown混合的内容
export function processContent(content: string): string {
  if (!content) return '';
  
  // 预处理：标准化换行符
  content = normalizeLineBreaks(content);
  
  // 处理可能的HTML实体字符，避免双重编码
  content = decodeHtmlEntities(content);
  
  // 第一阶段：预处理和提取引用标记，修复分割的引用
  // 步骤1：修复被分割的引用标记，例如 "[2][" 和 "3]" 会被合并为 "[2]" 和 "[3]"
  content = fixSplitCitations(content);
  
  // 步骤1.5：修复引用标记后缺失的换行
  content = fixCitationLineBreaks(content);
  
  // 步骤2：提取所有引用标记及其位置
  const citations: {index: string, start: number, end: number}[] = [];
  const citationRegex = /\[(\d+)\]/g;
  let match;
  while ((match = citationRegex.exec(content)) !== null) {
    citations.push({
      index: match[1],
      start: match.index,
      end: match.index + match[0].length
    });
  }
  
  // 步骤3：移除所有引用标记，用特殊标记代替
  let cleanContent = content;
  for (let i = citations.length - 1; i >= 0; i--) {
    const citation = citations[i];
    cleanContent = 
      cleanContent.substring(0, citation.start) + 
      `[CITATION_PLACEHOLDER_${i}]` + 
      cleanContent.substring(citation.end);
  }
  
  // 步骤4：处理换行和段落结构
  cleanContent = preprocessLineBreaks(cleanContent);
  
  // 第二阶段：渲染不包含引用标记的Markdown内容
  let rendered = md.render(cleanContent);
  
  // 第三阶段：将特殊标记替换回引用标记的HTML表示
  for (let i = 0; i < citations.length; i++) {
    const citation = citations[i];
    const placeholder = `[CITATION_PLACEHOLDER_${i}]`;
    const citationHTML = `<span class="citation-ref" data-index="${citation.index}" title="点击查看引用来源">[${citation.index}]</span>`;
    
    // 使用全局替换，确保所有占位符都被替换
    const placeholderRegex = new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
    rendered = rendered.replace(placeholderRegex, citationHTML);
  }
  
  // 第四阶段：后处理，确保格式正确
  rendered = postprocessContent(rendered);
  
  return rendered;
}

// 修复引用标记后缺失的换行
function fixCitationLineBreaks(content: string): string {
  // 在引用标记后面如果紧跟数字或字母，说明换行可能被吞掉了
  // 例如：[1]4.设计目标 应该是 [1]\n4.设计目标
  
  // 处理引用标记后紧跟数字的情况（如 [1]4.设计目标）
  content = content.replace(/\[(\d+)\](\d+\.)/g, '[$1]\n$2');
  
  // 处理引用标记后紧跟中文的情况，但要避免误处理正常的句子
  // 只有当引用标记后紧跟特定的中文模式时才添加换行
  content = content.replace(/\[(\d+)\]([一二三四五六七八九十\d]+[、\.．])/g, '[$1]\n$2');
  content = content.replace(/\[(\d+)\]([上下前后第])(?=[一二三四五六七八九十\d])/g, '[$1]\n$2');
  
  // 处理引用标记后紧跟特定知识点的情况
  const keywords = [
    '课程', '章节', '操作系统', '设计目标', '基础概念', '核心作用',
    '方便性', '有效性', '可扩充性', '开放性', '资源管理', '虚拟机',
    '裸机', '接口', '抽象', '功能', '特性', '结构', '算法', '技术'
  ];
  
  for (const keyword of keywords) {
    const regex = new RegExp(`\\[(\\d+)\\](${keyword})`, 'g');
    content = content.replace(regex, '[$1]\n$2');
  }
  
  // 处理引用标记后紧跟破折号或连字符的情况
  content = content.replace(/\[(\d+)\]([-－—])/g, '[$1]\n$2');
  
  // 处理引用标记后紧跟括号的情况（可能是新的要点）
  content = content.replace(/\[(\d+)\]([（(])/g, '[$1]\n$2');
  
  return content;
}

// 标准化换行符
function normalizeLineBreaks(content: string): string {
  // 将所有类型的换行符统一为 \n
  content = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  
  // 处理连续的换行符，保持段落结构
  // 3个或以上连续换行符视为段落分隔
  content = content.replace(/\n{3,}/g, '\n\n');
  
  return content;
}

// 预处理换行符，确保Markdown能正确解析
function preprocessLineBreaks(content: string): string {
  // 处理段落结构：确保段落之间有足够的空行
  const lines = content.split('\n');
  const processedLines: string[] = [];
  let inCodeBlock = false;
  let codeBlockType = '';
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();
    
    // 检测代码块
    if (trimmedLine.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBlockType = trimmedLine.substring(3);
      } else if (inCodeBlock && trimmedLine === '```') {
        inCodeBlock = false;
        codeBlockType = '';
      }
    }
    
    // 在代码块内部，保持原始格式
    if (inCodeBlock) {
      processedLines.push(line);
      continue;
    }
    
    // 处理普通文本行
    if (trimmedLine === '') {
      // 空行：检查是否需要添加段落分隔
      const prevLine = i > 0 ? lines[i - 1].trim() : '';
      const nextLine = i < lines.length - 1 ? lines[i + 1].trim() : '';
      
      if (prevLine && nextLine) {
        // 前后都有内容，保留空行作为段落分隔
        processedLines.push('');
      }
    } else {
      // 非空行：检查是否需要在行末添加双空格（强制换行）
      const nextLine = i < lines.length - 1 ? lines[i + 1].trim() : '';
      
      // 如果下一行不是空行且当前行不以标点符号结尾，可能需要保持换行
      if (nextLine && !nextLine.startsWith('#') && !trimmedLine.match(/[.!?。！？]$/)) {
        // 检查是否应该是同一段落的换行
        if (!trimmedLine.match(/^[-*+]|\d+\./) && !nextLine.match(/^[-*+]|\d+\./)) {
          // 不是列表项，检查是否是连续的要点或句子
          const isCurrentLineListItem = /^[-－—]\s*/.test(trimmedLine) || /^\d+[）)\.．]\s*/.test(trimmedLine);
          const isNextLineListItem = /^[-－—]\s*/.test(nextLine) || /^\d+[）)\.．]\s*/.test(nextLine);
          
          if (isCurrentLineListItem || isNextLineListItem) {
            // 列表项之间需要换行
            processedLines.push(line);
          } else {
            // 普通句子，可能是同一段落的软换行
            processedLines.push(line + '  '); // 添加双空格强制换行
          }
        } else {
          processedLines.push(line);
        }
      } else {
        processedLines.push(line);
      }
    }
  }
  
  return processedLines.join('\n');
}

// 后处理渲染结果
function postprocessContent(rendered: string): string {
  // 清理可能的重复换行
  rendered = rendered.replace(/<br\s*\/?>\s*<br\s*\/?>/g, '<br>');
  
  // 确保段落之间有适当间距
  rendered = rendered.replace(/<\/p>\s*<p>/g, '</p>\n<p>');
  
  // 处理流式生成可能导致的HTML标签分割问题
  rendered = fixBrokenTags(rendered);
  
  // 清理任何遗留的特殊标记
  rendered = cleanupSpecialMarkers(rendered);
  
  return rendered;
}

// 修复可能被分割的HTML标签
function fixBrokenTags(content: string): string {
  // 修复被分割的段落标签
  content = content.replace(/<p([^>]*)>\s*<\/p>/g, ''); // 移除空段落
  content = content.replace(/<p([^>]*)>\s*<p([^>]*)>/g, '<p$2>'); // 修复连续的开始标签
  content = content.replace(/<\/p>\s*<\/p>/g, '</p>'); // 修复连续的结束标签
  
  // 修复被分割的代码块
  content = content.replace(/<pre([^>]*)>\s*<pre([^>]*)>/g, '<pre$1>');
  content = content.replace(/<\/pre>\s*<\/pre>/g, '</pre>');
  
  // 修复被分割的列表
  content = content.replace(/<ul>\s*<\/ul>/g, '');
  content = content.replace(/<ol>\s*<\/ol>/g, '');
  content = content.replace(/<li>\s*<\/li>/g, '');
  
  return content;
}

// 清理特殊标记
function cleanupSpecialMarkers(content: string): string {
  // 清理 [$1] 格式
  content = content.replace(/\[\$(\d+)\]/g, (match: string, index: string) => {
    return `<span class="citation-ref" data-index="${index}" title="点击查看引用来源">[${index}]</span>`;
  });
  
  // 清理 CITATION_* 格式
  content = content.replace(/CITATION_(\d+)/g, (match: string, index: string) => {
    return `<span class="citation-ref" data-index="${index}" title="点击查看引用来源">[${index}]</span>`;
  });
  
  // 清理任何残留的占位符
  content = content.replace(/__SAFE_HTML_\d+__/g, '');
  content = content.replace(/\[CITATION_PLACEHOLDER_\d+\]/g, '');
  
  return content;
}

// 处理可能的HTML实体字符
function decodeHtmlEntities(content: string): string {
  const entities = {
    '&lt;': '<',
    '&gt;': '>',
    '&amp;': '&',
    '&quot;': '"',
    '&#39;': "'"
  };
  
  return content.replace(/&lt;|&gt;|&amp;|&quot;|&#39;/g, match => {
    return entities[match as keyof typeof entities];
  });
}

// 修复被分割的引用标记，例如 "[2][" 和 "3]" 合并为 "[2]" 和 "[3]"
function fixSplitCitations(content: string): string {
  // 初始清理
  // 1. 处理可能存在的 [$1] 格式，直接将其替换为 [1]
  content = content.replace(/\[\$(\d+)\]/g, '[$1]');
  
  // 2. 处理可能遗留的CITATION_*占位符
  content = content.replace(/CITATION_(\d+)/g, '[$1]');
  
  // 3. 清除任何可能残留的 __SAFE_HTML_*__ 占位符
  content = content.replace(/__SAFE_HTML_\d+__/g, '');
  
  // 4. 处理连续相邻的引用标记 
  // 例如: "[1][2][3]" 确保它们被识别为单独的引用
  content = content.replace(/\[(\d+)\]\[(\d+)\]/g, '[$1] [$2]');
  
  // 5. 使用更智能的算法处理分割的引用
  content = reconstructBrokenCitations(content);
  
  return content;
}

// 重构被分割的引用标记
function reconstructBrokenCitations(content: string): string {
  // 查找所有可能的引用片段
  const patterns = [
    /\[(\d+)(?!\])/g,  // 左半部分：[数字（没有右括号）
    /(?<!\[)(\d+)\]/g  // 右半部分：数字]（没有左括号）
  ];
  
  let result = content;
  
  // 首先标记所有完整的引用，避免误处理
  const completeRefs = [];
  const completePattern = /\[(\d+)\]/g;
  let match;
  while ((match = completePattern.exec(content)) !== null) {
    completeRefs.push({
      start: match.index,
      end: match.index + match[0].length,
      text: match[0]
    });
  }
  
  // 查找并修复分割的引用
  // 策略：在文本中查找 "数字" 后跟 "]" 且前面可能有 "[" 的模式
  const brokenPattern = /(\[?)(\d+)(\]?)/g;
  const replacements = [];
  
  while ((match = brokenPattern.exec(result)) !== null) {
    const fullMatch = match[0];
    const leftBracket = match[1];
    const digits = match[2];
    const rightBracket = match[3];
    const start = match.index;
    const end = start + fullMatch.length;
    
    // 跳过已经完整的引用
    const isComplete = completeRefs.some(ref => 
      start >= ref.start && end <= ref.end
    );
    if (isComplete) continue;
    
    // 检查是否缺少括号
    if (leftBracket && !rightBracket) {
      // 有左括号无右括号：查找附近的右括号
      const nearbyText = result.substring(end, end + 20);
      const rightBracketMatch = /^\s*\]/;
      if (rightBracketMatch.test(nearbyText)) {
        replacements.push({
          start,
          end: end + nearbyText.indexOf(']') + 1,
          replacement: `[${digits}]`
        });
      }
    } else if (!leftBracket && rightBracket) {
      // 有右括号无左括号：查找附近的左括号
      const beforeText = result.substring(Math.max(0, start - 20), start);
      const leftBracketMatch = /\[\s*$/;
      if (leftBracketMatch.test(beforeText)) {
        const leftStart = start - (beforeText.length - beforeText.lastIndexOf('['));
        replacements.push({
          start: leftStart,
          end,
          replacement: `[${digits}]`
        });
      }
    } else if (!leftBracket && !rightBracket) {
      // 两个括号都没有：检查前后是否有分离的括号
      const beforeText = result.substring(Math.max(0, start - 10), start);
      const afterText = result.substring(end, end + 10);
      
      const hasLeftBracket = /\[\s*$/.test(beforeText);
      const hasRightBracket = /^\s*\]/.test(afterText);
      
      if (hasLeftBracket && hasRightBracket) {
        const leftStart = start - (beforeText.length - beforeText.lastIndexOf('['));
        const rightEnd = end + afterText.indexOf(']') + 1;
        replacements.push({
          start: leftStart,
          end: rightEnd,
          replacement: `[${digits}]`
        });
      }
    }
  }
  
  // 从后往前应用替换，避免位置偏移
  replacements.sort((a, b) => b.start - a.start);
  for (const replacement of replacements) {
    result = result.substring(0, replacement.start) + 
             replacement.replacement + 
             result.substring(replacement.end);
  }
  
  return result;
}
