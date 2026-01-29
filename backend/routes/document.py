from flask import Blueprint, request, jsonify, current_app
from models.models import db, Document, Course, DocumentProcessingTask, Users, DocumentKeyword, DocumentVectorIndex, DocumentSegment, DocumentSummary, TaskLog
from utils.auth import token_required, is_teacher_or_admin
from utils.file_util import save_file, allowed_document_file
from utils.result import Result
import os
import uuid
import os
from datetime import datetime
import mimetypes

document_bp = Blueprint('document', __name__)

# 注意：文件类型检查已移至 utils.file_util.py 统一管理

@document_bp.route('/all', methods=['GET'])
@token_required
def get_all_documents():
    """获取当前用户的所有文档"""
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        
        # 检查权限
        if not is_teacher_or_admin(user_id):
            return jsonify({
                'code': 403,
                'message': '权限不足'
            }), 403
        
        # 将字符串UUID转换为UUID对象（如果需要）
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return jsonify({
                    'code': 400,
                    'message': '用户ID格式不正确'
                }), 400
        
        # 查询用户的课程
        user_courses = Course.query.filter_by(
            teacher_id=user_id,
            is_deleted=False
        ).all()
        
        course_ids = [course.id for course in user_courses]
        
        # 获取这些课程的所有文档
        documents = Document.query.filter(
            Document.course_id.in_(course_ids),
            Document.is_deleted == False
        ).order_by(Document.upload_time.desc()).all()
        
        # 获取文档处理状态
        document_ids = [doc.id for doc in documents]
        processing_status_map = {}
        if document_ids:
            # 查询每个文档的最新处理任务状态
            latest_tasks = db.session.query(DocumentProcessingTask.document_id, DocumentProcessingTask.status)\
                .filter(DocumentProcessingTask.document_id.in_(document_ids))\
                .order_by(DocumentProcessingTask.document_id, DocumentProcessingTask.start_time.desc())\
                .all()
            
            # 获取每个文档的最新状态
            for document_id, status in latest_tasks:
                if document_id not in processing_status_map:
                    processing_status_map[document_id] = status
        
        document_list = []
        for document in documents:
            doc_dict = document.to_dict()
            # 覆盖处理状态为最新的任务状态
            doc_dict['processingStatus'] = processing_status_map.get(document.id, 'unprocessed')
            document_list.append(doc_dict)
        
        return jsonify({
            'code': 200,
            'message': '获取文档列表成功',
            'data': {
                'list': document_list,
                'total': len(document_list)
            }
        })
        
    except Exception as e:
        print(f"获取所有文档列表错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<document_id>/segments', methods=['GET'])
@token_required
def get_document_segments(document_id):
    """获取文档分段列表"""
    try:
        from models.models import DocumentSegment
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        # 获取分段列表
        segments = DocumentSegment.query.filter_by(
            document_id=document_id
        ).order_by(DocumentSegment.segment_number).all()
        
        segment_list = [segment.to_dict() for segment in segments]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'list': segment_list,
                'total': len(segment_list)
            }
        })
        
    except Exception as e:
        print(f"获取文档分段列表错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<document_id>/segments/<int:segment_number>', methods=['GET'])
@token_required
def get_document_segment(document_id, segment_number):
    """获取特定分段内容"""
    try:
        from models.models import DocumentSegment
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        # 查找特定分段
        segment = DocumentSegment.query.filter_by(
            document_id=document_id,
            segment_number=segment_number
        ).first()
        
        if not segment:
            return jsonify({
                'code': 404,
                'message': '分段不存在'
            }), 404
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': segment.to_dict()
        })
        
    except Exception as e:
        print(f"获取文档分段错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<course_id>', methods=['GET'])
@token_required
def get_course_documents(course_id):
    """获取课程的所有文档"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'message': '课程不存在'
            }), 404
        
        # 获取文档列表
        documents = Document.query.filter_by(
            course_id=course_id, 
            is_deleted=False
        ).order_by(Document.upload_time.desc()).all()
        
        # 获取文档处理状态
        document_ids = [doc.id for doc in documents]
        processing_status_map = {}
        if document_ids:
            # 查询每个文档的最新处理任务状态
            latest_tasks = db.session.query(DocumentProcessingTask.document_id, DocumentProcessingTask.status)\
                .filter(DocumentProcessingTask.document_id.in_(document_ids))\
                .order_by(DocumentProcessingTask.document_id, DocumentProcessingTask.start_time.desc())\
                .all()
            
            # 获取每个文档的最新状态
            for document_id, status in latest_tasks:
                if document_id not in processing_status_map:
                    processing_status_map[document_id] = status
        
        document_list = []
        for document in documents:
            doc_dict = document.to_dict()
            # 覆盖处理状态为最新的任务状态
            doc_dict['processingStatus'] = processing_status_map.get(document.id, 'unprocessed')
            document_list.append(doc_dict)
        
        return jsonify({
            'code': 200,
            'message': '获取文档列表成功',
            'data': {
                'list': document_list,
                'total': len(document_list)
            }
        })
        
    except Exception as e:
        print(f"获取文档列表错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/upload', methods=['POST'])
@token_required
def upload_document():
    """上传文档"""
    try:
        # 检查权限：只有教师和管理员可以上传文档
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify({
                'code': 403,
                'message': '权限不足，只有教师和管理员可以上传文档'
            }), 403
        
        # 检查文件是否存在
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有选择文件'
            }), 400
        
        file = request.files['file']
        course_id = request.form.get('courseId')
        title = request.form.get('title')
        description = request.form.get('description', '')
        chapter_id = request.form.get('chapterId', None)
        
        # 验证必填字段
        if not course_id or not title:
            return jsonify({
                'code': 400,
                'message': '缺少必填字段：courseId, title'
            }), 400
        
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'message': '课程不存在'
            }), 404
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '没有选择文件'
            }), 400
        
        # 检查文件类型
        if not allowed_document_file(file.filename):
            return jsonify({
                'code': 400,
                'message': '不支持的文件类型，请上传PDF、Word、Excel、PowerPoint或文本文件'
            }), 400
        
        # 获取文件MIME类型
        file_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
        
        # 标准化文件类型，特别是PDF
        def normalize_file_type(mime_type, filename):
            """标准化文件类型为简化格式"""
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # 获取文件扩展名
            _, ext = os.path.splitext(filename.lower())
            
            # 根据扩展名和MIME类型返回简化的文件类型
            if 'pdf' in mime_type.lower() or ext == '.pdf':
                return 'pdf'
            
            # Word文档
            if 'word' in mime_type.lower() or ext == '.docx':
                return 'docx'
            elif ext == '.doc':
                return 'doc'
                
            # Excel文档
            if 'excel' in mime_type.lower() or 'spreadsheet' in mime_type.lower():
                if ext == '.xlsx':
                    return 'xlsx'
                elif ext == '.xls':
                    return 'xls'
                
            # PowerPoint文档
            if 'powerpoint' in mime_type.lower() or 'presentation' in mime_type.lower():
                if ext == '.pptx':
                    return 'pptx'
                elif ext == '.ppt':
                    return 'ppt'
            elif ext == '.pptx':
                return 'pptx'
            elif ext == '.ppt':
                return 'ppt'
                
            # 文本文件
            if 'text' in mime_type.lower() or ext == '.txt':
                return 'txt'
            elif ext == '.md':
                return 'md'
                
            # 其他常见格式
            if ext == '.zip':
                return 'zip'
            elif ext == '.rar':
                return 'rar'
            elif ext in ['.jpg', '.jpeg']:
                return 'jpg'
            elif ext == '.png':
                return 'png'
                
            # 如果无法识别，返回扩展名（去掉点号）
            return ext.lstrip('.') if ext else 'unknown'
        
        # 使用标准化后的文件类型
        file_type = normalize_file_type(file_type, file.filename)
        
        # 使用统一的文件保存函数
        file_url = save_file(file, file_type='document')
        
        # 获取文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # 重置文件指针
        
        # 创建文档记录
        new_document = Document(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            file_url=file_url,  # 使用统一的文件URL
            file_type=file_type,
            file_size=file_size,
            course_id=course_id,
            chapter_id=chapter_id if chapter_id else None,
            order_index=0,
            upload_time=datetime.now(),
            is_deleted=False
        )
        
        db.session.add(new_document)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '文档上传成功',
            'data': new_document.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"上传文档错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<document_id>', methods=['PUT'])
@token_required
def update_document(document_id):
    """更新文档信息"""
    try:
        # 检查权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify({
                'code': 403,
                'message': '权限不足'
            }), 403
        
        data = request.get_json()
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        # 更新字段
        if 'title' in data:
            document.title = data['title']
        if 'description' in data:
            document.description = data['description']
        if 'chapterId' in data:
            document.chapter_id = data['chapterId']
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '文档更新成功',
            'data': document.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"更新文档错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<document_id>', methods=['DELETE'])
@token_required
def delete_document(document_id):
    """删除文档（硬删除 + 级联删除）"""
    try:
        # 检查权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify({
                'code': 403,
                'message': '权限不足'
            }), 403
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        deletion_log = []
        
        # 1. 删除document_keywords
        doc_keywords_count = DocumentKeyword.query.filter_by(document_id=document_id).count()
        if doc_keywords_count > 0:
            DocumentKeyword.query.filter_by(document_id=document_id).delete()
            deletion_log.append(f"删除了document_keywords表中{doc_keywords_count}条记录")
        
        # 2. 删除document_vector_indices  
        doc_vector_count = DocumentVectorIndex.query.filter_by(document_id=document_id).count()
        if doc_vector_count > 0:
            # 删除向量索引文件
            vector_indices = DocumentVectorIndex.query.filter_by(document_id=document_id).all()
            for vector_index in vector_indices:
                try:
                    if vector_index.index_path and os.path.exists(vector_index.index_path):
                        import shutil
                        if os.path.isdir(vector_index.index_path):
                            shutil.rmtree(vector_index.index_path)
                        else:
                            os.remove(vector_index.index_path)
                        deletion_log.append(f"删除了向量索引文件: {vector_index.index_path}")
                except Exception as e:
                    current_app.logger.warning(f"删除向量索引文件失败: {e}")
            
            DocumentVectorIndex.query.filter_by(document_id=document_id).delete()
            deletion_log.append(f"删除了document_vector_indices表中{doc_vector_count}条记录")
        
        # 3. 删除document_segments
        doc_segments_count = DocumentSegment.query.filter_by(document_id=document_id).count()
        if doc_segments_count > 0:
            DocumentSegment.query.filter_by(document_id=document_id).delete()
            deletion_log.append(f"删除了document_segments表中{doc_segments_count}条记录")
        
        # 4. 删除document_summaries
        doc_summaries_count = DocumentSummary.query.filter_by(document_id=document_id).count()
        if doc_summaries_count > 0:
            DocumentSummary.query.filter_by(document_id=document_id).delete()
            deletion_log.append(f"删除了document_summaries表中{doc_summaries_count}条记录")
        
        # 5. 删除document_processing_tasks及其相关task_logs
        doc_tasks_count = DocumentProcessingTask.query.filter_by(document_id=document_id).count()
        if doc_tasks_count > 0:
            # 先获取所有相关的task_id
            doc_tasks = DocumentProcessingTask.query.filter_by(document_id=document_id).all()
            task_ids = [task.task_id for task in doc_tasks]
            
            # 删除task_logs表中的相关日志记录
            task_logs_count = 0
            for task_id in task_ids:
                logs_count = TaskLog.query.filter_by(task_id=task_id).count()
                if logs_count > 0:
                    TaskLog.query.filter_by(task_id=task_id).delete()
                    task_logs_count += logs_count
            
            if task_logs_count > 0:
                deletion_log.append(f"删除了task_logs表中{task_logs_count}条日志记录")
            
            # 删除document_processing_tasks表记录
            DocumentProcessingTask.query.filter_by(document_id=document_id).delete()
            deletion_log.append(f"删除了document_processing_tasks表中{doc_tasks_count}条记录")
        
        # 6. 删除文件系统中的实际文件
        try:
            from utils.file_util import get_upload_base_path
            base_path = get_upload_base_path()
            file_path = document.file_url.lstrip('/')
            
            if base_path == '.':
                full_path = file_path
            else:
                full_path = os.path.join(base_path, file_path)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                deletion_log.append(f"删除了文件系统中的文件: {full_path}")
            else:
                deletion_log.append(f"文件系统中的文件不存在: {full_path}")
        except Exception as e:
            current_app.logger.warning(f"删除文档文件失败: {e}")
            deletion_log.append(f"删除文档文件失败: {e}")
        
        # 7. 最后删除documents主表记录
        document_title = document.title
        db.session.delete(document)
        deletion_log.append(f"删除了documents表中的主记录: {document_title}")
        
        # 提交事务
        db.session.commit()
        
        # 输出删除日志
        print(f"\n📋 文档删除完成 - 文档ID: {document_id}")
        print(f"📋 文档标题: {document_title}")
        print("📋 级联删除详情:")
        for log in deletion_log:
            print(f"   ✓ {log}")
        print("📋 删除操作完成\n")
        
        return jsonify({
            'code': 200,
            'message': '文档删除成功',
            'data': {
                'deletionLog': deletion_log,
                'documentTitle': document_title
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"删除文档错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'删除文档失败: {str(e)}'
        }), 500

@document_bp.route('/<document_id>/download', methods=['GET'])
@token_required
def download_document(document_id):
    """下载文档"""
    try:
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        # 增加下载次数
        document.download_count += 1
        db.session.commit()
        
        # 使用文档模型的get_local_path方法获取正确路径
        local_path = document.get_local_path()
        
        # 检查文件是否存在
        if not os.path.exists(local_path):
            return jsonify({
                'code': 404,
                'message': '文件不存在'
            }), 404
        
        # 获取目录和文件名
        directory = os.path.dirname(local_path)
        filename = os.path.basename(local_path)
        
        # 设置下载文件名，优先使用文档标题
        download_name = document.title
        if not download_name.endswith(os.path.splitext(filename)[1]):
            # 如果标题没有扩展名，添加原文件的扩展名
            download_name += os.path.splitext(filename)[1]
        
        from flask import send_from_directory
        return send_from_directory(directory, filename, as_attachment=True, 
                                 download_name=download_name)
        
    except Exception as e:
        print(f"下载文档错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<document_id>/preview', methods=['GET'])
@token_required
def preview_document(document_id):
    """预览文档（支持token参数）"""

    # 解码token
    user_data = request.user
    
    # 验证用户是否存在
    from models.models import Users
    user = Users.query.get(user_data.get('user_id'))
    if not user or user.is_deleted:
        return jsonify({
            'code': 401,
            'message': '用户不存在或已删除'
        }), 401
            

    
    # 查找文档
    document = Document.query.get(document_id)
    if not document or document.is_deleted:
        return jsonify({
            'code': 404,
            'message': '文档不存在'
        }), 404
    
    # 使用统一的文件路径处理
    from flask import send_from_directory
    from utils.file_util import get_upload_base_path
    
    file_path = document.file_url.lstrip('/')
    
    # 构建完整的文件路径
    base_path = get_upload_base_path()
    if base_path == '.':
        # 相对于当前工作目录
        full_directory = os.path.dirname(file_path) if os.path.dirname(file_path) else '.'
        full_path = file_path
    else:
        # 绝对路径
        full_directory = os.path.join(base_path, os.path.dirname(file_path))
        full_path = os.path.join(base_path, file_path)
    
    filename = os.path.basename(file_path)
    
    # 调试信息
    print(f"预览文档调试信息:")
    print(f"  document_id: {document_id}")
    print(f"  file_url: {document.file_url}")
    print(f"  file_path: {file_path}")
    print(f"  full_directory: {full_directory}")
    print(f"  filename: {filename}")
    print(f"  full_path: {full_path}")
    print(f"  文件存在: {os.path.exists(full_path)}")
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        return jsonify({
            'code': 404,
            'message': f'文件不存在: {full_path}'
        }), 404
    
    # 使用绝对路径确保正确
    abs_directory = os.path.abspath(full_directory)
    print(f"  abs_directory: {abs_directory}")
    print(f"  目录存在: {os.path.exists(abs_directory)}")
    
    return send_from_directory(abs_directory, filename, as_attachment=False)


@document_bp.route('/<document_id>/process', methods=['POST'])
@token_required
def process_document(document_id):
    """
    手动触发文档处理任务的接口，支持简化的处理选项
    支持参数：
    - process_mode: 处理模式 ("full_reprocess" | "process_remaining")
    """
    try:
        # 检查权限
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找文档
        document = Document.query.get(document_id)
        if not document:
            return jsonify(Result.error(404, "文档不存在"))
            
        # 检查文档是否已删除
        if document.is_deleted:
            return jsonify(Result.error(400, "文档已被删除"))
            
        # 如果文档属于课程，确认是否有权限
        if document.course_id:
            course = Course.query.get(document.course_id)
            if course and str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
                return jsonify(Result.error(403, "无权处理他人创建的课程文档"))
          
        # 获取请求参数
        data = request.get_json() or {}
        process_mode = data.get('process_mode', 'full_reprocess')  # 默认为完全重新处理
        
        # 根据处理模式确定要执行的步骤
        processing_steps = None
        if process_mode == 'full_reprocess':
            # 清空记录并重新处理 - 执行所有步骤
            from tasks.document_processor.main_processor import get_all_document_processing_steps
            processing_steps = get_all_document_processing_steps()
        elif process_mode == 'process_remaining':
            # 处理还未处理的步骤
            from tasks.document_processor.main_processor import get_uncompleted_document_processing_steps
            processing_steps = get_uncompleted_document_processing_steps(document_id)
            if not processing_steps:
                return jsonify(Result.success({
                    "message": "所有处理步骤都已完成，无需重新处理"
                }, "文档处理已完成"))
        else:
            return jsonify(Result.error(400, f"无效的处理模式: {process_mode}，有效模式: full_reprocess, process_remaining"))
        
        # 检查文档本地文件可用性
        if not document.get_local_path() or not os.path.exists(document.get_local_path()):
            return jsonify(Result.error(400, f"文档文件不存在，无法处理"))

        # 检查是否有正在进行的处理任务
        existing_task = DocumentProcessingTask.query.filter_by(
            document_id=document_id, 
            status='processing'
        ).first()
        
        if existing_task:
            # 删除现有的处理任务而不是返回错误
            db.session.delete(existing_task)
            db.session.commit()

        # 导入处理函数并直接执行
        from tasks.document_processor.main_processor import process_document_async
        
        # 如果未指定步骤，使用所有步骤
        if processing_steps is None:
            from tasks.document_processor.main_processor import get_all_document_processing_steps
            processing_steps = get_all_document_processing_steps()
        
        # 直接执行文档处理（同步）
        processing_result = process_document_async(
            document_id, 
            processing_steps
        )
        
        # 构建响应数据
        result_data = {
            "documentId": document_id,
            "processingSteps": processing_steps,
            "processingResult": processing_result
        }
        
        message = "文档处理完成"
        return jsonify(Result.success(result_data, message))
        
    except Exception as e:
        current_app.logger.error(f"启动文档处理任务失败: {str(e)}")
        return jsonify(Result.error(500, f"启动文档处理任务失败: {str(e)}"))

@document_bp.route('/<document_id>/processing-status', methods=['GET'])
@token_required
def get_document_processing_status(document_id):
    """
    获取文档处理步骤状态的接口
    """
    try:
        # 检查权限
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找文档
        document = Document.query.get(document_id)
        if not document:
            return jsonify(Result.error(404, "文档不存在"))
            
        # 检查文档是否已删除
        if document.is_deleted:
            return jsonify(Result.error(400, "文档已被删除"))
            
        # 如果文档属于课程，确认是否有权限
        if document.course_id:
            course = Course.query.get(document.course_id)
            if course and str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
                return jsonify(Result.error(403, "无权查看他人创建的课程文档状态"))
        
        # 检查各个处理步骤的状态
        step_status = {
            "markitdown": False,
            "segment": False,
            "vector": False,
            "summary": False
        }
        
        # 检查markitdown转换 - 通过processing_status字段判断
        if document.processing_status in ['markitdown_completed', 'segmented', 'vectorized', 'summarized', 'completed']:
            step_status["markitdown"] = True
        
        # 检查智能分段
        segment_count = DocumentSegment.query.filter_by(document_id=document_id).count()
        if segment_count > 0:
            step_status["segment"] = True
        
        # 检查向量化处理
        vector_index = DocumentVectorIndex.query.filter_by(document_id=document_id).first()
        step_status["vector"] = vector_index is not None
        
        # 检查智能摘要
        summary = DocumentSummary.query.filter_by(document_id=document_id).first()
        step_status["summary"] = summary is not None
        
        # 计算整体进度和状态
        completed_steps = sum(1 for completed in step_status.values() if completed)
        total_steps = len(step_status)
        progress = completed_steps / total_steps if total_steps > 0 else 0
        
        # 确定处理状态
        if progress == 1.0:
            processing_status = 'completed'
        elif progress > 0:
            processing_status = 'processing' 
        else:
            # 检查是否有处理任务记录来判断是否在处理中
            processing_task = DocumentProcessingTask.query.filter_by(
                document_id=document_id,
                status='processing'
            ).first()
            processing_status = 'processing' if processing_task else 'pending'
        
        # 构建响应数据（兼容前端期望的格式）
        status_data = {
            "processing_status": processing_status,
            "progress": progress,
            "steps": step_status,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "error_message": None  # 如果需要错误信息，可以从任务记录中获取
        }
        
        return jsonify(Result.success(status_data, "获取文档处理状态成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取文档处理状态失败: {str(e)}")
        return jsonify(Result.error(500, f"获取文档处理状态失败: {str(e)}"))

@document_bp.route('/detail/<document_id>', methods=['GET'])
@token_required
def get_document_detail(document_id):
    """获取文档详情"""
    try:
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        # 构建文档详情数据
        doc_data = document.to_dict()
        
        # 添加课程信息
        if document.course:
            doc_data['course'] = {
                'id': str(document.course.id),
                'name': document.course.name
            }
        
        # 添加章节信息
        if document.chapter:
            doc_data['chapter'] = {
                'id': str(document.chapter.id),
                'title': document.chapter.title
            }
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': doc_data
        })
        
    except Exception as e:
        print(f"获取文档详情错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/<document_id>/summary', methods=['GET'])
@token_required
def get_document_summary(document_id):
    """获取文档摘要"""
    try:
        from models.models import DocumentSummary
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            }), 404
        
        # 查找摘要
        summary = DocumentSummary.query.filter_by(document_id=document_id).first()
        
        if summary:
            return jsonify({
                'code': 200,
                'message': '获取成功',
                'data': summary.to_dict()
            })
        else:
            return jsonify({
                'code': 404,
                'message': '暂无摘要信息',
                'data': None
            })
        
    except Exception as e:
        print(f"获取文档摘要错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@document_bp.route('/batch/processing-status', methods=['POST'])
@token_required
def get_documents_processing_status():
    """
    批量获取文档处理状态
    """
    try:
        data = request.get_json()
        if not data or 'document_ids' not in data:
            return jsonify(Result.error(400, "缺少document_ids参数"))
        
        document_ids = data['document_ids']
        if not isinstance(document_ids, list):
            return jsonify(Result.error(400, "document_ids必须是数组"))
        
        # 导入处理函数
        from tasks.document_processor.main_processor import get_all_document_processing_steps, get_uncompleted_document_processing_steps
        
        results = []
        for document_id in document_ids:
            try:
                document_uuid = uuid.UUID(document_id) if isinstance(document_id, str) else document_id
                document = Document.query.filter_by(id=document_uuid, is_deleted=False).first()
                
                if not document:
                    results.append({
                        'document_id': str(document_id),
                        'error': '文档不存在'
                    })
                    continue
                
                # 获取所有处理步骤和未完成的步骤
                all_steps = get_all_document_processing_steps()
                uncompleted_steps = get_uncompleted_document_processing_steps(document_uuid)
                
                # 计算完成状态
                total_steps = len(all_steps)
                completed_steps = total_steps - len(uncompleted_steps)
                is_fully_completed = len(uncompleted_steps) == 0
                
                results.append({
                    'document_id': str(document_id),
                    'title': document.title,
                    'all_steps': all_steps,
                    'uncompleted_steps': uncompleted_steps,
                    'total_steps': total_steps,
                    'completed_steps': completed_steps,
                    'is_fully_completed': is_fully_completed,
                    'completion_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 100
                })
                
            except Exception as e:
                current_app.logger.error(f"获取文档 {document_id} 处理状态失败: {str(e)}")
                results.append({
                    'document_id': str(document_id),
                    'error': f'获取状态失败: {str(e)}'
                })
        
        return jsonify(Result.success({
            'documents': results
        }))
        
    except Exception as e:
        current_app.logger.error(f"批量获取文档处理状态失败: {str(e)}")
        return jsonify(Result.error(500, f"批量获取文档处理状态失败: {str(e)}"))


@document_bp.route('/<document_id>/progress', methods=['POST'])
@token_required
def update_document_progress(document_id):
    """更新文档阅读进度"""
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        
        # 获取请求参数
        data = request.get_json()
        reading_time = data.get('reading_time', 0)  # 本次阅读时长（秒）
        
        if reading_time <= 0:
            return jsonify({
                'code': 400,
                'message': '阅读时长必须大于0'
            })
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            })
        
        # 查找或创建文档进度记录
        from models.models import DocumentProgress
        progress = DocumentProgress.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()
        
        if not progress:
            # 创建新的进度记录
            progress = DocumentProgress(
                document_id=document_id,
                user_id=user_id,
                reading_time=reading_time,
                progress=0.0,
                last_read_time=datetime.utcnow(),
                completed=False
            )
            db.session.add(progress)
        else:
            # 更新现有进度记录
            progress.reading_time += reading_time
            progress.last_read_time = datetime.utcnow()
        
        # 计算进度百分比（总阅读时长10分钟=600秒）
        total_duration = 600  # 10分钟
        progress.progress = min(1.0, progress.reading_time / total_duration)
        
        # 判断是否完成
        if progress.progress >= 1.0:
            progress.completed = True
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '进度更新成功',
            'data': {
                'total_reading_time': progress.reading_time,
                'progress_percentage': round(progress.progress * 100, 2),
                'is_completed': progress.completed
            }
        })
        
    except Exception as e:
        print(f"更新文档进度错误: {e}")
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        })

@document_bp.route('/<document_id>/progress', methods=['GET'])
@token_required
def get_document_progress(document_id):
    """获取文档阅读进度"""
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        
        # 查找文档
        document = Document.query.get(document_id)
        if not document or document.is_deleted:
            return jsonify({
                'code': 404,
                'message': '文档不存在'
            })
        
        # 查找进度记录
        from models.models import DocumentProgress
        progress = DocumentProgress.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()
        
        if not progress:
            # 如果没有进度记录，返回初始状态
            return jsonify({
                'code': 200,
                'message': '获取进度成功',
                'data': {
                    'total_reading_time': 0,
                    'progress_percentage': 0.0,
                    'is_completed': False,
                    'last_read_time': None,
                    'completion_time': None
                }
            })
        
        return jsonify({
            'code': 200,
            'message': '获取进度成功',
            'data': {
                'total_reading_time': progress.reading_time,
                'progress_percentage': round(progress.progress * 100, 2),
                'is_completed': progress.completed,
                'last_read_time': progress.last_read_time.isoformat() if progress.last_read_time else None,
                'completion_time': None  # DocumentProgress模型中没有completion_time字段
            }
        })
        
    except Exception as e:
        print(f"获取文档进度错误: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        })

