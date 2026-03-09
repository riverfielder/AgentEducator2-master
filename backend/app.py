from flask import Flask, send_from_directory
from dotenv import load_dotenv # type: ignore
load_dotenv() # Load environment variables before importing config

from models.models import db  # Import db from models
import os
# 导入 OpenMP 冲突修复
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from config import Config,WinstarConfig
from flask_cors import CORS
import atexit
import logging
from logging.handlers import RotatingFileHandler
# 导入新的路由模块
from routes.task_logs import task_logs_bp

def create_app(config_name='development'):
    app = Flask(__name__)
    app.url_map.strict_slashes = False  
    if os.getenv('IS_WINSTAR') == 'True':
        print("使用生产环境配置")
        app.config.from_object(WinstarConfig)
        app.debug=False
    else:
        print("使用开发环境配置")
        app.config.from_object(Config)

    
    # Initialize the database with the app
    db.init_app(app)

    # 配置 CORS
    CORS(app, 
         origins=["http://localhost:5173", "https://winstar.snakekiss.com","https://edu.homeworkkun.top"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
         expose_headers=["*"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    # 允许所有OPTIONS请求直接返回200，解决CORS预检问题
    @app.after_request
    def after_request_func(response):
        if response.status_code == 405 and response.headers.get('Allow') and 'OPTIONS' in response.headers.get('Allow'):
            response.status_code = 200
        return response
    
    # Create all database tables
    with app.app_context():
        db.create_all()
    
    # 注册蓝图
    from routes.user import user_bp
    from routes.course import course_bp
    from routes.upload import upload_bp
    from routes.video import video_bp
    from routes.summary import summary_bp
    from routes.qa_api import qa_bp
    from routes.student import student_bp
    from routes.student_management import student_management_bp    
    from routes.chat_history import chat_history_bp
    from routes.knowledge_graph import knowledge_graph_bp
    from routes.statistics import statistics_bp
    from routes.teacher_dashboard import teacher_dashboard_bp
    from routes.teacher_assistant import teacher_assistant_bp
    from routes.chapter import chapter_bp
    from routes.document import document_bp
    from routes.category import category_bp
    from routes.config_management import config_bp
    from routes.assignment import assignment_bp  # 添加作业路由导入
    from routes.knowledge_point import knowledge_point_bp  # 添加知识点路由导入
    from routes.question_bank import bp as question_bank_bp  # 导入题库蓝图
    from routes.global_search import global_search_bp  # 导入全局搜索蓝图
    from routes.personalized_recommendation import personalized_recommendation_bp  # 导入个性化推荐蓝图
    from routes.training import training_bp # 导入动态专项训练卷蓝图

    
    # 添加静态文件路由，支持环境变量配置上传路径
    def create_static_route(route_path, folder_type, default_folder):
        """创建静态文件路由的辅助函数"""
        from config.config import Config
        folder_name = Config.get_upload_folder(folder_type)
        base_path = Config.get_upload_base_path()
        full_folder_path = os.path.join(base_path, folder_name)
        
        def serve_static(filename):
            return send_from_directory(full_folder_path, filename)
        
        
        
        # 使用route_path作为端点名称的一部分，确保唯一性
        endpoint_name = f'serve_{route_path.strip("/").replace("/", "_")}'
        
        # 注册路由
        app.add_url_rule(f'/{folder_name}/<path:filename>', 
                        endpoint_name, 
                        serve_static)
    if not os.getenv('IS_WINSTAR') == 'True':
        # 创建各类文件的静态路由
        create_static_route('/temp_img/', 'image', 'temp_img')
        create_static_route('/temp_video/', 'video', 'temp_video')
        create_static_route('/temp_docs/', 'document', 'temp_docs')
        create_static_route('/temp_avatars/', 'avatar', 'temp_avatars')

        # 注意：文档静态路由已统一到通用配置系统中 (/temp_docs/)

    app.register_blueprint(user_bp, url_prefix='/api/auth')  # 认证相关接口
    app.register_blueprint(course_bp, url_prefix='/api/courses')  # 课程相关接口(复数形式)
    app.register_blueprint(upload_bp, url_prefix='/api/uploads')  # 上传相关接口(复数形式)
    app.register_blueprint(video_bp, url_prefix='/api/videos')  # 视频相关接口(复数形式)
    app.register_blueprint(summary_bp, url_prefix='/api/summaries')  # 总结相关接口(复数形式)
    app.register_blueprint(qa_bp, url_prefix='/api/qa')  # 问答相关接口
    app.register_blueprint(student_bp, url_prefix='/api/students')  # 学生相关接口(复数形式)
    app.register_blueprint(task_logs_bp, url_prefix='/api/task_logs')  # 任务日志相关接口
    app.register_blueprint(student_management_bp, url_prefix='/api/student_management')  # 学生管理相关接口
    app.register_blueprint(chat_history_bp, url_prefix='/api/chat_history')  # 聊天历史相关接口
    app.register_blueprint(knowledge_graph_bp)  # 知识图谱相关接口
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')  # 统计数据相关接口
    app.register_blueprint(teacher_dashboard_bp, url_prefix='/api/teacher')  # 教师仪表板相关接口
    app.register_blueprint(teacher_assistant_bp)  # 教师智能助手相关接口
    app.register_blueprint(config_bp, url_prefix='/api/config')  # 配置管理相关接口
    app.register_blueprint(chapter_bp, url_prefix='/api/chapters')  # 章节管理相关接口（直接使用，路由中已包含完整路径）
    app.register_blueprint(document_bp, url_prefix='/api/documents')  # 文档管理相关接口（直接使用，路由中已包含完整路径）
    app.register_blueprint(category_bp, url_prefix='/api/category')
    app.register_blueprint(assignment_bp, url_prefix='/api/assignments')  # 添加作业相关接口
    app.register_blueprint(knowledge_point_bp, url_prefix='/api/knowledge-points')  # 添加知识点相关接口
    app.register_blueprint(question_bank_bp)  # 注册题库相关接口
    app.register_blueprint(global_search_bp)  # 注册全局搜索相关接口
    app.register_blueprint(personalized_recommendation_bp)  # 注册个性化推荐相关接口
    app.register_blueprint(training_bp, url_prefix='/api/training') # 注册专项训练卷相关接口


    # 添加静态文件路由，用于访问上传的图片# 初始化视频处理线程池
    from utils.video_processing_pool import video_processing_pool
    
    # 初始化知识图谱处理线程池
    from utils.knowledge_graph_processing_pool import knowledge_graph_processing_pool
    
    # 注册应用关闭时的清理函数
    atexit.register(lambda: video_processing_pool.shutdown(wait=True))
    atexit.register(lambda: knowledge_graph_processing_pool.shutdown(wait=True))
    
    # 设置app的全局线程信息字典
    app.PROCESSING_THREADS = {}
    # 启动前查找所有软删除的视频并清理相关数据
    # 注意：这里不能直接执行数据库查询，因为还在应用初始化阶段
    # 数据库查询需要在应用上下文中执行

    
    return app

if __name__ == '__main__':
    app = create_app()  
    # 配置日志记录到本地文件

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    app.run(host='0.0.0.0', port=5000)  # 修改运行参数

