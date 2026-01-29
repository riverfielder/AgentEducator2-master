"""缓存服务模块"""
from functools import lru_cache
from flask import has_app_context
from config.qa_config import LLMConfig
from models.models import Video, Course, Keyword, VideoKeyword, CourseKeyword, VideoSummary, Document, DocumentKeyword, DocumentSummary
from sqlalchemy.orm import joinedload
from .redis_service import redis_service
import pickle

class CacheService:
    """缓存服务"""
    
    def __init__(self):
        # 索引缓存
        self._index_cache = {}
        self._use_redis = redis_service.is_connected()
    
    def get_course_cache_key(self, course_id):
        """生成基于课程ID和最近更新时间的缓存键"""
        try:
            def get_course_updates():
                from models.models import db, VideoVectorIndex, DocumentVectorIndex, Video, Document
                from sqlalchemy import func
                
                # 获取该课程最近的视频向量索引更新时间
                latest_video_update = (db.session.query(func.max(VideoVectorIndex.update_time))
                                     .join(Video, VideoVectorIndex.video_id == Video.id)
                                     .filter(Video.course_id == course_id, Video.is_deleted == False)
                                     .scalar())
                
                # 获取该课程最近的文档向量索引更新时间
                latest_doc_update = (db.session.query(func.max(DocumentVectorIndex.update_time))
                                   .join(Document, DocumentVectorIndex.document_id == Document.id)
                                   .filter(Document.course_id == course_id, Document.is_deleted == False)
                                   .scalar())
                return latest_video_update, latest_doc_update
            
            # 确保在应用上下文中执行数据库查询
            if not has_app_context():
                from app import create_app
                app = create_app()
                with app.app_context():
                    latest_video_update, latest_doc_update = get_course_updates()
            else:
                latest_video_update, latest_doc_update = get_course_updates()
            
            # 取两者中的最新时间
            latest_update = None
            if latest_video_update and latest_doc_update:
                latest_update = max(latest_video_update, latest_doc_update)
            elif latest_video_update:
                latest_update = latest_video_update
            elif latest_doc_update:
                latest_update = latest_doc_update
            
            # 生成缓存键：课程ID_最近更新时间戳
            if latest_update:
                timestamp = int(latest_update.timestamp())
                return f"ensemble_retriever_{course_id}_{timestamp}"
            else:
                # 如果没有向量索引，使用当前时间戳
                import time
                return f"ensemble_retriever_{course_id}_{int(time.time())}"
                
        except Exception as e:
            print(f"[ERROR] 生成课程缓存键失败: {e}")
            # 发生异常时使用简单的缓存键
            import time
            return f"ensemble_retriever_{course_id}_{int(time.time())}"
    
    def get_general_cache_key(self, prefix, *args, **kwargs):
        """生成基于全局最新向量时间的通用缓存键
        
        Args:
            prefix (str): 缓存键前缀
            *args: 位置参数，将被转换为字符串并用下划线连接
            **kwargs: 关键字参数，将按键名排序后用下划线连接
            
        Returns:
            str: 生成的缓存键，格式为 prefix_args_kwargs_global_timestamp
            
        Examples:
            get_general_cache_key("user", 123, "profile") -> "user_123_profile_1704067200"
            get_general_cache_key("search", query="python", limit=10) -> "search_limit_10_query_python_1704067200"
            get_general_cache_key("video", 456, type="summary", lang="zh") -> "video_456_lang_zh_type_summary_1704067200"
        """
        try:
            def get_latest_updates():
                from models.models import db, VideoVectorIndex, DocumentVectorIndex
                from sqlalchemy import func
                
                # 获取全局最新的向量索引更新时间
                latest_video_update = db.session.query(func.max(VideoVectorIndex.update_time)).scalar()
                latest_doc_update = db.session.query(func.max(DocumentVectorIndex.update_time)).scalar()
                return latest_video_update, latest_doc_update
            
            # 确保在应用上下文中执行数据库查询
            if not has_app_context():
                from app import create_app
                app = create_app()
                with app.app_context():
                    latest_video_update, latest_doc_update = get_latest_updates()
            else:
                latest_video_update, latest_doc_update = get_latest_updates()
            
            # 取两者中的最新时间
            global_latest_update = None
            if latest_video_update and latest_doc_update:
                global_latest_update = max(latest_video_update, latest_doc_update)
            elif latest_video_update:
                global_latest_update = latest_video_update
            elif latest_doc_update:
                global_latest_update = latest_doc_update
            
            # 构建缓存键组件列表
            key_parts = [str(prefix)]
            
            # 添加位置参数
            for arg in args:
                if arg is not None:
                    key_parts.append(str(arg))
            
            # 添加关键字参数（按键名排序以确保一致性）
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                for key, value in sorted_kwargs:
                    if value is not None:
                        key_parts.extend([str(key), str(value)])
            
            # 添加全局时间戳
            if global_latest_update:
                timestamp = int(global_latest_update.timestamp())
                key_parts.append(str(timestamp))
            else:
                # 如果没有向量索引，使用当前时间戳
                import time
                key_parts.append(str(int(time.time())))
            
            # 用下划线连接所有部分
            cache_key = "_".join(key_parts)
            
            # 确保缓存键不会过长（Redis键名限制为512MB，但实际建议不超过250字符）
            if len(cache_key) > 250:
                import hashlib
                # 如果键太长，使用哈希值
                hash_suffix = hashlib.md5(cache_key.encode()).hexdigest()[:8]
                if global_latest_update:
                    timestamp = int(global_latest_update.timestamp())
                    cache_key = f"{prefix}_{hash_suffix}_{timestamp}"
                else:
                    import time
                    cache_key = f"{prefix}_{hash_suffix}_{int(time.time())}"
            
            return cache_key
            
        except Exception as e:
            print(f"[ERROR] 生成通用缓存键失败: {e}")
            # 发生异常时使用简单的缓存键
            import time
            return f"{prefix}_{int(time.time())}"

    def get_index_cache(self):
        """获取索引缓存（仅本地）"""
        return self._index_cache
    
    def set_index_cache(self, key, value, expire_seconds=36000000):
        """设置索引缓存，优先Redis，降级本地"""
        if self._use_redis:
            try:
                redis_service.set(key, pickle.dumps(value), expire_seconds)
            except Exception:
                self._index_cache[key] = value
        else:
            self._index_cache[key] = value
    
    def get_cached_index(self, key):
        """获取缓存的索引，优先Redis，降级本地"""
        if self._use_redis:
            try:
                data = redis_service.get(key)
                if data is not None:
                    return pickle.loads(data)
            except Exception:
                return self._index_cache.get(key)
        return self._index_cache.get(key)
    
    def has_cached_index(self, key):
        """检查是否有缓存的索引，优先Redis，降级本地"""
        if self._use_redis:
            try:
                return redis_service.exists(key)
            except Exception:
                return key in self._index_cache
        return key in self._index_cache


