"""回调处理器模块"""
import json
from langchain_core.callbacks import BaseCallbackHandler


class CustomStreamingCallback(BaseCallbackHandler):
    """RAG模式自定义流式回调处理器"""
    
    def __init__(self, queue):
        self.queue = queue
        self.token_count = 0
        self.answer_content = ""
        self.token_buffer = ""  # 用于缓冲token以处理Markdown序号
        
    def on_llm_new_token(self, token, **kwargs):
        self.answer_content += token
        self.token_count += 1
        
        # 临时禁用智能缓冲，直接输出token以避免数字丢失问题
        # TODO: 后续可以优化为更智能的缓冲机制
        self.queue.put(token)
    
    def _process_token_with_buffer(self, token):
        """智能缓冲处理token，确保Markdown序号不被分割"""
        self.token_buffer += token
        
        # 检查是否可以释放缓冲区的内容
        if self._should_flush_buffer():
            # 释放整个缓冲区
            self.queue.put(self.token_buffer)
            self.token_buffer = ""
        elif len(self.token_buffer) > 100:  # 防止缓冲区过大，增加阈值
            # 如果缓冲区太大，采用更保守的策略
            # 只有在确认不会破坏数字的情况下才进行截断
            safe_point = self._find_safe_truncation_point()
            if safe_point > 0:
                self.queue.put(self.token_buffer[:safe_point])
                self.token_buffer = self.token_buffer[safe_point:]
            else:
                # 如果找不到安全截断点，直接输出所有内容
                self.queue.put(self.token_buffer)
                self.token_buffer = ""
    
    def _should_flush_buffer(self):
        """判断是否应该释放缓冲区 - 简化版本"""
        if not self.token_buffer:
            return False
        
        # 如果缓冲区以完整的句子结尾，可以释放
        if self.token_buffer.endswith(('\n', '。', '！', '？', '.', '!', '?')):
            return True
        
        # 如果缓冲区以空格结尾且不包含未完成的数字序号，可以释放
        if self.token_buffer.endswith(' ') and not self._has_incomplete_number_sequence():
            return True
            
        return False
    
    def _has_incomplete_number_sequence(self):
        """检查是否有未完成的数字序列"""
        import re
        # 检查缓冲区末尾是否有可能未完成的序号（如 "3"、"3."、"3）" 等）
        # 但要避免误判正常的数字（如 "8名学生"）
        buffer_end = self.token_buffer[-10:].strip()  # 只检查最后10个字符
        
        # 如果以纯数字结尾，可能是未完成的序号，但也可能是正常数字
        if re.search(r'\d+$', buffer_end):
            # 进一步检查上下文，如果前面有中文则可能是正常数字
            before_number = self.token_buffer[:-10] if len(self.token_buffer) > 10 else ""
            if re.search(r'[一-龟]', before_number[-5:]):  # 前面有中文字符
                return False  # 可能是 "8名学生" 这样的正常数字
            return True  # 可能是序号开始
            
        # 如果以 "数字." 或 "数字）" 结尾，可能是未完成的序号
        if re.search(r'\d+[.）)]\s*$', buffer_end):
            return True
            
        return False
    
    def send_tool_event(self, tool_event_token):
        """直接发送工具事件，绕过token缓存机制"""
        self.queue.put(tool_event_token)
    
    def flush_remaining_buffer(self):
        """强制释放剩余的缓冲区内容（在流结束时调用）"""
        if self.token_buffer:
            self.queue.put(self.token_buffer)
            self.token_buffer = ""
    
    def _find_safe_truncation_point(self):
        """查找安全的截断点，确保不会破坏数字或重要内容"""
        buffer = self.token_buffer
        
        # 从后往前找安全的截断点
        for i in range(len(buffer) - 20, 0, -1):  # 保留最后20个字符
            char = buffer[i]
            
            # 在空格、标点符号后截断是安全的
            if char in [' ', '\n', '\t', '。', '！', '？', '.', '!', '?', '，', ',', '；', ';']:
                return i + 1
                
            # 在中文字符后截断通常是安全的（但要避免在数字后）
            if ord(char) > 127 and not buffer[i-1:i+2].strip().isdigit():
                return i + 1
        
        return 0  # 找不到安全点，返回0表示不截断


class StatusNotifier:
    """状态通知器，用于发送处理状态消息"""
    
    def __init__(self, queue):
        self.queue = queue
    
    def notify_analysis_start(self):
        """通知分析开始"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "analysis_start", 
            "message": "分析问题中..."
        }))
    
    def notify_generation_start(self):
        """通知生成开始"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "generation_start",
            "message": "开始生成回答..."
        }))
    
    def notify_retrieval_start(self):
        """通知检索开始"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "retrieval_start",
            "message": "检索相关资料..."
        }))
    
    def notify_retrieval_complete(self, doc_count=0):
        """通知检索完成"""
        index_info = f"已加载 {doc_count} 个文档片段" if doc_count > 0 else ""
        self.queue.put(json.dumps({
            "type": "status", 
            "stage": "retrieval_complete",
            "message": f"检索完成 {index_info}",
            "stats": {"document_count": doc_count}
        }))
    
    def notify_question_analysis(self):
        """通知问题分析"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "question_analysis", 
            "message": "思考中..."
        }))
