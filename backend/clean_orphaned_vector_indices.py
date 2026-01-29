#!/usr/bin/env python3
"""
清理孤儿向量索引脚本
删除所有不属于任何有效视频的向量索引数据和文件
包括：数据库记录、文件系统中的索引文件和目录
"""

import os
import sys
import shutil
from datetime import datetime
from sqlalchemy import text

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
app = create_app()
from models.models import (
    db, Video, VideoVectorIndex, Course
)

def get_orphaned_vector_indices():
    """获取所有孤儿向量索引"""
    orphaned_indices = []
    
    print("正在查找孤儿向量索引...")
    
    # 1. 查找video_id为NULL的向量索引
    null_video_indices = VideoVectorIndex.query.filter(VideoVectorIndex.video_id.is_(None)).all()
    if null_video_indices:
        print(f"找到 {len(null_video_indices)} 个video_id为NULL的向量索引")
    orphaned_indices.extend(null_video_indices)
    
    # 2. 查找video_id指向不存在视频的向量索引
    invalid_video_indices = db.session.query(VideoVectorIndex).outerjoin(
        Video, VideoVectorIndex.video_id == Video.id
    ).filter(
        VideoVectorIndex.video_id.isnot(None),
        Video.id.is_(None)
    ).all()
    if invalid_video_indices:
        print(f"找到 {len(invalid_video_indices)} 个video_id指向不存在视频的向量索引")
    orphaned_indices.extend(invalid_video_indices)
    
    # 3. 查找video_id指向已删除视频的向量索引
    deleted_video_indices = db.session.query(VideoVectorIndex).join(
        Video, VideoVectorIndex.video_id == Video.id
    ).filter(
        Video.is_deleted == True
    ).all()
    if deleted_video_indices:
        print(f"找到 {len(deleted_video_indices)} 个video_id指向已删除视频的向量索引")
    orphaned_indices.extend(deleted_video_indices)
    
    # 4. 查找video存在但课程不存在或已删除的向量索引
    orphaned_by_course_indices = db.session.query(VideoVectorIndex).join(
        Video, VideoVectorIndex.video_id == Video.id
    ).outerjoin(
        Course, Video.course_id == Course.id
    ).filter(
        Video.is_deleted == False,  # 只考虑未删除的视频
        db.or_(
            Video.course_id.is_(None),  # 课程ID为空
            Course.id.is_(None),        # 课程不存在
            Course.is_deleted == True   # 课程已删除
        )
    ).all()
    if orphaned_by_course_indices:
        print(f"找到 {len(orphaned_by_course_indices)} 个关联视频无有效课程的向量索引")
    orphaned_indices.extend(orphaned_by_course_indices)
    
    return orphaned_indices

def get_orphaned_vector_files():
    """获取文件系统中的孤儿向量索引文件"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    vector_indices_dir = os.path.join(backend_dir, 'vector_indices')
    
    if not os.path.exists(vector_indices_dir):
        print("向量索引目录不存在")
        return []
    
    # 获取所有有效的video_id（未删除且课程未删除的视频）
    valid_video_ids = set()
    valid_videos = db.session.query(Video).join(Course).filter(
        Video.is_deleted == False,
        Course.is_deleted == False
    ).all()
    for video in valid_videos:
        valid_video_ids.add(str(video.id))
    
    print(f"有效视频数量: {len(valid_video_ids)}")
    
    # 检查文件系统中的向量索引目录
    orphaned_items = []
    
    for item in os.listdir(vector_indices_dir):
        item_path = os.path.join(vector_indices_dir, item)
        
        if os.path.isdir(item_path):
            # 检查是否是video_开头的目录
            if item.startswith('video_'):
                video_id = item[6:]  # 去掉'video_'前缀
                if video_id not in valid_video_ids:
                    orphaned_items.append(item_path)
            else:
                # 其他不符合命名规范的目录
                orphaned_items.append(item_path)
        elif os.path.isfile(item_path):
            # 文件系统中不应该有单独的文件，都应该在video_目录中
            orphaned_items.append(item_path)
    
    if orphaned_items:
        print(f"找到 {len(orphaned_items)} 个孤儿向量索引文件/目录")
    
    return orphaned_items

def get_directory_size(directory):
    """计算目录大小"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except Exception as e:
        print(f"计算目录大小时出错 {directory}: {e}")
    return total_size

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    elif size_bytes > 1024 * 1024 * 1024:  # GB
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    elif size_bytes > 1024 * 1024:  # MB
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes > 1024:  # KB
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"

