"""
聊天历史功能初始化脚本
运行此脚本可以完成所有必要的数据库设置
"""

from migrations.chat_history_tables import run_migration
from migrations.sqlite_triggers import create_triggers

def setup_chat_history():
    """设置聊天历史功能所需的所有数据库结构"""
    print("正在创建聊天历史相关表...")
    run_migration()
    
    print("正在创建SQLite触发器...")
    create_triggers()
    
    print("聊天历史功能初始化完成！")

if __name__ == "__main__":
    setup_chat_history() 