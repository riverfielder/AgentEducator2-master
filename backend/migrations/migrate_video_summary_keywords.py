#!/usr/bin/env python3
"""
将VideoSummary表中的知识点数据迁移到新的知识点数据库结构

迁移步骤：
1. 从VideoSummary.keywords字段提取知识点（逗号分隔）
2. 创建或更新Keyword表记录
3. 建立VideoKeyword关系
4. 根据VideoKeyword统计生成CourseKeyword关系
5. 可选：备份原始数据后清理VideoSummary.keywords字段

运行方式：
python migrate_video_summary_keywords.py [--dry-run] [--backup] [--clear-old]
"""

import sys
import os
import argparse
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.models import (
    db, VideoSummary, Video, Course, Keyword, 
    VideoKeyword, CourseKeyword
)

class VideoSummaryKeywordMigrator:
    """VideoSummary知识点迁移器"""
    
    def __init__(self, dry_run=False, backup=False):
        self.dry_run = dry_run
        self.backup = backup
        self.stats = {
            'processed_summaries': 0,
            'extracted_keywords': 0,
            'created_keywords': 0,
            'updated_keywords': 0,
            'created_video_relations': 0,
            'created_course_relations': 0,
            'errors': []
        }
    
    def migrate(self):
        """执行迁移"""
        #清空keyword表
        if not self.dry_run:
            print("清空Keyword表...")
            Keyword.query.delete()
            db.session.commit()
        print("开始VideoSummary知识点迁移...")
        print(f"模式: {'DRY RUN' if self.dry_run else 'ACTUAL RUN'}")
        
        # 备份数据
        if self.backup:
            self._backup_data()
        
        # 获取所有有知识点的VideoSummary记录
        summaries_with_keywords = VideoSummary.query.filter(
            VideoSummary.keywords.isnot(None),
            VideoSummary.keywords != '',
            VideoSummary.keywords != 'null'
        ).all()
        
        print(f"找到 {len(summaries_with_keywords)} 个包含知识点的视频摘要")
        
        if not summaries_with_keywords:
            print("没有需要迁移的数据")
            return
        
        # 处理每个摘要
        for summary in summaries_with_keywords:
            try:
                self._process_summary(summary)
                self.stats['processed_summaries'] += 1
            except Exception as e:
                error_msg = f"处理视频摘要 {summary.id} 时出错: {str(e)}"
                self.stats['errors'].append(error_msg)
                print(f"错误: {error_msg}")
        
        # 生成课程知识点统计
        self._generate_course_keywords()
        
        # 提交更改
        if not self.dry_run:
            try:
                db.session.commit()
                print("迁移成功完成并已提交到数据库")
            except Exception as e:
                db.session.rollback()
                print(f"提交失败，已回滚: {str(e)}")
                return False
        else:
            db.session.rollback()
            print("DRY RUN 完成，未提交任何更改")
        
        # 打印统计信息
        self._print_stats()
        return True
    
    def _backup_data(self):
        """备份原始数据"""
        backup_file = f"video_summary_keywords_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join('instance', backup_file)
        
        print(f"备份原始数据到 {backup_path}")
        
        backup_data = []
        summaries = VideoSummary.query.filter(
            VideoSummary.keywords.isnot(None),
            VideoSummary.keywords != ''
        ).all()
        
        for summary in summaries:
            backup_data.append({
                'id': str(summary.id),
                'video_id': str(summary.video_id),
                'keywords': summary.keywords,
                'generate_time': summary.generate_time.isoformat() if summary.generate_time else None
            })
        
        os.makedirs('instance', exist_ok=True)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"备份完成，共备份 {len(backup_data)} 条记录")
    
    def _process_summary(self, summary):
        """处理单个视频摘要的知识点"""
        video = Video.query.get(summary.video_id)
        if not video:
            raise Exception(f"视频 {summary.video_id} 不存在")
        
        # 解析知识点
        keywords_str = summary.keywords.strip()
        if not keywords_str:
            return
        
        # 处理不同的分隔符
        keywords_list = []
        for separator in [',', '，', ';', '；']:
            if separator in keywords_str:
                keywords_list = [kw.strip() for kw in keywords_str.split(separator)]
                break
        
        if not keywords_list:
            # 如果没有分隔符，整个字符串作为一个知识点
            keywords_list = [keywords_str]
        
        # 过滤空知识点
        keywords_list = [kw for kw in keywords_list if kw]
        
        if not keywords_list:
            return
        
        print(f"  处理视频 {video.title} 的知识点: {keywords_list}")
        self.stats['extracted_keywords'] += len(keywords_list)
        
        # 为每个知识点创建或更新记录
        for keyword_name in keywords_list:
            self._process_keyword(keyword_name, video)
    
    def _process_keyword(self, keyword_name, video):
        """处理单个知识点"""
        # 查找或创建知识点
        keyword = Keyword.query.filter_by(name=keyword_name).first()
        
        if not keyword:
            # 创建新知识点（默认分类为specific_point）
            keyword = Keyword(
                name=keyword_name,
                category='specific_point',  # 从VideoSummary迁移的知识点默认为三级知识点
                description=f"从视频摘要迁移的知识点: {keyword_name}"
            )
            if not self.dry_run:
                db.session.add(keyword)
                db.session.flush()  # 获取ID
            self.stats['created_keywords'] += 1
            print(f"    创建新知识点: {keyword_name}")
        else:
            # 更新现有知识点（如果描述为空，补充描述）
            if not keyword.description:
                keyword.description = f"知识点: {keyword_name}"
                keyword.update_time = datetime.now()
            self.stats['updated_keywords'] += 1
            print(f"    使用现有知识点: {keyword_name}")
        
        # 创建视频-知识点关系（如果不存在）
        if not self.dry_run or True:  # DRY RUN时也检查关系
            existing_relation = VideoKeyword.query.filter_by(
                video_id=video.id,
                keyword_id=keyword.id
            ).first()
            
            if not existing_relation:
                video_keyword = VideoKeyword(
                    video_id=video.id,
                    keyword_id=keyword.id,
                    weight=1.0  # 默认权重
                )
                if not self.dry_run:
                    db.session.add(video_keyword)
                self.stats['created_video_relations'] += 1
                print(f"    创建视频-知识点关系")
            else:
                print(f"    视频-知识点关系已存在")
    
    def _generate_course_keywords(self):
        """根据VideoKeyword关系生成CourseKeyword统计"""
        print("生成课程知识点统计...")
        
        # 获取所有课程
        courses = Course.query.filter_by(is_deleted=False).all()
        
        for course in courses:
            print(f"  处理课程: {course.name}")
            
            # 统计该课程下每个知识点的使用情况
            keyword_stats = db.session.query(
                Keyword.id,
                db.func.count(VideoKeyword.id).label('video_count'),
                db.func.avg(VideoKeyword.weight).label('avg_weight')
            ).join(VideoKeyword).join(Video).filter(
                Video.course_id == course.id,
                Video.is_deleted == False
            ).group_by(Keyword.id).all()
            
            for keyword_id, video_count, avg_weight in keyword_stats:
                # 检查课程知识点关系是否已存在
                existing_course_keyword = CourseKeyword.query.filter_by(
                    course_id=course.id,
                    keyword_id=keyword_id
                ).first()
                
                if not existing_course_keyword:
                    course_keyword = CourseKeyword(
                        course_id=course.id,
                        keyword_id=keyword_id,
                        video_count=video_count,
                        avg_weight=float(avg_weight) if avg_weight else 0.0
                    )
                    if not self.dry_run:
                        db.session.add(course_keyword)
                    self.stats['created_course_relations'] += 1
                    print(f"    创建课程知识点关系: 知识点ID {keyword_id}")
                else:
                    # 更新统计信息
                    existing_course_keyword.video_count = video_count
                    existing_course_keyword.avg_weight = float(avg_weight) if avg_weight else 0.0
                    existing_course_keyword.update_time = datetime.now()
                    print(f"    更新课程知识点关系: 知识点ID {keyword_id}")
    
    def _print_stats(self):
        """打印迁移统计信息"""
        print("\n=== 迁移统计 ===")
        print(f"处理的视频摘要数: {self.stats['processed_summaries']}")
        print(f"提取的知识点数: {self.stats['extracted_keywords']}")
        print(f"创建的知识点数: {self.stats['created_keywords']}")
        print(f"更新的知识点数: {self.stats['updated_keywords']}")
        print(f"创建的视频知识点关系数: {self.stats['created_video_relations']}")
        print(f"创建的课程知识点关系数: {self.stats['created_course_relations']}")
        
        if self.stats['errors']:
            print(f"\n错误数: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  - {error}")
    
    def clear_old_keywords(self):
        """清理VideoSummary表中的知识点字段"""
        if self.dry_run:
            print("DRY RUN: 不会清理原始知识点字段")
            return
        
        print("清理VideoSummary表中的知识点字段...")
        
        # 将keywords字段设置为NULL
        summaries = VideoSummary.query.filter(
            VideoSummary.keywords.isnot(None),
            VideoSummary.keywords != ''
        ).all()
        
        for summary in summaries:
            summary.keywords = None
        
        try:
            db.session.commit()
            print(f"已清理 {len(summaries)} 条记录的知识点字段")
        except Exception as e:
            db.session.rollback()
            print(f"清理失败: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='迁移VideoSummary知识点到新数据库结构')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不实际修改数据库')
    parser.add_argument('--backup', action='store_true', help='备份原始数据')
    parser.add_argument('--clear-old', action='store_true', help='清理VideoSummary表中的知识点字段')
    
    args = parser.parse_args()
    
    # 创建Flask应用
    app = create_app()
    
    with app.app_context():
        migrator = VideoSummaryKeywordMigrator(
            dry_run=args.dry_run,
            backup=args.backup
        )
        
        # 执行迁移
        success = migrator.migrate()
        
        if success and args.clear_old:
            confirm = input("确认要清理VideoSummary表中的知识点字段吗？(y/N): ")
            if confirm.lower() == 'y':
                migrator.clear_old_keywords()

if __name__ == '__main__':
    main()
