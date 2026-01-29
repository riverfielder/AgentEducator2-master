"""LLM服务模块 - 使用统一配置管理"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config.unified_llm_config import get_langchain_config


class LLMService:
    """LLM服务"""
    
    @staticmethod
    def create_chat_llm(streaming=False, callback=None):
        """创建聊天LLM实例"""
        config = get_langchain_config(
            "qa_main",
            streaming=streaming,
            callbacks=[callback] if callback else None
        )
        return ChatOpenAI(**config)
    
    @staticmethod
    def create_general_llm(streaming=False, callback=None):
        """创建通用聊天LLM实例"""
        config = get_langchain_config(
            "general_lite",
            streaming=streaming,
            callbacks=[callback] if callback else None
        )
        return ChatOpenAI(**config)
    
    @staticmethod
    def create_non_streaming_llm():
        """创建非流式LLM实例（用于问题重写）"""
        config = get_langchain_config("general", streaming=False)
        return ChatOpenAI(**config)

    @staticmethod
    def create_non_streaming_llm_lite():
        """创建非流式LLM实例（用于问题重写）"""
        config = get_langchain_config("general_lite", streaming=False)
        return ChatOpenAI(**config)

    @staticmethod
    def create_non_streaming_llm_lite_20():
        """创建非流式LLM实例（用于问题重写）"""
        config = get_langchain_config("general_lite_20", streaming=False)
        return ChatOpenAI(**config)

    def generate_response(self, prompt: str, system_message: str = None) -> str:
        """生成非流式响应"""
        try:
            llm = self.create_general_llm(streaming=False)
            
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"[ERROR] LLM response generation failed: {str(e)}")
            raise e
    
    def generate_streaming_response(self, prompt: str, callback=None, system_message: str = None) -> str:
        """生成流式响应"""
        try:
            llm = self.create_general_llm(streaming=True, callback=callback)
            
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            # 对于流式响应，我们仍然需要返回完整内容
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"[ERROR] LLM streaming response generation failed: {str(e)}")
            raise e


# 全局LLM服务实例
llm_service = LLMService()