# 视频信息缓存装饰器
@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_video_info(video_id):
    """缓存视频信息查询"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_video_info_impl(video_id)
    else:
        return _get_video_info_impl(video_id)

def _get_video_info_impl(video_id):
    """获取视频信息的实际实现，包含事务处理"""
    try:
        from models.models import db
        video = Video.query.filter_by(id=video_id).first()
        return (video.title, video.course_id) if video else (None, None)
    except Exception as e:
        # 发生异常时回滚事务
        try:
            db.session.rollback()
        except:
            pass
        print(f"[ERROR] 获取视频信息失败: {e}")
        return (None, None)


# 课程信息缓存装饰器
@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_course_info(course_id):
    """缓存课程信息查询"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_course_info_impl(course_id)
    else:
        return _get_course_info_impl(course_id)

def _get_course_info_impl(course_id):
    """获取课程信息的实际实现，包含事务处理"""
    try:
        from models.models import db
        course = Course.query.filter_by(id=course_id).first()
        return course.name if course else None
    except Exception as e:
        # 发生异常时回滚事务
        try:
            db.session.rollback()
        except:
            pass
        print(f"[ERROR] 获取课程信息失败: {e}")
        return None


# 视频知识点缓存装饰器
@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_video_keywords(video_id, limit=20):
    """缓存视频知识点查询，返回按权重排序的前N个知识点"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_video_keywords_impl(video_id, limit)
    else:
        return _get_video_keywords_impl(video_id, limit)

@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_video_summary(video_id):
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            video_summary = VideoSummary.query.filter_by(video_id=video_id).first()
            return video_summary.whole_summary if video_summary else None

def _get_video_keywords_impl(video_id, limit):
    """获取视频知识点的实际实现"""
    try:
        from models.models import db
        video_keywords = (VideoKeyword.query
                          .filter_by(video_id=video_id)
                          .join(Keyword)
                          .with_entities(Keyword.name, VideoKeyword.weight)
                          .order_by(VideoKeyword.weight.desc())
                          .limit(limit)
                          .all())
        
        return [{"name": kw.name, "weight": kw.weight} for kw in video_keywords] if video_keywords else []
    except Exception as e:
        # 发生异常时回滚事务
        try:
            db.session.rollback()
        except:
            pass
        print(f"[ERROR] 获取视频知识点失败: {e}")
        return []


# 课程知识点缓存装饰器  
@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_course_keywords(course_id, limit=10):
    """缓存课程知识点查询，返回按重要性排序的前N个知识点"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_course_keywords_impl(course_id, limit)
    else:
        return _get_course_keywords_impl(course_id, limit)


