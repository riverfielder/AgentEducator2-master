#!/usr/bin/env python3
"""
知识图谱维护工具 - 清空课程知识图谱
用于强制清空指定课程的所有知识图谱相关数据
"""

import sys
import os
import argparse
import uuid
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.models import (
    db, Course, Video, Document, Keyword, VideoKeyword, DocumentKeyword, 
    CourseKeyword, KeywordRelation, KnowledgeGraphProcessingTask
)
from config.config import WinstarConfig


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(WinstarConfig)
    
    # 初始化数据库
    db.init_app(app)
    
    return app


def validate_course_id(course_id_str):
    """验证课程ID格式"""
    try:
        # 尝试转换为UUID格式
        course_uuid = uuid.UUID(course_id_str)
        return str(course_uuid)
    except ValueError:
        raise argparse.ArgumentTypeError(f"无效的课程ID格式: {course_id_str}")


def get_course_info(course_id):
    """获取课程信息"""
    course = Course.query.get(course_id)
    if not course:
        return None
    
    return {
        'id': str(course.id),
        'name': course.name,
        'description': course.description or '',
        'create_time': course.create_time.strftime('%Y-%m-%d %H:%M:%S') if course.create_time else 'Unknown'
    }


def get_course_knowledge_graph_stats(course_id):
    """获取课程知识图谱统计信息"""
    # 获取课程下的所有视频ID
    video_ids = [row[0] for row in db.session.query(Video.id).filter(
        Video.course_id == course_id,
        Video.is_deleted == False
    ).all()]
    
    # 获取课程下的所有文档ID
    document_ids = [row[0] for row in db.session.query(Document.id).filter(
        Document.course_id == course_id,
        Document.is_deleted == False
    ).all()]
    
    # 获取视频知识点
    video_keyword_ids = []
    if video_ids:
        video_keyword_ids = [row[0] for row in db.session.query(VideoKeyword.keyword_id).filter(
            VideoKeyword.video_id.in_(video_ids)
        ).distinct().all()]
    
    # 获取文档知识点
    document_keyword_ids = []
    if document_ids:
        document_keyword_ids = [row[0] for row in db.session.query(DocumentKeyword.keyword_id).filter(
            DocumentKeyword.document_id.in_(document_ids)
        ).distinct().all()]
    
    # 合并所有相关知识点ID
    all_keyword_ids = list(set(video_keyword_ids + document_keyword_ids))
    
    # 统计知识点关系
    relation_count = 0
    if all_keyword_ids:
        relation_count = db.session.query(KeywordRelation).filter(
            (KeywordRelation.source_keyword_id.in_(all_keyword_ids)) | 
            (KeywordRelation.target_keyword_id.in_(all_keyword_ids))
        ).count()
    
    # 统计知识点分类
    category_stats = {}
    if all_keyword_ids:
        category_results = db.session.query(
            Keyword.category, 
            db.func.count(Keyword.id)
        ).filter(
            Keyword.id.in_(all_keyword_ids)
        ).group_by(Keyword.category).all()
        category_stats = {cat: count for cat, count in category_results}
    
    return {
        'videos': len(video_ids),
        'documents': len(document_ids),
        'unique_keywords': len(all_keyword_ids),
        'video_keyword_relations': len(video_keyword_ids),
        'document_keyword_relations': len(document_keyword_ids),
        'keyword_relations': relation_count,
        'category_distribution': category_stats
    }


