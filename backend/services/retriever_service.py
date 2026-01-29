"""检索器服务模块"""
import jieba
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from config.qa_config import LLMConfig
from services.tokenization_cache_service import tokenization_cache_service


class RetrieverService:
    """检索器服务"""
    
    @staticmethod
    def tokenize_chinese(text,cache_key=""):
        """使用jieba进行中文分词（带缓存）"""
        if not text:
            return []
        # 使用缓存服务进行分词
        return tokenization_cache_service.get_or_create_tokens(text, 'retrieval',cache_key)

    
    @staticmethod
    def create_ensemble_retriever(index,cache_key=""):
        """创建混合检索器：结合知识点匹配和语义检索"""
        # 获取所有文档用于BM25
        all_docs = []
        for i in range(index.index.ntotal):
            try:
                # 从FAISS索引中获取文档
                doc_id = index.index_to_docstore_id[i]
                doc = index.docstore.search(doc_id)
                if doc:
                    all_docs.append(doc)
            except:
                continue
        
        # 创建BM25检索器（适合知识点匹配）
        # 使用jieba分词来改进中文文本处理
        bm25_retriever = BM25Retriever.from_documents(
            all_docs, 
            k=LLMConfig.BM25_K,
            preprocess_func=lambda text: RetrieverService.tokenize_chinese(text, cache_key)
        )
        
        # 创建语义检索器（适合语义理解）
        semantic_retriever = index.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": LLMConfig.SEMANTIC_K, 
                "score_threshold": LLMConfig.SEMANTIC_SCORE_THRESHOLD,
                "fetch_k": LLMConfig.SEMANTIC_FETCH_K
            }
        )
        
        # 混合检索器：结合知识点匹配和语义检索
        retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, semantic_retriever],
            weights=LLMConfig.ENSEMBLE_WEIGHTS,
            k=LLMConfig.ENSEMBLE_K
        )
        
        return retriever


# 全局检索器服务实例
retriever_service = RetrieverService()
