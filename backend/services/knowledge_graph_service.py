"""
知识图谱数据同步服务
将SQLAlchemy模型数据同步到Neo4j图数据库
"""

from typing import List, Dict, Any, Optional
import dotenv # type: ignore
from datetime import datetime
import logging
import os

# 导入模型
dotenv.load_dotenv()  # 加载环境变量
def get_neo4j_adapter():
    """获取Neo4j适配器实例"""
    return Neo4jAdapter()
from models.models import (
    Keyword, VideoKeyword, CourseKeyword, KeywordRelation,
    Video, Course, db
)

logger = logging.getLogger(__name__)

# Neo4j适配器类（最小实现）
class Neo4jAdapter:
    """最小化Neo4j适配器"""
    
    def __init__(self):
        self.driver = None
        self._init_neo4j()
    
    def _init_neo4j(self):
        """初始化Neo4j连接"""
        try:
            # 检查是否安装了neo4j驱动
            from neo4j import GraphDatabase # type: ignore
            from config.config import Config
            
            # 获取配置
            uri = Config.get_neo4j_uri()
            username = Config.get_neo4j_username()
            password = Config.get_neo4j_password()
            
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            logger.info("Neo4j连接成功")
            
        except ImportError:
            logger.warning("Neo4j驱动未安装，跳过Neo4j功能")
            self.driver = None
        except Exception as e:
            logger.warning(f"Neo4j连接失败，跳过Neo4j功能: {e}")
            self.driver = None
    
    def is_available(self) -> bool:
        """检查Neo4j是否可用"""
        return self.driver is not None
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
    
    def sync_keyword(self, keyword_data: Dict[str, Any]) -> bool:
        """同步知识点到Neo4j"""
        if not self.is_available():
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (k:Keyword {id: $id})
                    SET k.name = $name,
                        k.category = $category,
                        k.description = $description,
                        k.create_time = $create_time,
                        k.update_time = $update_time
                """, keyword_data)
            return True
        except Exception as e:
            logger.error(f"同步知识点到Neo4j失败: {e}")
            return False
    
    def sync_keyword_relation(self, source_id: str, target_id: str, 
                            relation_type: str, strength: float = 1.0) -> bool:
        """同步知识点关系到Neo4j"""
        if not self.is_available():
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (source:Keyword {id: $source_id})
                    MATCH (target:Keyword {id: $target_id})
                    MERGE (source)-[r:RELATES {type: $relation_type}]->(target)
                    SET r.strength = $strength,
                        r.updated_at = datetime()
                """, {
                    'source_id': source_id,
                    'target_id': target_id,
                    'relation_type': relation_type,
                    'strength': strength
                })
            return True
        except Exception as e:
            logger.error(f"同步知识点关系到Neo4j失败: {e}")
            return False
    
    def get_prerequisite_path(self, target_keyword_id: str) -> List[Dict[str, Any]]:
        """获取前置知识路径（Neo4j查询）"""
        if not self.is_available():
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (start:Keyword)-[:RELATES*1..5]->(target:Keyword {id: $target_id})
                    WHERE ALL(r IN relationships(path) WHERE r.type = 'prerequisite')
                    RETURN [node in nodes(path) | {
                        id: node.id, 
                        name: node.name, 
                        category: node.category
                    }] as path_nodes
                    ORDER BY length(path)
                    LIMIT 10
                """, {'target_id': target_keyword_id})
                
                return [record['path_nodes'] for record in result]
        except Exception as e:
            logger.error(f"Neo4j查询前置路径失败: {e}")
            return []
    
    def get_related_keywords(self, keyword_id: str, min_strength: float = 0.5) -> List[Dict[str, Any]]:
        """获取相关知识点（Neo4j查询）"""
        if not self.is_available():
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (k:Keyword {id: $keyword_id})-[r:RELATES]-(related:Keyword)
                    WHERE r.strength >= $min_strength
                    RETURN related.id as id, related.name as name, 
                           related.category as category, r.strength as strength,
                           r.type as relation_type
                    ORDER BY r.strength DESC
                    LIMIT 20
                """, {'keyword_id': keyword_id, 'min_strength': min_strength})
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Neo4j查询相关知识点失败: {e}")
            return []

    def link_video_keyword(self, video_id: str, keyword_id: str, weight: float = 1.0) -> bool:
        """建立视频与知识点的关联关系"""
        if not self.is_available():
            return False
        
        try:
            with self.driver.session() as session:
                # 首先确保Video和Keyword节点存在
                session.run("""
                    MERGE (v:Video {id: $video_id})
                    MERGE (k:Keyword {id: $keyword_id})
                    MERGE (v)-[r:CONTAINS_KEYWORD]->(k)
                    SET r.weight = $weight,
                        r.updated_at = datetime()
                """, {
                    'video_id': video_id,
                    'keyword_id': keyword_id,
                    'weight': weight
                })
            return True
        except Exception as e:
            logger.error(f"建立视频-知识点关联失败: {e}")
            return False

    def link_course_keyword(self, course_id: str, keyword_id: str, 
                          video_count: int = 0, avg_weight: float = 0.0) -> bool:
        """建立课程与知识点的关联关系"""
        if not self.is_available():
            return False
        
        try:
            with self.driver.session() as session:
                # 首先确保Course和Keyword节点存在
                session.run("""
                    MERGE (c:Course {id: $course_id})
                    MERGE (k:Keyword {id: $keyword_id})
                    MERGE (c)-[r:INCLUDES_KEYWORD]->(k)
                    SET r.video_count = $video_count,
                        r.avg_weight = $avg_weight,
                        r.updated_at = datetime()
                """, {
                    'course_id': course_id,
                    'keyword_id': keyword_id,
                    'video_count': video_count,
                    'avg_weight': avg_weight
                })
            return True
        except Exception as e:
            logger.error(f"建立课程-知识点关联失败: {e}")
            return False

    def get_course_knowledge_map(self, course_id: str) -> Dict[str, Any]:
        """获取课程的知识图谱"""
        if not self.is_available():
            return {'keywords': [], 'relations': [], 'videos': []}
        
        try:
            with self.driver.session() as session:
                # 获取课程相关的知识点
                keywords_result = session.run("""
                    MATCH (c:Course {id: $course_id})-[r:INCLUDES_KEYWORD]->(k:Keyword)
                    RETURN k.id as id, k.name as name, k.category as category,
                           r.video_count as video_count, r.avg_weight as avg_weight
                """, {'course_id': course_id})
                
                keywords = [dict(record) for record in keywords_result]
                
                # 获取这些知识点之间的关系
                if keywords:
                    keyword_ids = [k['id'] for k in keywords]
                    relations_result = session.run("""
                        MATCH (k1:Keyword)-[r:RELATES]->(k2:Keyword)
                        WHERE k1.id IN $keyword_ids AND k2.id IN $keyword_ids
                        RETURN k1.id as source_id, k1.name as source_name,
                               k2.id as target_id, k2.name as target_name,
                               r.type as type, r.strength as strength
                    """, {'keyword_ids': keyword_ids})
                    
                    relations = [dict(record) for record in relations_result]
                else:
                    relations = []
                
                # 获取课程相关的视频
                videos_result = session.run("""
                    MATCH (c:Course {id: $course_id})-[:CONTAINS]-(v:Video)
                    RETURN v.id as id, v.title as title
                """, {'course_id': course_id})
                
                videos = [dict(record) for record in videos_result]
                
                return {
                    'keywords': keywords,
                    'relations': relations,
                    'videos': videos
                }
        except Exception as e:
            logger.error(f"获取课程知识图谱失败: {e}")
            return {'keywords': [], 'relations': [], 'videos': []}

