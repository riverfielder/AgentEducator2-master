import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import sys

# 加载环境变量
load_dotenv()

uri = os.getenv('SQLALCHEMY_DATABASE_URI')
# 简单的脱敏打印
if uri:
    masked_uri = uri.replace(uri.split(':')[2].split('@')[0], '******') if '@' in uri and ':' in uri else uri
    print(f"正在尝试连接数据库: {masked_uri}")
else:
    print("错误: 未找到 SQLALCHEMY_DATABASE_URI 环境变量")
    sys.exit(1)

try:
    engine = create_engine(uri)
    with engine.connect() as connection:
        print("✅ 数据库连接建立成功!")
        
        # 1. 尝试获取数据库版本和主机名信息
        try:
            version = connection.execute(text("SELECT VERSION()")).fetchone()[0]
            print(f"数据库版本: {version}")
        except Exception:
            print("无法获取数据库版本")

        # 2. 检查 courses 表结构，确认排课字段是否存在
        print("\n正在检查 courses 表结构...")
        try:
            # 使用标准的 SQL 查询列信息
            result = connection.execute(text("SHOW COLUMNS FROM courses")).fetchall()
            columns = [col[0] for col in result]
            
            print(f"courses 表共有 {len(columns)} 个字段")
            
            new_fields = ['schedule_start_time', 'schedule_end_time']
            all_exist = True
            
            for field in new_fields:
                if field in columns:
                    print(f"✅ 字段 '{field}' 已存在")
                else:
                    print(f"❌ 字段 '{field}' 未找到")
                    all_exist = False
            
            if all_exist:
                print("\n🎉 验证成功: 远程数据库已包含最新的排课字段！")
            else:
                print("\n⚠️ 验证警告: 远程数据库缺少部分字段，请重新运行迁移脚本。")
                
        except Exception as e:
            print(f"无法查询表结构: {e}")

except Exception as e:
    print(f"\n❌ 连接失败: {e}")
    print("请检查网络连接、VPN状态或防火墙设置。")
