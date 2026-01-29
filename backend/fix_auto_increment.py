#!/usr/bin/env python3
"""
修复MySQL数据库中应该自增但没有设置AUTO_INCREMENT的字段
"""
import pymysql
import json
import os
from config.config import Config

def get_database_connection():
    """获取数据库连接"""
    try:
        # 从配置中获取数据库连接信息
        db_url = Config.SQLALCHEMY_DATABASE_URI
        
        # 解析MySQL连接URL
        # 格式: mysql+pymysql://username:password@host:port/database
        if db_url.startswith('mysql+pymysql://'):
            db_url = db_url.replace('mysql+pymysql://', '')
            
        # 分解连接字符串
        if '@' in db_url:
            auth_part, host_part = db_url.split('@')
            username, password = auth_part.split(':')
            
            if '/' in host_part:
                host_port, database = host_part.split('/')
            else:
                host_port = host_part
                database = 'wendao_platform'
                
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host = host_port
                port = 3306
        else:
            # 默认配置
            host = 'localhost'
            port = 3306
            username = 'root'
            password = ''
            database = 'wendao_platform'
        
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        print(f"成功连接到MySQL数据库: {host}:{port}/{database}")
        return connection
        
    except Exception as e:
        print(f"连接数据库失败: {e}")
        print("请检查config.py中的数据库配置")
        return None

def check_table_structure(cursor, table_name):
    """检查表结构"""
    print(f"\n检查表 {table_name} 的结构:")
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    
    id_column = None
    for column in columns:
        field, type_info, null, key, default, extra = column
        if field == 'id':
            id_column = column
            print(f"  ID字段: {field} {type_info} {extra}")
            break
    
    return id_column

def fix_auto_increment(cursor, table_name, max_id=None):
    """修复表的自增字段"""
    try:
        print(f"\n修复表 {table_name} 的自增字段...")
        
        # 如果没有提供max_id，查询当前最大ID
        if max_id is None:
            cursor.execute(f"SELECT MAX(id) FROM {table_name}")
            result = cursor.fetchone()
            max_id = result[0] if result[0] is not None else 0
        
        print(f"  当前最大ID: {max_id}")
        
        # 修改字段为自增
        alter_sql = f"ALTER TABLE {table_name} MODIFY COLUMN id INT AUTO_INCREMENT"
        cursor.execute(alter_sql)
        print(f"  ✓ 设置id字段为AUTO_INCREMENT")
        
        # 设置自增起始值
        if max_id > 0:
            auto_increment_sql = f"ALTER TABLE {table_name} AUTO_INCREMENT = {max_id + 1}"
            cursor.execute(auto_increment_sql)
            print(f"  ✓ 设置AUTO_INCREMENT起始值为 {max_id + 1}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 修复失败: {e}")
        return False

def main():
    """主函数"""
    print("=== MySQL自增字段修复脚本 ===")
    
    # 需要修复的表列表（只包含应该自增的表）
    tables_to_fix = [
        'video_keyframes',
        'video_vector_indices', 
        'task_logs'
    ]
    
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        print("\n1. 检查当前表结构...")
        for table_name in tables_to_fix:
            try:
                id_column = check_table_structure(cursor, table_name)
                if id_column:
                    field, type_info, null, key, default, extra = id_column
                    if 'auto_increment' not in extra.lower():
                        print(f"  ⚠️  表 {table_name} 的id字段未设置AUTO_INCREMENT")
                    else:
                        print(f"  ✓ 表 {table_name} 的id字段已正确设置AUTO_INCREMENT")
                else:
                    print(f"  ❌ 表 {table_name} 没有id字段")
            except Exception as e:
                print(f"  ❌ 检查表 {table_name} 失败: {e}")
        
        print("\n2. 开始修复...")
        success_count = 0
        
        for table_name in tables_to_fix:
            try:
                # 检查表是否存在
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if not cursor.fetchone():
                    print(f"  ⚠️  表 {table_name} 不存在，跳过")
                    continue
                
                # 检查是否已经是自增字段
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                create_sql = cursor.fetchone()[1]
                
                if 'AUTO_INCREMENT' in create_sql.upper() and '`id`' in create_sql:
                    print(f"  ✓ 表 {table_name} 已正确设置，跳过")
                    success_count += 1
                    continue
                
                # 修复自增字段
                if fix_auto_increment(cursor, table_name):
                    success_count += 1
                    
            except Exception as e:
                print(f"  ❌ 处理表 {table_name} 时出错: {e}")
        
        # 提交更改
        connection.commit()
        print(f"\n3. 修复完成! 成功处理 {success_count}/{len(tables_to_fix)} 个表")
        
        print("\n4. 验证修复结果...")
        for table_name in tables_to_fix:
            try:
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                result = cursor.fetchone()
                if result:
                    create_sql = result[1]
                    if 'AUTO_INCREMENT' in create_sql.upper():
                        print(f"  ✓ {table_name}: AUTO_INCREMENT 已设置")
                    else:
                        print(f"  ❌ {table_name}: AUTO_INCREMENT 未设置")
                else:
                    print(f"  ⚠️  {table_name}: 表不存在")
            except Exception as e:
                print(f"  ❌ 验证表 {table_name} 失败: {e}")
        
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
        print("\n数据库连接已关闭")

if __name__ == '__main__':
    main()