class KnowledgeGraphSyncService:
    """知识图谱数据同步服务"""
    
    def __init__(self, neo4j_service=None):
        """
        初始化同步服务
        
        Args:
            neo4j_service: Neo4j服务实例（可选，如果为None则使用内置适配器）
        """
        self.neo4j_service = neo4j_service
    
    def sync_all_data(self):
        """同步所有知识图谱相关数据到Neo4j"""
        try:
            logger.info("开始同步知识图谱数据到Neo4j...")
            
            # 1. 同步知识点
            self.sync_keywords()
            
            # 2. 同步课程
            self.sync_courses()
            
            # 3. 同步视频
            self.sync_videos()
            
            # 4. 同步知识点关系
            self.sync_keyword_relations()
            
            # 5. 同步视频-知识点关系
            self.sync_video_keywords()
            
            # 6. 同步课程-知识点关系
            self.sync_course_keywords()
            
            logger.info("知识图谱数据同步完成")
            
        except Exception as e:
            logger.error(f"同步数据时发生错误: {e}")
            raise
    def sync_keywords(self):
        """同步知识点数据"""
        logger.info("同步知识点数据...")
        
        keywords = Keyword.query.all()
        for keyword in keywords:
            keyword_data = {
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description or '',
                'create_time': keyword.create_time.isoformat() if keyword.create_time else datetime.now().isoformat(),
                'update_time': keyword.update_time.isoformat() if keyword.update_time else datetime.now().isoformat()
            }
            
            try:
                # 尝试同步到Neo4j（如果可用）
                if hasattr(self.neo4j_service, 'sync_keyword'):
                    self.neo4j_service.sync_keyword(keyword_data)
                elif hasattr(self.neo4j_service, 'create_keyword'):
                    self.neo4j_service.create_keyword(keyword_data)
                logger.debug(f"同步知识点: {keyword.name}")
            except Exception as e:
                logger.warning(f"同步知识点 {keyword.name} 失败: {e}")
        
        logger.info(f"完成同步 {len(keywords)} 个知识点")
    
    def sync_courses(self):
        """同步课程数据"""
        logger.info("同步课程数据...")
        
        courses = Course.query.filter_by(is_deleted=False).all()
        for course in courses:
            course_data = {
                'id': str(course.id),
                'name': course.name,
                'code': course.code,
                'description': course.description or '',
                'teacher_id': str(course.teacher_id) if course.teacher_id else '',
                'create_time': course.create_time.isoformat() if course.create_time else datetime.now().isoformat()
            }
            
            try:
                self.neo4j_service.create_course_node(course_data)
                logger.debug(f"同步课程: {course.name}")
            except Exception as e:
                logger.warning(f"同步课程 {course.name} 失败: {e}")
        
        logger.info(f"完成同步 {len(courses)} 个课程")
    
    def sync_videos(self):
        """同步视频数据"""
        logger.info("同步视频数据...")
        
        videos = Video.query.filter_by(is_deleted=False).all()
        for video in videos:
            video_data = {
                'id': str(video.id),
                'title': video.title,
                'description': video.description or '',
                'duration': video.duration,
                'course_id': str(video.course_id) if video.course_id else '',
                'create_time': video.upload_time.isoformat() if video.upload_time else datetime.now().isoformat()
            }
            
            try:
                self.neo4j_service.create_video_node(video_data)
                logger.debug(f"同步视频: {video.title}")
            except Exception as e:
                logger.warning(f"同步视频 {video.title} 失败: {e}")
        
        logger.info(f"完成同步 {len(videos)} 个视频")
    def sync_keyword_relations(self):
        """同步知识点关系"""
        logger.info("同步知识点关系...")
        
        relations = KeywordRelation.query.all()
        for relation in relations:
            try:
                # 尝试同步到Neo4j（如果可用）
                if hasattr(self.neo4j_service, 'sync_keyword_relation'):
                    self.neo4j_service.sync_keyword_relation(
                        source_id=str(relation.source_keyword_id),
                        target_id=str(relation.target_keyword_id),
                        relation_type=relation.relation_type,
                        strength=relation.strength
                    )
                elif hasattr(self.neo4j_service, 'create_keyword_relation'):
                    self.neo4j_service.create_keyword_relation(
                        source_id=str(relation.source_keyword_id),
                        target_id=str(relation.target_keyword_id),
                        relation_type=relation.relation_type,
                        strength=relation.strength,
                        description=relation.description
                    )
                logger.debug(f"同步知识点关系: {relation.relation_type}")
            except Exception as e:
                logger.warning(f"同步知识点关系失败: {e}")
        
        logger.info(f"完成同步 {len(relations)} 个知识点关系")
    
    def sync_video_keywords(self):
        """同步视频-知识点关系"""
        logger.info("同步视频-知识点关系...")
        
        video_keywords = VideoKeyword.query.all()
        for vk in video_keywords:
            try:
                self.neo4j_service.link_video_keyword(
                    video_id=str(vk.video_id),
                    keyword_id=str(vk.keyword_id),
                    weight=vk.weight
                )
                logger.debug(f"同步视频-知识点关系: {vk.video_id} -> {vk.keyword_id}")
            except Exception as e:
                logger.warning(f"同步视频-知识点关系失败: {e}")
        
        logger.info(f"完成同步 {len(video_keywords)} 个视频-知识点关系")
    
    def sync_course_keywords(self):
        """同步课程-知识点关系"""
        logger.info("同步课程-知识点关系...")
        
        course_keywords = CourseKeyword.query.all()
        for ck in course_keywords:
            try:
                self.neo4j_service.link_course_keyword(
                    course_id=str(ck.course_id),
                    keyword_id=str(ck.keyword_id),
                    video_count=ck.video_count,
                    avg_weight=ck.avg_weight
                )
                logger.debug(f"同步课程-知识点关系: {ck.course_id} -> {ck.keyword_id}")
            except Exception as e:
                logger.warning(f"同步课程-知识点关系失败: {e}")
        
        logger.info(f"完成同步 {len(course_keywords)} 个课程-知识点关系")
    
    def sync_single_keyword(self, keyword: Keyword):
        """同步单个知识点"""
        keyword_data = {
            'id': str(keyword.id),
            'name': keyword.name,
            'category': keyword.category,
            'description': keyword.description or '',
            'create_time': keyword.create_time.isoformat() if keyword.create_time else datetime.now().isoformat(),
            'update_time': keyword.update_time.isoformat() if keyword.update_time else datetime.now().isoformat()
        }
        
        return self.neo4j_service.create_keyword(keyword_data)
    
    def sync_single_keyword_relation(self, relation: KeywordRelation):
        """同步单个知识点关系"""
        return self.neo4j_service.create_keyword_relation(
            source_id=str(relation.source_keyword_id),
            target_id=str(relation.target_keyword_id),
            relation_type=relation.relation_type,
            strength=relation.strength,
            description=relation.description
        )
    
    def sync_single_video_keyword(self, video_keyword: VideoKeyword):
        """同步单个视频-知识点关系"""
        return self.neo4j_service.link_video_keyword(
            video_id=str(video_keyword.video_id),
            keyword_id=str(video_keyword.keyword_id),
            weight=video_keyword.weight
        )