def clear_course_knowledge_graph(course_id, dry_run=False):
    """清空课程知识图谱数据 - 只删除关系和重置分类"""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}开始清理课程 {course_id} 的知识图谱...")
    
    # 获取课程下的所有视频和文档ID
    video_ids = [row[0] for row in db.session.query(Video.id).filter(
        Video.course_id == course_id,
        Video.is_deleted == False
    ).all()]
    
    document_ids = [row[0] for row in db.session.query(Document.id).filter(
        Document.course_id == course_id,
        Document.is_deleted == False
    ).all()]
    
    print(f"发现 {len(video_ids)} 个视频, {len(document_ids)} 个文档")
    
    # 获取所有相关的知识点ID
    video_keyword_ids = []
    document_keyword_ids = []
    
    if video_ids:
        video_keyword_ids = [row[0] for row in db.session.query(VideoKeyword.keyword_id).filter(
            VideoKeyword.video_id.in_(video_ids)
        ).distinct().all()]
        print(f"视频关联的知识点: {len(video_keyword_ids)} 个")
    
    if document_ids:
        document_keyword_ids = [row[0] for row in db.session.query(DocumentKeyword.keyword_id).filter(
            DocumentKeyword.document_id.in_(document_ids)
        ).distinct().all()]
        print(f"文档关联的知识点: {len(document_keyword_ids)} 个")
    
    # 合并所有知识点ID
    all_keyword_ids = list(set(video_keyword_ids + document_keyword_ids))
    print(f"总共涉及知识点: {len(all_keyword_ids)} 个")
    
    if not dry_run:
        try:
            deleted_counts = {}
            
            # 1. 删除知识点关系
            if all_keyword_ids:
                relation_delete_count = db.session.query(KeywordRelation).filter(
                    (KeywordRelation.source_keyword_id.in_(all_keyword_ids)) | 
                    (KeywordRelation.target_keyword_id.in_(all_keyword_ids))
                ).delete(synchronize_session=False)
                deleted_counts['keyword_relations'] = relation_delete_count
                print(f"✓ 删除知识点关系: {relation_delete_count} 条")
            
            # 2. 重置涉及的知识点分类为默认值
            if all_keyword_ids:
                keyword_reset_count = db.session.query(Keyword).filter(
                    Keyword.id.in_(all_keyword_ids)
                ).update(
                    {Keyword.category: 'specific_point'},
                    synchronize_session=False
                )
                deleted_counts['keywords_reset'] = keyword_reset_count
                print(f"✓ 重置知识点分类: {keyword_reset_count} 个")
            
            # 提交所有更改
            db.session.commit()
            print(f"\n✅ 课程 {course_id} 的知识图谱结构已成功清空!")
            print("注意: 知识点本身及其与视频/文档的关联保持不变")
            
            return deleted_counts
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清空知识图谱时发生错误: {str(e)}")
            raise e
    else:
        print(f"\n[DRY RUN] 将要执行的清理操作:")
        print(f"  - 删除知识点关系: 涉及 {len(all_keyword_ids)} 个知识点的所有关系")
        print(f"  - 重置知识点分类: {len(all_keyword_ids)} 个知识点 -> specific_point")
        print(f"\n保持不变的数据:")
        print(f"  - 知识点本身 ({len(all_keyword_ids)} 个)")
        print(f"  - 视频-知识点关联 ({len(video_keyword_ids)} 条)")
        print(f"  - 文档-知识点关联 ({len(document_keyword_ids)} 条)")
        print(f"\n使用 --execute 参数来实际执行清理操作")
        
        return None


