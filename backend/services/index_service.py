"""向量索引服务模块"""
import os
import time
import traceback
from flask import current_app, has_app_context
from langchain_community.vectorstores import FAISS
from models.models import VideoVectorIndex, Video, db
from .embeddings_service import embeddings_service
from .cache_service import cache_service


class IndexService:
    """向量索引服务"""
    
    def get_video_index(self, video_id):
        """获取指定视频的向量索引（带缓存）"""
        cache_key = f"video_{video_id}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的视频索引: {video_id}")
            return cache_service.get_cached_index(cache_key), None
        
        if not has_app_context():
            from app import create_app
            app = create_app()
            app_ctx = app.app_context()
            app_ctx.push()
            try:
                result = self._get_video_index_impl(video_id)
                if result[0] is not None:  # 成功加载则缓存
                    cache_service.set_index_cache(cache_key, result[0])
                return result
            finally:
                app_ctx.pop()
        else:
            result = self._get_video_index_impl(video_id)
            if result[0] is not None:  # 成功加载则缓存
                cache_service.set_index_cache(cache_key, result[0])
            return result

    def get_course_video_index(self, course_id):
        """获取指定课程的向量索引（带缓存）"""
        cache_key = f"course_{course_id}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的课程索引: {course_id}")
            return cache_service.get_cached_index(cache_key), None
        
        if not has_app_context():
            from app import create_app
            app = create_app()
            app_ctx = app.app_context()
            app_ctx.push()
            try:
                result = self._get_course_video_index_impl(course_id)
                if result[0] is not None:  # 成功加载则缓存
                    cache_service.set_index_cache(cache_key, result[0])
                return result
            finally:
                app_ctx.pop()
        else:
            result = self._get_course_video_index_impl(course_id)
            if result[0] is not None:  # 成功加载则缓存
                cache_service.set_index_cache(cache_key, result[0])
            return result
    
    def merge_course_indices(self, course_ids):
        """高效合并多个课程的所有视频和文档向量索引，避免docstore_id冲突"""
        cache_key = f"multi_course_{'_'.join(map(str, sorted(course_ids)))}"
        if cache_service.has_cached_index(cache_key):
            return cache_service.get_cached_index(cache_key), None

        from models.models import Document, DocumentVectorIndex
        embeddings = embeddings_service.get_embeddings()
        all_indices = []
        all_doc_ids = set()
        try:
            # 视频索引
            videos_with_indices = db.session.query(Video, VideoVectorIndex).join(
                VideoVectorIndex, Video.id == VideoVectorIndex.video_id
            ).filter(Video.course_id.in_(course_ids), Video.is_deleted.is_(False)).all()
            for video, index_info in videos_with_indices:
                if os.path.exists(index_info.index_path):
                    try:
                        idx = FAISS.load_local(index_info.index_path, embeddings, allow_dangerous_deserialization=True)
                        # 检查docstore_id冲突
                        docstore = idx.docstore
                        index_to_docstore_id = idx.index_to_docstore_id
                        need_rename = False
                        for i in range(idx.index.ntotal):
                            doc_id = index_to_docstore_id[i]
                            if doc_id in all_doc_ids:
                                need_rename = True
                                break
                        if need_rename:
                            # 只重命名冲突部分
                            for i in range(idx.index.ntotal):
                                doc_id = index_to_docstore_id[i]
                                if doc_id in all_doc_ids:
                                    new_id = f"video_{video.id}_{i}_{os.urandom(4).hex()}"
                                    doc = docstore._dict.pop(doc_id)
                                    docstore._dict[new_id] = doc
                                    index_to_docstore_id[i] = new_id
                                    # 不直接改doc.metadata，避免副作用
                                all_doc_ids.add(index_to_docstore_id[i])
                        else:
                            for i in range(idx.index.ntotal):
                                all_doc_ids.add(index_to_docstore_id[i])
                        all_indices.append(idx)
                    except Exception:
                        continue
            # 文档索引
            documents_with_indices = db.session.query(Document, DocumentVectorIndex).join(
                DocumentVectorIndex, Document.id == DocumentVectorIndex.document_id
            ).filter(Document.course_id.in_(course_ids), Document.is_deleted.is_(False)).all()
            for document, index_info in documents_with_indices:
                if os.path.exists(index_info.index_path):
                    try:
                        idx = FAISS.load_local(index_info.index_path, embeddings, allow_dangerous_deserialization=True)
                        docstore = idx.docstore
                        index_to_docstore_id = idx.index_to_docstore_id
                        need_rename = False
                        for i in range(idx.index.ntotal):
                            doc_id = index_to_docstore_id[i]
                            if doc_id in all_doc_ids:
                                need_rename = True
                                break
                        if need_rename:
                            for i in range(idx.index.ntotal):
                                doc_id = index_to_docstore_id[i]
                                if doc_id in all_doc_ids:
                                    new_id = f"doc_{document.id}_{i}_{os.urandom(4).hex()}"
                                    doc = docstore._dict.pop(doc_id)
                                    docstore._dict[new_id] = doc
                                    index_to_docstore_id[i] = new_id
                                all_doc_ids.add(index_to_docstore_id[i])
                        else:
                            for i in range(idx.index.ntotal):
                                all_doc_ids.add(index_to_docstore_id[i])
                        all_indices.append(idx)
                    except Exception:
                        continue
            if not all_indices:
                return None, "未找到任何有效的索引内容"
            base_index = all_indices[0]
            for idx in all_indices[1:]:
                base_index.merge_from(idx)
            cache_service.set_index_cache(cache_key, base_index)
            return base_index, None
        except Exception as e:
            return None, f"合并索引失败: {str(e)}"
    
    def _get_course_video_index_impl(self, course_id):
        """实际获取课程视频索引的实现（优化版）"""
        try:
            start_time = time.time()
            embeddings = embeddings_service.get_embeddings()
            
            # 批量查询视频和索引信息
            videos_with_indices = db.session.query(Video, VideoVectorIndex).join(
                VideoVectorIndex, Video.id == VideoVectorIndex.video_id
            ).filter(Video.course_id == course_id,
                     Video.is_deleted.is_(False)).all()
            
            if not videos_with_indices:
                return None, f"课程 {course_id} 没有可用的视频索引"
            
            if has_app_context():
                current_app.logger.info(f"课程 {course_id} 有 {len(videos_with_indices)} 个有效视频索引")
            
            # 收集所有文档和向量
            combined_docs = []
            loaded_count = 0
            
            for video, index_info in videos_with_indices:
                if not os.path.exists(index_info.index_path):
                    if has_app_context():
                        current_app.logger.warning(f"索引文件不存在: {index_info.index_path}")
                    continue
                
                try:
                    current_index = FAISS.load_local(
                        index_info.index_path, 
                        embeddings, 
                        allow_dangerous_deserialization=True
                    )
                    
                    # 提取文档内容和嵌入向量
                    docstore = current_index.docstore
                    index_to_docstore_id = current_index.index_to_docstore_id

                    # 为每个文档生成唯一ID，避免冲突
                    for i in range(current_index.index.ntotal):
                        doc_id = index_to_docstore_id[i]
                        doc = docstore.search(doc_id)
                        if doc:
                            # 修改文档ID以避免冲突
                            new_metadata = dict(doc.metadata)
                            new_metadata['_unique_id'] = f"video_{video.id}_{i}"

                            # 提取向量并保存文档
                            vector = current_index.index.reconstruct(i)
                            combined_docs.append((
                                doc.page_content,
                                new_metadata,
                                vector
                            ))
                    
                    loaded_count += 1
                    if has_app_context():
                        current_app.logger.debug(f"成功处理视频 {video.id} 的索引")
                except Exception as e:
                    if has_app_context():
                        current_app.logger.error(f"加载视频 {video.id} 索引失败: {str(e)}")
                    continue
            
            if not combined_docs:
                return None, "未找到任何有效的视频索引内容"
            
            # 创建新索引
            try:
                # 提取文档、元数据和向量
                texts = [doc[0] for doc in combined_docs]
                metadatas = [doc[1] for doc in combined_docs]
                vectors = [doc[2] for doc in combined_docs]

                # 使用预计算的向量创建索引，避免重复计算嵌入
                base_index = FAISS.from_embeddings(
                    text_embeddings=list(zip(texts, vectors)),
                    embedding=embeddings,
                    metadatas=metadatas
                )

                load_time = time.time() - start_time
                if has_app_context():
                    current_app.logger.info(f"成功合并课程 {course_id} 的 {loaded_count} 个视频索引，总文档数: {len(texts)}，耗时 {load_time:.2f}s")
                return base_index, None

            except Exception as e:
                if has_app_context():
                    current_app.logger.error(f"构建索引失败: {str(e)}")
                return None, f"构建视频索引失败: {str(e)}"
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"获取课程索引失败: {str(e)}")
                traceback.print_exc()
            return None, f"获取课程索引失败: {str(e)}"

    def _get_video_index_impl(self, video_id):
        """实际获取视频索引的实现（优化版）"""
        try:
            # 查询数据库获取索引信息
            index_info = VideoVectorIndex.query.filter_by(video_id=video_id).first()
            if not index_info:
                return None, "视频索引不存在，请先处理视频"
                
            # 检查索引路径是否存在
            if not os.path.exists(index_info.index_path):
                return None, f"索引文件不存在: {index_info.index_path}"
                
            # 加载索引
            embeddings = embeddings_service.get_embeddings()
            index = FAISS.load_local(
                index_info.index_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            return index, None
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"加载索引失败: {str(e)}")
            return None, f"加载索引失败: {str(e)}"

    def get_document_index(self, document_id):
        """获取指定文档的向量索引（带缓存）"""
        cache_key = f"document_{document_id}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的文档索引: {document_id}")
            return cache_service.get_cached_index(cache_key), None
        
        if not has_app_context():
            from app import create_app
            app = create_app()
            app_ctx = app.app_context()
            app_ctx.push()
            try:
                result = self._get_document_index_impl(document_id)
                if result[0] is not None:  # 成功加载则缓存
                    cache_service.set_index_cache(cache_key, result[0])
                return result
            finally:
                app_ctx.pop()
        else:
            result = self._get_document_index_impl(document_id)
            if result[0] is not None:  # 成功加载则缓存
                cache_service.set_index_cache(cache_key, result[0])
            return result

    def get_course_document_index(self, course_id):
        """获取指定课程的所有文档向量索引（带缓存）"""
        cache_key = f"course_docs_{course_id}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的课程文档索引: {course_id}")
            return cache_service.get_cached_index(cache_key), None
        
        if not has_app_context():
            from app import create_app
            app = create_app()
            app_ctx = app.app_context()
            app_ctx.push()
            try:
                result = self._get_course_document_index_impl(course_id)
                if result[0] is not None:  # 成功加载则缓存
                    cache_service.set_index_cache(cache_key, result[0])
                return result
            finally:
                app_ctx.pop()
        else:
            result = self._get_course_document_index_impl(course_id)
            if result[0] is not None:  # 成功加载则缓存
                cache_service.set_index_cache(cache_key, result[0])
            return result

    def _get_document_index_impl(self, document_id):
        """实际获取文档索引的实现"""
        try:
            from models.models import DocumentVectorIndex
            
            # 查询数据库获取索引信息
            index_info = DocumentVectorIndex.query.filter_by(document_id=document_id).first()
            if not index_info:
                return None, "文档索引不存在，请先处理文档"
            
            # 检查索引文件是否存在
            if not os.path.exists(index_info.index_path):
                return None, f"索引文件不存在: {index_info.index_path}"
            
            # 加载索引
            embeddings = embeddings_service.get_embeddings()
            index = FAISS.load_local(
                index_info.index_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            
            if has_app_context():
                current_app.logger.info(f"成功加载文档 {document_id} 的索引，向量数: {index.index.ntotal}")
            return index, None
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"加载文档索引失败: {str(e)}")
                traceback.print_exc()
            return None, f"加载索引失败: {str(e)}"

    def _get_course_document_index_impl(self, course_id):
        """实际获取课程文档索引的实现"""
        try:
            from models.models import Document, DocumentVectorIndex
            start_time = time.time()
            embeddings = embeddings_service.get_embeddings()
            documents_with_indices = db.session.query(Document, DocumentVectorIndex).join(
                DocumentVectorIndex, Document.id == DocumentVectorIndex.document_id
            ).filter(Document.course_id == course_id,
                     Document.is_deleted.is_(False)).all()
            if not documents_with_indices:
                return None, f"课程 {course_id} 没有可用的文档索引"
            if has_app_context():
                current_app.logger.info(f"课程 {course_id} 有 {len(documents_with_indices)} 个有效文档索引")
            combined_docs = []
            loaded_count = 0
            for document, index_info in documents_with_indices:
                if not os.path.exists(index_info.index_path):
                    if has_app_context():
                        current_app.logger.warning(f"索引文件不存在: {index_info.index_path}")
                    continue
                try:
                    current_index = FAISS.load_local(
                        index_info.index_path, 
                        embeddings, 
                        allow_dangerous_deserialization=True
                    )
                    docstore = current_index.docstore
                    index_to_docstore_id = current_index.index_to_docstore_id
                    for i in range(current_index.index.ntotal):
                        doc_id = index_to_docstore_id[i]
                        doc = docstore.search(doc_id)
                        if doc:
                            new_metadata = dict(doc.metadata)
                            new_metadata['_unique_id'] = f"doc_{document.id}_{i}"
                            vector = current_index.index.reconstruct(i)
                            combined_docs.append((
                                doc.page_content,
                                new_metadata,
                                vector
                            ))
                    loaded_count += 1
                    if has_app_context():
                        current_app.logger.debug(f"成功处理文档 {document.id} 的索引")
                except Exception as e:
                    if has_app_context():
                        current_app.logger.error(f"加载文档 {document.id} 索引失败: {str(e)}")
                    continue
            if not combined_docs:
                return None, "未找到任何有效的文档索引内容"
            try:
                texts = [doc[0] for doc in combined_docs]
                metadatas = [doc[1] for doc in combined_docs]
                vectors = [doc[2] for doc in combined_docs]
                base_index = FAISS.from_embeddings(
                    text_embeddings=list(zip(texts, vectors)),
                    embedding=embeddings,
                    metadatas=metadatas
                )
                load_time = time.time() - start_time
                if has_app_context():
                    current_app.logger.info(f"成功合并课程 {course_id} 的 {loaded_count} 个文档索引，总文档数: {len(texts)}，耗时 {load_time:.2f}s")
                return base_index, None
            except Exception as e:
                if has_app_context():
                    current_app.logger.error(f"构建文档索引失败: {str(e)}")
                return None, f"构建文档索引失败: {str(e)}"
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"获取课程文档索引失败: {str(e)}")
                traceback.print_exc()
            return None, f"获取课程文档索引失败: {str(e)}"


# 全局索引服务实例
index_service = IndexService()