class KnowledgeGraphQueryService:
    """基于Neo4j的知识图谱查询服务"""
    
    def __init__(self, neo4j_service):
        self.neo4j_service = neo4j_service
    
    def get_course_knowledge_overview(self, course_id: str) -> Dict[str, Any]:
        """
        获取课程知识概览
        
        Args:
            course_id: 课程ID
            
        Returns:
            包含知识点分布、关系统计等信息的字典
        """
        knowledge_map = self.neo4j_service.get_course_knowledge_map(course_id)
        
        # 按分类统计知识点
        category_stats = {}
        for keyword in knowledge_map['keywords']:
            category = keyword['category']
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total_weight': 0,
                    'keywords': []
                }
            category_stats[category]['count'] += 1
            category_stats[category]['total_weight'] += keyword['avg_weight']
            category_stats[category]['keywords'].append(keyword['name'])
        
        # 关系类型统计
        relation_type_stats = {}
        for relation in knowledge_map['relations']:
            rel_type = relation['type']
            if rel_type not in relation_type_stats:
                relation_type_stats[rel_type] = 0
            relation_type_stats[rel_type] += 1
        
        return {
            'course_id': course_id,
            'total_keywords': len(knowledge_map['keywords']),
            'total_relations': len(knowledge_map['relations']),
            'category_distribution': category_stats,
            'relation_type_distribution': relation_type_stats,
            'knowledge_map': knowledge_map
        }
    def find_prerequisite_knowledge(self, keyword_name: str) -> List[Dict[str, Any]]:
        """
        查找知识点的前置知识（优先使用Neo4j图查询）
        
        Args:
            keyword_name: 知识点名称
            
        Returns:
            前置知识路径列表
        """
        # 首先找到知识点ID
        keyword = Keyword.query.filter_by(name=keyword_name).first()
        if not keyword:
            return []
        
        keyword_id = str(keyword.id)
        
        # 尝试使用Neo4j图查询
        if hasattr(self.neo4j_service, 'get_prerequisite_path'):
            try:
                return self.neo4j_service.get_prerequisite_path(keyword_id)
            except Exception as e:
                logger.warning(f"Neo4j查询失败，降级到SQLite: {e}")
        
        # 降级到SQLite查询
        return self._get_prerequisite_path_sqlite(keyword_id)
    
    def get_smart_recommendations(self, keyword_name: str) -> List[Dict[str, Any]]:
        """
        获取智能知识点推荐（优先使用Neo4j）
        
        Args:
            keyword_name: 知识点名称
            
        Returns:
            推荐的相关知识点列表
        """
        # 首先找到知识点ID
        keyword = Keyword.query.filter_by(name=keyword_name).first()
        if not keyword:
            return []
        
        keyword_id = str(keyword.id)
        
        # 尝试使用Neo4j图查询
        if hasattr(self.neo4j_service, 'get_related_keywords'):
            try:
                return self.neo4j_service.get_related_keywords(keyword_id)
            except Exception as e:
                logger.warning(f"Neo4j查询失败，降级到SQLite: {e}")
        
        # 降级到SQLite查询
        return self._get_related_keywords_sqlite(keyword_id)
    
    def _get_prerequisite_path_sqlite(self, keyword_id: str) -> List[Dict[str, Any]]:
        """SQLite版本的前置知识查询（降级方案）"""
        try:
            # 简单的递归查询前置关系
            relations = KeywordRelation.query.filter_by(
                target_keyword_id=keyword_id,
                relation_type='prerequisite'
            ).all()
            
            paths = []
            for relation in relations:
                source_keyword = Keyword.query.get(relation.source_keyword_id)
                if source_keyword:
                    paths.append([{
                        'id': str(source_keyword.id),
                        'name': source_keyword.name,
                        'category': source_keyword.category
                    }])
            
            return paths
        except Exception as e:
            logger.error(f"SQLite前置知识查询失败: {e}")
            return []
    
    def _get_related_keywords_sqlite(self, keyword_id: str) -> List[Dict[str, Any]]:
        """SQLite版本的相关知识点查询（降级方案）"""
        try:
            # 查询直接相关的知识点
            relations = KeywordRelation.query.filter(
                db.or_(
                    KeywordRelation.source_keyword_id == keyword_id,
                    KeywordRelation.target_keyword_id == keyword_id
                )
            ).limit(20).all()
            
            related = []
            for relation in relations:
                # 确定相关的知识点ID
                related_id = (relation.target_keyword_id 
                            if str(relation.source_keyword_id) == keyword_id 
                            else relation.source_keyword_id)
                
                related_keyword = Keyword.query.get(related_id)
                if related_keyword:
                    related.append({
                        'id': str(related_keyword.id),
                        'name': related_keyword.name,
                        'category': related_keyword.category,
                        'strength': relation.strength,
                        'relation_type': relation.relation_type
                    })
            
            return related
        except Exception as e:
            logger.error(f"SQLite相关知识点查询失败: {e}")
            return []
    
    def recommend_learning_sequence(self, course_id: str, 
                                  target_keywords: List[str]) -> List[Dict[str, Any]]:
        """
        推荐学习序列
        
        Args:
            course_id: 课程ID
            target_keywords: 目标知识点列表
            
        Returns:
            推荐的学习序列
        """
        learning_sequence = []
        
        for target_name in target_keywords:
            # 查找前置知识
            prerequisites = self.find_prerequisite_knowledge(target_name)
            
            if prerequisites:
                # 选择最短路径
                shortest_path = min(prerequisites, key=len) if prerequisites else []
                learning_sequence.append({
                    'target': target_name,
                    'prerequisite_path': shortest_path,
                    'path_length': len(shortest_path)
                })
            else:
                learning_sequence.append({
                    'target': target_name,
                    'prerequisite_path': [],
                    'path_length': 0
                })
        
        # 按路径长度排序，先学习前置知识较少的
        learning_sequence.sort(key=lambda x: x['path_length'])
        
        return learning_sequence
    
    def get_related_videos(self, keyword_name: str, course_id: str = None) -> List[Dict[str, Any]]:
        """
        获取与知识点相关的视频
        
        Args:
            keyword_name: 知识点名称
            course_id: 可选的课程ID过滤
            
        Returns:
            相关视频列表
        """
        # 找到知识点
        keyword = Keyword.query.filter_by(name=keyword_name).first()
        if not keyword:
            return []
        
        # 从Neo4j获取相关视频
        related_videos = self.neo4j_service.get_keyword_videos(str(keyword.id))
        
        # 如果指定了课程ID，进行过滤
        if course_id:
            filtered_videos = []
            for item in related_videos:
                video_data = item['video']
                if video_data.get('course_id') == course_id:
                    filtered_videos.append(item)
            return filtered_videos
        
        return related_videos
    
    def analyze_knowledge_gaps(self, course_id: str) -> Dict[str, Any]:
        """
        分析课程知识图谱中的空白点
        
        Args:
            course_id: 课程ID
            
        Returns:
            知识空白分析结果
        """
        knowledge_map = self.neo4j_service.get_course_knowledge_map(course_id)
        
        # 找出孤立的知识点（没有关系的知识点）
        connected_keywords = set()
        for relation in knowledge_map['relations']:
            connected_keywords.add(relation['source_id'])
            connected_keywords.add(relation['target_id'])
        
        isolated_keywords = []
        for keyword in knowledge_map['keywords']:
            if keyword['id'] not in connected_keywords:
                isolated_keywords.append(keyword)
        
        # 找出缺少前置关系的知识点
        keywords_with_prerequisites = set()
        for relation in knowledge_map['relations']:
            if relation['type'] == 'prerequisite':
                keywords_with_prerequisites.add(relation['target_id'])
        
        missing_prerequisites = []
        for keyword in knowledge_map['keywords']:
            if (keyword['category'] in ['main_module', 'specific_point'] and 
                keyword['id'] not in keywords_with_prerequisites):
                missing_prerequisites.append(keyword)
        
        return {
            'course_id': course_id,
            'isolated_keywords': isolated_keywords,
            'missing_prerequisites': missing_prerequisites,
            'total_keywords': len(knowledge_map['keywords']),
            'connected_keywords': len(connected_keywords),
            'connectivity_rate': len(connected_keywords) / len(knowledge_map['keywords']) if knowledge_map['keywords'] else 0
        }

# 全局服务实例
sync_service = None
query_service = None

def init_knowledge_graph_services(neo4j_service):
    """初始化知识图谱服务"""
    global sync_service, query_service
    sync_service = KnowledgeGraphSyncService(neo4j_service)
    query_service = KnowledgeGraphQueryService(neo4j_service)
    return sync_service, query_service

def get_sync_service() -> KnowledgeGraphSyncService:
    """获取同步服务实例"""
    global sync_service
    if sync_service is None:
        raise RuntimeError("知识图谱服务未初始化")
    return sync_service

def get_query_service() -> KnowledgeGraphQueryService:
    """获取查询服务实例"""
    global query_service
    if query_service is None:
        raise RuntimeError("知识图谱服务未初始化")
    return query_service