def list_courses():
    """列出所有课程"""
    courses = db.session.query(Course).filter(Course.is_deleted == False).all()
    
    if not courses:
        print("没有找到任何课程")
        return
    
    print(f"\n找到 {len(courses)} 个课程:")
    print("-" * 80)
    print(f"{'课程ID':<40} {'课程名称':<30} {'创建时间':<20}")
    print("-" * 80)
    
    for course in courses:
        create_time = course.create_time.strftime('%Y-%m-%d %H:%M:%S') if course.create_time else 'Unknown'
        print(f"{str(course.id):<40} {course.name[:29]:<30} {create_time:<20}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='知识图谱维护工具 - 清空课程知识图谱',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有课程
  python clear_course_knowledge_graph.py --list
  
  # 查看课程知识图谱统计信息
  python clear_course_knowledge_graph.py --course-id <课程ID> --stats
  
  # 预览清理操作（不实际执行）
  python clear_course_knowledge_graph.py --course-id <课程ID> --dry-run
  
  # 执行清理操作
  python clear_course_knowledge_graph.py --course-id <课程ID> --execute
  
  # 强制执行（跳过确认）
  python clear_course_knowledge_graph.py --course-id <课程ID> --execute --force
        """
    )
    
    # 添加参数
    parser.add_argument('--list', action='store_true', help='列出所有可用的课程')
    parser.add_argument('--course-id', type=validate_course_id, help='要清理的课程ID')
    parser.add_argument('--stats', action='store_true', help='显示课程知识图谱统计信息')
    parser.add_argument('--dry-run', action='store_true', help='预览清理操作，不实际执行')
    parser.add_argument('--execute', action='store_true', help='执行清理操作')
    parser.add_argument('--force', action='store_true', help='强制执行，跳过确认提示')
    
    args = parser.parse_args()
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            # 列出课程
            if args.list:
                list_courses()
                return
            
            # 检查课程ID是否提供
            if not args.course_id:
                if not args.list:
                    print("错误: 请提供课程ID或使用 --list 查看可用课程")
                    parser.print_help()
                return
            
            # 验证课程存在
            course_info = get_course_info(args.course_id)
            if not course_info:
                print(f"错误: 课程 {args.course_id} 不存在")
                return
            
            print(f"课程信息:")
            print(f"  ID: {course_info['id']}")
            print(f"  名称: {course_info['name']}")
            print(f"  描述: {course_info['description']}")
            print(f"  创建时间: {course_info['create_time']}")
            
            # 显示统计信息
            if args.stats or args.dry_run or args.execute:
                stats = get_course_knowledge_graph_stats(args.course_id)
                print(f"\n知识图谱统计:")
                print(f"  视频数量: {stats['videos']}")
                print(f"  文档数量: {stats['documents']}")
                print(f"  关联知识点: {stats['unique_keywords']} 个")
                print(f"  视频-知识点关系: {stats['video_keyword_relations']} 条")
                print(f"  文档-知识点关系: {stats['document_keyword_relations']} 条")
                print(f"  知识点关系: {stats['keyword_relations']} 条")
                
                # 显示分类分布
                if stats['category_distribution']:
                    print(f"  知识点分类分布:")
                    for category, count in stats['category_distribution'].items():
                        category_name = {
                            'core_concept': '一级知识点',
                            'main_module': '二级知识点', 
                            'specific_point': '三级知识点'
                        }.get(category, category)
                        print(f"    {category_name}: {count} 个")
                
                if stats['keyword_relations'] == 0 and stats['unique_keywords'] > 0:
                    print(f"\n✅ 课程 {args.course_id} 的知识图谱结构已为空（仅有知识点但无关系）")
                elif stats['unique_keywords'] == 0:
                    print(f"\n✅ 课程 {args.course_id} 没有知识图谱数据需要清理")
                    return
            
            # 只显示统计信息
            if args.stats and not (args.dry_run or args.execute):
                return
            
            # 预览模式
            if args.dry_run:
                clear_course_knowledge_graph(args.course_id, dry_run=True)
                return
            
            # 执行清理
            if args.execute:
                # 安全确认
                if not args.force:
                    print(f"\n⚠️  警告: 即将清空课程 '{course_info['name']}' 的知识图谱结构!")
                    print("这个操作是不可逆的，将执行以下操作:")
                    print("  - 删除所有知识点关系")
                    print("  - 重置知识点分类为 'specific_point'")
                    print("\n保留的数据:")
                    print("  - 知识点本身")
                    print("  - 视频-知识点关联")
                    print("  - 文档-知识点关联")
                    
                    confirm = input("\n确认要继续吗? 请输入 'yes' 确认: ").strip().lower()
                    if confirm != 'yes':
                        print("操作已取消")
                        return
                
                # 执行清理
                deleted_counts = clear_course_knowledge_graph(args.course_id, dry_run=False)
                
                if deleted_counts:
                    print(f"\n清理统计:")
                    for key, count in deleted_counts.items():
                        print(f"  {key}: {count}")
                
            else:
                print("\n请指定操作: --stats (查看统计), --dry-run (预览), 或 --execute (执行)")
                
        except KeyboardInterrupt:
            print("\n\n操作被用户中断")
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
