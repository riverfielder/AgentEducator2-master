"""内存管理服务模块"""
from langchain.memory.buffer import ConversationBufferMemory
from config.qa_config import LLMConfig


class MemoryService:
    """内存管理服务"""
    
    @staticmethod
    def create_memory_from_history(history):
        """从历史消息创建内存对象（优化版）"""
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="result"
        )
        
        if history:
            from langchain_core.messages import HumanMessage, AIMessage
            # 限制历史消息数量，避免内存过大
            recent_history = history[-LLMConfig.MAX_HISTORY_LENGTH:] if len(history) > LLMConfig.MAX_HISTORY_LENGTH else history
            
            for msg in recent_history:
                role = msg.get('role')
                content = msg.get('content')
                if role == 'user':
                    memory.chat_memory.add_user_message(content)
                elif role == 'assistant':
                    memory.chat_memory.add_ai_message(content)
        
        return memory
    
    @staticmethod
    def format_chat_history(history):
        """格式化聊天历史为字符串"""
        chat_history = ""
        if history:
            recent_history = history[-LLMConfig.RECENT_HISTORY_LENGTH:]  # 只取最近几条
            for msg in recent_history:
                role = "用户" if msg.get('role') == 'user' else "助手"
                content = msg.get('content', '')
                chat_history += f"{role}: {content}\n"
        return chat_history


# 全局内存服务实例
memory_service = MemoryService()
