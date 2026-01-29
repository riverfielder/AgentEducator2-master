"""
文档向量索引模块
负责构建和管理文档分段的向量索引
参照视频向量化逻辑实现
"""

import os
from flask import current_app
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 导入数据库模型
from models.models import db, DocumentVectorIndex, DocumentSegment

# 配置信息
DOCUMENT_VECTOR_INDEX_DIR = "vector_indices"

def build_document_vector_index(document_id, segments_data, index_path, api_key=None, base_url=None, model='Pro/BAAI/bge-m3'):
    """
    构建文档分段的向量索引
    
    参数:
        document_id: 文档ID
        segments_data: 文档分段数据列表
        index_path: 索引保存路径
        api_key: API密钥，默认为None，将使用环境变量中的API_KEY
        base_url: API基础URL，默认为None，将使用环境变量中的SILICON_API_BASE
        model: 嵌入模型名称，默认为'Pro/BAAI/bge-m3'
        
    返回:
        bool: 索引构建是否成功
    """
    try:
        # 获取API配置
        if api_key is None:
            from config.config import Config
            api_key = Config.get_openai_api_key()
        if base_url is None:
            from config.config import Config
            base_url = Config.get_silicon_api_base()
        
        current_app.logger.info(f"开始构建文档 {document_id} 的向量索引，使用模型: {model}")
        
        # 初始化embeddings
        embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            base_url=base_url,
            model=model,
            chunk_size=32  # 设置块大小以避免批量限制
        )
        
        # 准备文档和元数据
        docs = []
        metadatas = []
        
        for segment in segments_data:
            # 获取分段内容
            content = segment.get("content", "").strip()
            
            if content:
                # 为向量化准备内容，添加标题信息（如果有）
                title = segment.get("title", "")
                segment_type = segment.get("segment_type", "paragraph")
                
                # 构建用于向量化的文本
                if title:
                    vectorize_text = f"标题：{title}\n内容：{content}"
                else:
                    vectorize_text = content
                
                docs.append(vectorize_text)
                metadatas.append({
                    "document_id": str(document_id),
                    "segment_id": segment.get("id", ""),
                    "segment_number": segment.get("segment_number", 0),
                    "segment_type": segment_type,
                    "title": title,
                    "page_number": segment.get("page_number", None)
                })
        
        # 分批处理，避免内存问题
        # 设置更保守的批量大小以避免API限制
        MAX_BATCH_SIZE = 32
        
        # 构建索引
        if not docs:
            current_app.logger.warning(f"文档 {document_id} 没有可索引的分段内容")
            return False
        
        current_app.logger.info(f"准备向量化 {len(docs)} 个文档分段")
        
        index = None
        for i in range(0, len(docs), MAX_BATCH_SIZE):
            batch_docs = docs[i:i + MAX_BATCH_SIZE]
            batch_metadatas = metadatas[i:i + MAX_BATCH_SIZE]
            
            current_app.logger.info(f"处理批次 {i//MAX_BATCH_SIZE + 1}，包含 {len(batch_docs)} 个分段")
            
            try:
                if index is None:
                    index = FAISS.from_texts(
                        texts=batch_docs,
                        embedding=embeddings,
                        metadatas=batch_metadatas
                    )
                    current_app.logger.info(f"创建初始向量索引，包含 {len(batch_docs)} 个文档")
                else:
                    batch_index = FAISS.from_texts(
                        texts=batch_docs,
                        embedding=embeddings,
                        metadatas=batch_metadatas
                    )
                    index.merge_from(batch_index)
                    current_app.logger.info(f"合并批次索引，包含 {len(batch_docs)} 个文档")
            except Exception as batch_error:
                current_app.logger.error(f"批次 {i//MAX_BATCH_SIZE + 1} 处理失败: {str(batch_error)}")
                current_app.logger.error(f"批次详情: 文档数量={len(batch_docs)}, 元数据数量={len(batch_metadatas)}")
                raise batch_error
        
        # 创建索引目录
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # 保存索引
        index.save_local(index_path)
        
        current_app.logger.info(f"文档向量索引构建成功，保存到: {index_path}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"构建文档向量索引失败: {str(e)}")
        import traceback
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def check_document_vector_index_exists(document_id):
    """
    检查文档向量索引是否存在
    
    参数:
        document_id: 文档ID
        
    返回:
        (exists, index_path): 布尔值表示是否存在，若存在则返回索引路径
    """
    try:
        # 查询数据库中的向量索引记录
        vector_index = DocumentVectorIndex.query.filter_by(document_id=document_id).first()
        
        if not vector_index:
            return False, None
            
        index_path = vector_index.index_path
        
        # 检查文件是否实际存在
        if not os.path.exists(index_path):
            current_app.logger.warning(f"文档向量索引记录存在，但文件不存在: {index_path}")
            return False, index_path
            
        return True, index_path
        
    except Exception as e:
        current_app.logger.error(f"检查文档向量索引失败: {str(e)}")
        return False, None

def load_document_segments_for_vector(document_id):
    """
    加载文档分段数据用于向量化
    
    参数:
        document_id: 文档ID
        
    返回:
        list: 分段数据列表
    """
    try:
        segments = DocumentSegment.query.filter_by(document_id=document_id).order_by(DocumentSegment.segment_number).all()
        
        segments_data = []
        for segment in segments:
            segments_data.append({
                "id": segment.id,
                "document_id": segment.document_id,
                "segment_number": segment.segment_number,
                "title": segment.title,
                "content": segment.content,
                "segment_type": segment.segment_type,
                "page_number": segment.page_number
            })
        
        current_app.logger.info(f"加载文档 {document_id} 的 {len(segments_data)} 个分段数据")
        return segments_data
        
    except Exception as e:
        current_app.logger.error(f"加载文档分段数据失败: {str(e)}")
        return []

def save_document_vector_index_to_db(document_id, index_path, embedding_model, total_vectors, preview_mode=False):
    """
    保存文档向量索引信息到数据库
    
    参数:
        document_id: 文档ID
        index_path: 索引文件路径
        embedding_model: 嵌入模型名称
        total_vectors: 向量总数
        preview_mode: 是否为预览模式
        
    返回:
        bool: 保存是否成功
    """
    try:
        if preview_mode:
            current_app.logger.info("预览模式：文档向量索引信息不保存到数据库")
            return True
        
        # 清除旧的向量索引记录
        DocumentVectorIndex.query.filter_by(document_id=document_id).delete()
        db.session.commit()
        
        # 创建新的向量索引记录
        vector_index = DocumentVectorIndex(
            document_id=document_id,
            index_path=index_path,
            embedding_model=embedding_model,
            total_vectors=total_vectors
        )
        db.session.add(vector_index)
        db.session.commit()
        
        current_app.logger.info(f"文档向量索引信息已保存到数据库: document_id={document_id}, total_vectors={total_vectors}")
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存文档向量索引信息到数据库失败: {str(e)}")
        return False

def process_document_vector_step(document_id, preview_mode=False):  # preview_mode参数保留但不再使用
    """
    执行文档向量化处理步骤
    
    参数:
        document_id: 文档ID
        preview_mode: 参数保留但不再使用(已弃用)
        
    返回:
        dict: 处理结果
    """
    try:
        current_app.logger.info(f"开始处理文档 {document_id} 的向量化步骤")
        
        # 1. 检查是否已存在向量索引
        vector_exists, existing_index_path = check_document_vector_index_exists(document_id)
        
        if vector_exists and not preview_mode:
            current_app.logger.info(f"文档 {document_id} 的向量索引已存在: {existing_index_path}")
            
            # 获取现有向量索引的信息
            vector_index = DocumentVectorIndex.query.filter_by(document_id=document_id).first()
            embedding_model = vector_index.embedding_model if vector_index else "Pro/BAAI/bge-m3"
            total_vectors = vector_index.total_vectors if vector_index else 0
            
            return {
                "success": True,
                "message": "向量索引已存在，跳过构建步骤",
                "index_path": existing_index_path,
                "embedding_model": embedding_model,
                "total_vectors": total_vectors,
                "action": "skipped"
            }
        
        # 2. 加载文档分段数据
        segments_data = load_document_segments_for_vector(document_id)
        
        if not segments_data:
            error_msg = f"文档 {document_id} 没有可用的分段数据，无法构建向量索引"
            current_app.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "index_path": "",
                "embedding_model": "Pro/BAAI/bge-m3",
                "total_vectors": 0,
                "action": "failed"
            }
        
        # 3. 构建向量索引
        index_path = f"{DOCUMENT_VECTOR_INDEX_DIR}/document_{document_id}"
        success = build_document_vector_index(document_id, segments_data, index_path)
        
        if not success:
            error_msg = f"文档 {document_id} 向量索引构建失败"
            current_app.logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "index_path": index_path,
                "embedding_model": "Pro/BAAI/bge-m3",
                "total_vectors": len(segments_data),
                "action": "failed"
            }
        
        # 4. 保存索引信息到数据库
        embedding_model = "Pro/BAAI/bge-m3"
        total_vectors = len(segments_data)
        
        db_success = save_document_vector_index_to_db(
            document_id, 
            index_path, 
            embedding_model, 
            total_vectors, 
            preview_mode
        )
        
        if not db_success and not preview_mode:
            current_app.logger.warning("向量索引构建成功，但数据库记录保存失败")
        
        # 5. 返回处理结果
        result = {
            "success": True,
            "message": f"文档向量索引构建{'（预览模式）' if preview_mode else ''}成功",
            "index_path": index_path,
            "embedding_model": embedding_model,
            "total_vectors": total_vectors,
            "action": "created"
        }
        
        current_app.logger.info(f"文档 {document_id} 向量化处理完成: {result}")
        return result
        
    except Exception as e:
        error_msg = f"文档向量化处理失败: {str(e)}"
        current_app.logger.error(error_msg)
        import traceback
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return {
            "success": False,
            "message": error_msg,
            "index_path": "",
            "embedding_model": "Pro/BAAI/bge-m3",
            "total_vectors": 0,
            "action": "failed"
        } 