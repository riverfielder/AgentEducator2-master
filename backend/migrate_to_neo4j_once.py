"""
一次性数据迁移脚本：从MySQL数据库同步知识图谱数据到Neo4j
执行一次后删除此文件
"""

import os
import sys
import logging
from flask import Flask

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 添加当前目录到路径

from models.models import db, Keyword, KeywordRelation, VideoKeyword, CourseKeyword
from services.knowledge_graph_service import get_neo4j_adapter

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_to_neo4j():
    """一次性迁移数据到Neo4j"""
    
    print("=== 知识图谱数据迁移到Neo4j ===")
    print()
    
    # 检查Neo4j连接
    adapter = get_neo4j_adapter()
    if not adapter.is_available():
        print("❌ Neo4j不可用，请检查：")
        print("1. Neo4j服务是否运行")
        print("2. 环境变量NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD是否设置")
        print("3. 是否安装了neo4j Python驱动: pip install neo4j")
        return False
    
    print("✅ Neo4j连接正常")
    
    try:
        # 1. 迁移知识点
        print("正在迁移知识点...")
        keywords = Keyword.query.all()
        success_count = 0
        
        for keyword in keywords:
            keyword_data = {
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description or '',
                'create_time': keyword.create_time.isoformat() if keyword.create_time else '',
                'update_time': keyword.update_time.isoformat() if keyword.update_time else ''
            }
            
            if adapter.sync_keyword(keyword_data):
                success_count += 1
        
        print(f"✅ 知识点迁移完成: {success_count}/{len(keywords)}")
        
        # 2. 迁移知识点关系
        print("正在迁移知识点关系...")
        relations = KeywordRelation.query.all()
        success_count = 0
        
        for relation in relations:
            if adapter.sync_keyword_relation(
                str(relation.source_keyword_id),
                str(relation.target_keyword_id),
                relation.relation_type,
                relation.strength
            ):
                success_count += 1
        
        print(f"✅ 知识点关系迁移完成: {success_count}/{len(relations)}")
        
        print()
        print("🎉 数据迁移完成！")
        print()
        print("现在您可以：")
        print("1. 使用Neo4j浏览器查看数据：http://localhost:7474")
        print("2. 在应用中使用增强的图查询功能")
        print("3. 删除此迁移脚本文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移过程中发生错误: {e}")
        return False
    
    finally:
        adapter.close()

def create_app():
    """创建Flask应用（用于数据库上下文）"""
    app = Flask(__name__)
    
    # 导入并使用正确的配置
    import dotenv
    dotenv.load_dotenv()
    
    from config import Config, WinstarConfig
    
    # 使用与主应用相同的配置逻辑
    if os.getenv('IS_DEBUG') == 'True':
        app.config.from_object(WinstarConfig)
    else:
        app.config.from_object(Config)
    
    db.init_app(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        success = migrate_to_neo4j()
        
        if success:
            print("\n✨ 迁移成功！请删除此脚本文件。")
        else:
            print("\n💡 迁移失败，请检查配置后重试。")