def _get_course_keywords_impl(course_id, limit):
    """获取课程知识点的实际实现"""
    try:
        from models.models import db
        course_keywords = (CourseKeyword.query
                           .filter_by(course_id=course_id)
                           .join(Keyword)
                           .with_entities(
                               Keyword.name, 
                               Keyword.category,
                               CourseKeyword.video_count,
                               CourseKeyword.avg_weight
                           )
                           .order_by(
                               CourseKeyword.video_count.desc(),
                               CourseKeyword.avg_weight.desc()
                           )
                           .limit(limit)
                           .all())
        
        return [{"name": kw.name, "category": kw.category, "video_count": kw.video_count, "avg_weight": kw.avg_weight} 
                for kw in course_keywords] if course_keywords else []
    except Exception as e:
        # 发生异常时回滚事务
        try:
            db.session.rollback()
        except:
            pass
        print(f"[ERROR] 获取课程知识点失败: {e}")
        return []


# 文档信息缓存装饰器
@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_document_info(document_id):
    """缓存文档信息查询"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            document = Document.query.filter_by(id=document_id).first()
            return (document.title, document.course_id) if document else (None, None)
    else:
        document = Document.query.filter_by(id=document_id).first()
        return (document.title, document.course_id) if document else (None, None)


# 文档知识点缓存装饰器
@lru_cache(maxsize=LLMConfig.LRU_CACHE_SIZE)
def get_document_keywords(document_id, limit=20):
    """缓存文档知识点查询，返回按权重排序的前N个知识点"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_document_keywords_impl(document_id, limit)
    else:
        return _get_document_keywords_impl(document_id, limit)


def _get_document_keywords_impl(document_id, limit):
    """获取文档知识点的实际实现"""
    document_keywords = (DocumentKeyword.query
                        .filter_by(document_id=document_id)
                        .join(Keyword)
                        .with_entities(Keyword.name, DocumentKeyword.weight)
                        .order_by(DocumentKeyword.weight.desc())
                        .limit(limit)
                        .all())
    
    return [{"name": kw.name, "weight": kw.weight} for kw in document_keywords] if document_keywords else []


# 全局缓存实例
cache_service = CacheService()
