#!/usr/bin/env python3
"""
手动更新课程知识点统计的脚本
"""

from app import create_app
from models.models import db, Course, Keyword, CourseKeyword, VideoKeyword, Video
from sqlalchemy import func
from datetime import datetime

app = create_app()

with app.app_context():
    print('=== 手动更新课程知识点统计 ===', flush=True)
    
    # 获取所有课程
    courses = Course.query.all()
    print(f'发现 {len(courses)} 个课程', flush=True)
    
    for course in courses:
        print(f'\n处理课程: {course.name} (ID: {course.id})')
        
        # 计算每个知识点在课程中的统计信息
        keyword_stats = db.session.query(
            Keyword.id,
            func.count(VideoKeyword.video_id).label('video_count'),
            func.avg(VideoKeyword.weight).label('avg_weight')
        ).join(VideoKeyword).join(Video).filter(
            Video.course_id == course.id
        ).group_by(Keyword.id).all()
        
        print(f'  该课程关联的知识点数: {len(keyword_stats)}')
        
        updated_count = 0
        for keyword_id, video_count, avg_weight in keyword_stats:
            # 检查课程知识点关系是否已存在
            existing_course_keyword = CourseKeyword.query.filter_by(
                course_id=course.id,
                keyword_id=keyword_id
            ).first()
            
            if existing_course_keyword:
                existing_course_keyword.video_count = video_count
                existing_course_keyword.avg_weight = float(avg_weight) if avg_weight else 0.0
                existing_course_keyword.update_time = datetime.now()
                print(f'  更新知识点关系: {keyword_id} (视频数: {video_count}, 平均权重: {avg_weight:.3f})')
            else:
                course_keyword = CourseKeyword(
                    course_id=course.id,
                    keyword_id=keyword_id,
                    video_count=video_count,
                    avg_weight=float(avg_weight) if avg_weight else 0.0
                )
                db.session.add(course_keyword)
                print(f'  创建知识点关系: {keyword_id} (视频数: {video_count}, 平均权重: {avg_weight:.3f})')
            
            updated_count += 1
        
        try:
            db.session.commit()
            print(f'  ✅ 课程 {course.name} 更新完成，共处理 {updated_count} 个知识点')
        except Exception as e:
            db.session.rollback()
            print(f'  ❌ 课程 {course.name} 更新失败: {e}')
    
    # 验证结果
    print('\n=== 验证结果 ===')
    total_course_keywords = CourseKeyword.query.count()
    print(f'总课程知识点关系数: {total_course_keywords}')
    
    for course in courses:
        course_keyword_count = CourseKeyword.query.filter_by(course_id=course.id).count()
        print(f'课程 "{course.name}": {course_keyword_count} 个知识点')
