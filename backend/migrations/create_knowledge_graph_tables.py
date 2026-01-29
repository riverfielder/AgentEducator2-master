"""
创建知识图谱相关数据表
"""

from models.models import db, Keyword, VideoKeyword, CourseKeyword, KeywordRelation, KnowledgeGraphProcessingTask

def create_knowledge_graph_tables():
    """创建知识图谱相关的数据表"""
    try:
        # 创建知识点表
        db.create_all()
        
        print("✅ 知识图谱相关数据表创建成功:")
        print("  - keywords (知识点表)")
        print("  - video_keywords (视频知识点关系表)")
        print("  - course_keywords (课程知识点关系表)")
        print("  - keyword_relations (知识点关系表)")
        print("  - knowledge_graph_tasks (知识图谱处理任务表)")
        
        return True
    except Exception as e:
        print(f"❌ 创建知识图谱数据表失败: {str(e)}")
        return False

if __name__ == "__main__":
    from app import app
    
    with app.app_context():
        success = create_knowledge_graph_tables()
        if success:
            print("\n🎉 知识图谱数据表创建完成!")
        else:
            print("\n💥 知识图谱数据表创建失败!")
