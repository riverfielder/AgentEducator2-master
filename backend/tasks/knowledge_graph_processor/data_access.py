"""知识图谱处理器数据访问层"""

from sqlalchemy import func, and_, or_
from collections import defaultdict
from models.models import (
    db, Video, Course, Document,
    Keyword, VideoKeyword, CourseKeyword, DocumentKeyword,
    KeywordRelation, KnowledgeGraphProcessingTask
)

class KnowledgeGraphDataAccess:
    """知识图谱数据访问层"""
    
    @staticmethod
    def get_course_videos(course_id):
        """获取课程视频"""
        return Video.query.filter_by(course_id=course_id).all()
    
    @staticmethod
    def get_course_documents(course_id):
        """获取课程文档"""
        return Document.query.filter_by(course_id=course_id).all()
    
    @staticmethod
    def get_course_info(course_id):
        """获取课程信息"""
        return Course.query.get(course_id)
    
    @staticmethod
    def get_video_keywords(video_id):
        """获取视频关键词"""
        return db.session.query(Keyword).join(VideoKeyword).filter(
            VideoKeyword.video_id == video_id
        ).all()
    
    @staticmethod
    def get_document_keywords(document_id):
        """获取文档关键词"""
        return db.session.query(Keyword).join(DocumentKeyword).filter(
            DocumentKeyword.document_id == document_id
        ).all()
    
    @staticmethod
    def get_course_keywords_by_category(course_id):
        """按分类获取课程关键词"""
        keywords = db.session.query(Keyword).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        ).distinct().all()  # 添加distinct去重
        
        categorized = {
            'core_concept': [],
            'main_module': [],
            'specific_point': []
        }
        
        # 使用集合去重关键词名称
        seen_names = {
            'core_concept': set(),
            'main_module': set(),
            'specific_point': set()
        }
        
        for keyword in keywords:
            category = keyword.category or 'specific_point'
            if category in categorized and keyword.name not in seen_names[category]:
                categorized[category].append(keyword)
                seen_names[category].add(keyword.name)
        
        return categorized
    
    @staticmethod
    def get_all_course_keywords(course_id):
        """获取课程所有关键词"""
        # 直接从CourseKeyword表获取，确保去重
        keywords = db.session.query(Keyword).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        ).distinct().all()
        
        # 再次基于关键词名称去重，以防数据库中有重复记录
        unique_keywords = {}
        for keyword in keywords:
            if keyword.name not in unique_keywords:
                unique_keywords[keyword.name] = keyword
        
        return list(unique_keywords.values())
    
    @staticmethod
    def get_keyword_relations(keyword_ids=None):
        """获取关键词关系"""
        query = KeywordRelation.query
        if keyword_ids:
            query = query.filter(
                or_(
                    KeywordRelation.source_keyword_id.in_(keyword_ids),
                    KeywordRelation.target_keyword_id.in_(keyword_ids)
                )
            )
        return query.all()
    
    @staticmethod
    def check_relation_exists(source_id, target_id, relation_type):
        """检查关系是否存在"""
        return KeywordRelation.query.filter_by(
            source_keyword_id=source_id,
            target_keyword_id=target_id,
            relation_type=relation_type
        ).first() is not None
    
    @staticmethod
    def get_orphaned_keywords(course_id):
        """获取孤立关键词（没有任何关系的关键词）"""
        # 获取课程所有关键词
        all_keywords = KnowledgeGraphDataAccess.get_all_course_keywords(course_id)
        keyword_ids = [k.id for k in all_keywords]
        
        # 获取有关系的关键词ID
        connected_ids = set()
        relations = db.session.query(KeywordRelation).filter(
            or_(
                KeywordRelation.source_keyword_id.in_(keyword_ids),
                KeywordRelation.target_keyword_id.in_(keyword_ids)
            )
        ).all()
        
        for relation in relations:
            connected_ids.add(relation.source_keyword_id)
            connected_ids.add(relation.target_keyword_id)
        
        # 找出孤立的关键词
        orphaned_keywords = [k for k in all_keywords if k.id not in connected_ids]
        return orphaned_keywords
    
    @staticmethod
    def save_keywords(keywords_data):
        """保存关键词分类信息"""
        for keyword_data in keywords_data:
            keyword = Keyword.query.filter_by(name=keyword_data['keyword']).first()
            if keyword:
                keyword.category = keyword_data['category']
        
        db.session.commit()
    
    @staticmethod
    def save_relations(relations_data):
        """保存关键词关系"""
        saved_count = 0
        
        for relation_data in relations_data:
            source_keyword = Keyword.query.filter_by(name=relation_data['source']).first()
            target_keyword = Keyword.query.filter_by(name=relation_data['target']).first()
            
            if not source_keyword or not target_keyword:
                continue
            
            # 检查关系是否已存在
            if KnowledgeGraphDataAccess.check_relation_exists(
                source_keyword.id, target_keyword.id, relation_data['relation_type']
            ):
                continue
            
            # 创建新关系
            relation = KeywordRelation(
                source_keyword_id=source_keyword.id,
                target_keyword_id=target_keyword.id,
                relation_type=relation_data['relation_type'],
                strength=relation_data.get('strength', 1.0),
                description=relation_data.get('reason', '')
            )
            
            db.session.add(relation)
            saved_count += 1
        
        db.session.commit()
        return saved_count
    
    @staticmethod
    def update_course_keyword_stats(course_id):
        """更新课程关键词统计"""
        # 获取视频关键词统计
        video_stats = db.session.query(
            func.count(VideoKeyword.keyword_id).label('count'),
            func.avg(VideoKeyword.weight).label('avg_weight')
        ).join(Video).filter(Video.course_id == course_id).first()
        
        # 获取文档关键词统计
        document_stats = db.session.query(
            func.count(DocumentKeyword.keyword_id).label('count'),
            func.avg(DocumentKeyword.weight).label('avg_weight')
        ).join(Document).filter(Document.course_id == course_id).first()
        
        # 更新课程关键词表
        course_keywords = CourseKeyword.query.filter_by(course_id=course_id).all()
        
        for course_keyword in course_keywords:
            # 计算综合权重
            video_weight = video_stats.avg_weight or 0
            document_weight = document_stats.avg_weight or 0
            
            if video_weight > 0 and document_weight > 0:
                course_keyword.weight = (video_weight + document_weight) / 2
            elif video_weight > 0:
                course_keyword.weight = video_weight
            elif document_weight > 0:
                course_keyword.weight = document_weight
            else:
                course_keyword.weight = 0.5
        
        db.session.commit()
    
    @staticmethod
    def create_processing_task(course_id, task_type='full'):
        """创建处理任务记录"""
        task = KnowledgeGraphProcessingTask(
            course_id=course_id,
            task_type=task_type,
            status='running',
            progress=0
        )
        db.session.add(task)
        db.session.commit()
        return task
    
    @staticmethod
    def update_task_progress(task_id, progress, status=None, error_message=None):
        """更新任务进度"""
        task = KnowledgeGraphProcessingTask.query.get(task_id)
        if task:
            task.progress = progress
            if status:
                task.status = status
            if error_message:
                task.error_message = error_message
            db.session.commit()
    
    @staticmethod
    def get_content_processed_status(course_id):
        """获取内容处理状态"""
        # 获取课程视频
        videos = Video.query.filter_by(course_id=course_id).all()
        
        # 获取课程文档
        documents = Document.query.filter_by(course_id=course_id).all()
        
        # 检查视频处理状态
        processed_videos = []
        unprocessed_videos = []
        
        for video in videos:
            if KnowledgeGraphDataAccess._is_content_processed(video.id, 'video'):
                processed_videos.append(video.id)
            else:
                unprocessed_videos.append(video.id)
        
        # 检查文档处理状态
        processed_documents = []
        unprocessed_documents = []
        
        for document in documents:
            if KnowledgeGraphDataAccess._is_content_processed(document.id, 'document'):
                processed_documents.append(document.id)
            else:
                unprocessed_documents.append(document.id)
        
        return {
            'videos': {
                'processed': processed_videos,
                'unprocessed': unprocessed_videos,
                'total': len(videos)
            },
            'documents': {
                'processed': processed_documents,
                'unprocessed': unprocessed_documents,
                'total': len(documents)
            }
        }
    
    @staticmethod
    def _is_content_processed(content_id, content_type):
        """检查内容是否已被处理"""
        if content_type == 'video':
            # 获取视频的关键词
            keyword_ids = db.session.query(VideoKeyword.keyword_id).filter_by(
                video_id=content_id
            ).subquery()
        else:  # document
            # 获取文档的关键词
            keyword_ids = db.session.query(DocumentKeyword.keyword_id).filter_by(
                document_id=content_id
            ).subquery()
        
        # 检查这些关键词是否参与了关系建立
        relations_count = db.session.query(KeywordRelation).filter(
            or_(
                KeywordRelation.source_keyword_id.in_(keyword_ids),
                KeywordRelation.target_keyword_id.in_(keyword_ids)
            )
        ).count()
        
        return relations_count > 0