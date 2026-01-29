"""
运行数据库迁移脚本
"""
from flask import Flask
from models.models import db
from migrations.convert_ids_to_uuid import convert_video_ids

app = Flask(__name__)
# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mysql_jZQHwE@localhost:3307/wendao_platform'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

with app.app_context():
    # 执行迁移
    create_table()

print("数据库迁移完成")