def clean_database_records(orphaned_indices, dry_run=True):
    """清理数据库中的孤儿向量索引记录"""
    if not orphaned_indices:
        print("没有需要清理的数据库记录")
        return 0
    
    print(f"\n{'[预览模式]' if dry_run else '[执行模式]'} 清理数据库记录...")
    
    cleaned_count = 0
    for index in orphaned_indices:
        try:
            if dry_run:
                print(f"  [预览] 将删除索引记录: ID={index.id}, video_id={index.video_id}, path={index.index_path}")
            else:
                print(f"  正在删除索引记录: ID={index.id}, video_id={index.video_id}")
                db.session.delete(index)
                cleaned_count += 1
        except Exception as e:
            print(f"  删除索引记录失败 {index.id}: {e}")
    
    if not dry_run:
        try:
            db.session.commit()
            print(f"✅ 成功删除 {cleaned_count} 条数据库记录")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 提交数据库更改失败: {e}")
            cleaned_count = 0
    
    return cleaned_count

def clean_vector_files(orphaned_files, dry_run=True):
    """清理文件系统中的孤儿向量索引文件"""
    if not orphaned_files:
        print("没有需要清理的文件")
        return 0, 0
    
    print(f"\n{'[预览模式]' if dry_run else '[执行模式]'} 清理文件系统...")
    
    cleaned_count = 0
    total_size_freed = 0
    
    for file_path in orphaned_files:
        try:
            # 计算文件/目录大小
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    size = get_directory_size(file_path)
                    item_type = "目录"
                else:
                    size = os.path.getsize(file_path)
                    item_type = "文件"
                
                if dry_run:
                    print(f"  [预览] 将删除{item_type}: {file_path} ({format_size(size)})")
                    total_size_freed += size
                else:
                    print(f"  正在删除{item_type}: {file_path} ({format_size(size)})")
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    total_size_freed += size
                    cleaned_count += 1
            else:
                print(f"  ⚠️  文件不存在，跳过: {file_path}")
                
        except Exception as e:
            print(f"  ❌ 删除失败 {file_path}: {e}")
    
    if not dry_run and cleaned_count > 0:
        print(f"✅ 成功删除 {cleaned_count} 个文件/目录，释放空间 {format_size(total_size_freed)}")
    
    return cleaned_count, total_size_freed

def clean_missing_file_records(dry_run=True):
    """清理数据库中存在但文件不存在的索引记录"""
    print(f"\n{'[预览模式]' if dry_run else '[执行模式]'} 检查并清理数据库中的无效文件路径记录...")
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    all_indices = VideoVectorIndex.query.all()
    missing_file_records = []
    
    for index in all_indices:
        if index.index_path:
            # 构建完整路径
            if index.index_path.startswith('/') or index.index_path.startswith('\\'):
                full_path = os.path.join(backend_dir, index.index_path.lstrip('/\\'))
            else:
                full_path = os.path.join(backend_dir, index.index_path)
            
            if not os.path.exists(full_path):
                missing_file_records.append(index)
        else:
            # 索引路径为空的记录也可以考虑清理
            missing_file_records.append(index)
    
    if not missing_file_records:
        print("没有发现文件路径无效的索引记录")
        return 0
    
    print(f"发现 {len(missing_file_records)} 个文件路径无效的索引记录")
    
    cleaned_count = 0
    for index in missing_file_records:
        try:
            if dry_run:
                print(f"  [预览] 将删除无效记录: ID={index.id}, video_id={index.video_id}, path={index.index_path or 'NULL'}")
            else:
                print(f"  正在删除无效记录: ID={index.id}, video_id={index.video_id}")
                db.session.delete(index)
                cleaned_count += 1
        except Exception as e:
            print(f"  删除记录失败 {index.id}: {e}")
    
    if not dry_run:
        try:
            db.session.commit()
            print(f"✅ 成功删除 {cleaned_count} 条无效记录")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 提交数据库更改失败: {e}")
            cleaned_count = 0
    
    return cleaned_count

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='清理孤儿向量索引数据')
    parser.add_argument('--execute', action='store_true', help='执行清理操作（默认为预览模式）')
    parser.add_argument('--database-only', action='store_true', help='只清理数据库记录')
    parser.add_argument('--files-only', action='store_true', help='只清理文件系统')
    parser.add_argument('--clean-missing', action='store_true', help='同时清理文件路径无效的记录')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    print("=" * 60)
    print("孤儿向量索引清理工具")
    print(f"运行模式: {'执行清理' if not dry_run else '预览模式'}")
    print(f"清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if dry_run:
        print("⚠️  当前为预览模式，不会实际删除任何数据")
        print("⚠️  要执行实际清理，请使用 --execute 参数")
        print("")
    
    with app.app_context():
        try:
            total_db_cleaned = 0
            total_files_cleaned = 0
            total_size_freed = 0
            
            # 清理数据库中的孤儿索引记录
            if not args.files_only:
                print("1. 查找并清理数据库中的孤儿向量索引记录...")
                print("-" * 40)
                
                orphaned_indices = get_orphaned_vector_indices()
                
                if orphaned_indices:
                    db_cleaned = clean_database_records(orphaned_indices, dry_run)
                    total_db_cleaned += db_cleaned
                else:
                    print("✅ 没有发现孤儿向量索引记录")
            
            # 清理文件系统中的孤儿文件
            if not args.database_only:
                print("\n2. 查找并清理文件系统中的孤儿向量索引文件...")
                print("-" * 40)
                
                orphaned_files = get_orphaned_vector_files()
                
                if orphaned_files:
                    files_cleaned, size_freed = clean_vector_files(orphaned_files, dry_run)
                    total_files_cleaned += files_cleaned
                    total_size_freed += size_freed
                else:
                    print("✅ 没有发现孤儿向量索引文件")
            
            # 清理文件路径无效的记录
            if args.clean_missing and not args.files_only:
                print("\n3. 清理文件路径无效的索引记录...")
                print("-" * 40)
                
                missing_cleaned = clean_missing_file_records(dry_run)
                total_db_cleaned += missing_cleaned
            
            # 总结
            print("\n" + "=" * 60)
            print("清理总结:")
            
            if dry_run:
                print("🔍 预览结果:")
                if total_db_cleaned > 0 or len(get_orphaned_vector_indices()) > 0:
                    print(f"  - 将清理数据库记录: {len(get_orphaned_vector_indices())} 条")
                if total_files_cleaned > 0 or len(get_orphaned_vector_files()) > 0:
                    print(f"  - 将清理文件/目录: {len(get_orphaned_vector_files())} 个")
                    print(f"  - 将释放存储空间: {format_size(total_size_freed)}")
                print("\n要执行实际清理，请使用: python clean_orphaned_vector_indices.py --execute")
            else:
                print("✅ 执行结果:")
                if total_db_cleaned > 0:
                    print(f"  - 已清理数据库记录: {total_db_cleaned} 条")
                if total_files_cleaned > 0:
                    print(f"  - 已清理文件/目录: {total_files_cleaned} 个")
                    print(f"  - 已释放存储空间: {format_size(total_size_freed)}")
                
                if total_db_cleaned == 0 and total_files_cleaned == 0:
                    print("  - 没有清理任何数据，系统已是干净状态")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"清理过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.session.close()

if __name__ == "__main__":
    main()
