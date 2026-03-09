"""
教师端智能助手API路由
提供教师专用的AI助手功能，包括课程分析、学生洞察、教学建议等
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
# from flask_cors import cross_origin  # 移除，使用全局CORS配置
import json
import uuid
from datetime import datetime
import traceback

# 导入认证和工具
from utils.auth import token_required, role_required
from services.teacher_agent_service import teacher_agent_service
from models.models import db, ChatSession, ChatMessage

# 创建蓝图
teacher_assistant_bp = Blueprint('teacher_assistant', __name__, url_prefix='/api/teacher-assistant')

@teacher_assistant_bp.route('/chat', methods=['POST'])
@token_required
@role_required('teacher')
def teacher_chat():
    """
    教师端智能对话接口
    支持流式响应和工具调用
    """
    try:
        data = request.get_json()
        
        # 提取请求参数
        content = data.get('content', '').strip()
        session_id = data.get('sessionId')
        qa_mode = data.get('qaMode', 'teacher_general')
        references = data.get('references', [])
        chat_id = data.get('chatId')
        
        # 获取教师ID
        teacher_id = request.current_user.get('user_id')
        
        if not content:
            return jsonify({
                'success': False,
                'message': '请输入问题内容'
            }), 400
        
        print(f"🎓 教师端对话请求: teacher_id={teacher_id}, qa_mode={qa_mode}, content={content[:50]}...")
        
        # 创建Agent执行器
        agent_executor, error = teacher_agent_service.create_teacher_agent(
            teacher_id=teacher_id,
            qa_mode=qa_mode,
            references=references
        )
        
        if error or not agent_executor:
            return jsonify({
                'success': False,
                'message': error or '无法创建智能助手'
            }), 500

        # 执行查询
        try:
            # 获取历史记录
            # 优先使用前端传入的history，如果没有且有sessionId，则从数据库加载
            history = request.get_json().get('history', [])
            
            # 数据库会话处理
            current_db_session = None
            if session_id:
                current_db_session = ChatSession.query.filter_by(id=session_id, user_id=teacher_id).first()
                
                # 如果有会话ID但没传history，尝试从库里捞
                if not history and current_db_session and not current_db_session.is_deleted:
                    saved_msgs = ChatMessage.query.filter_by(
                        session_id=session_id
                    ).order_by(ChatMessage.created_at).all()
                    
                    history = [
                        {'role': msg.role, 'content': msg.content} 
                        for msg in saved_msgs
                    ]
            
            # 如果是新会话（没有session_id或库里没找到）
            if not current_db_session:
                # 生成新ID
                new_session_id = session_id or str(uuid.uuid4())
                session_id = new_session_id
                
                # 创建新会话记录
                current_db_session = ChatSession(
                    id=new_session_id,
                    user_id=teacher_id,
                    title=content[:30] + ('...' if len(content) > 30 else ''),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.session.add(current_db_session)
                db.session.flush()

            result = teacher_agent_service.query_teacher_agent(
                agent_executor=agent_executor,
                question=content,
                history=history
            )
            
            # 保存对话记录到数据库
            try:
                # 1. 保存用户提问
                user_msg = ChatMessage(
                    session_id=session_id,
                    role='user',
                    content=content,
                    created_at=datetime.now()
                )
                db.session.add(user_msg)
                
                # 2. 保存AI回答
                ai_response = result.get('result', '')
                ai_msg = ChatMessage(
                    session_id=session_id,
                    role='assistant',
                    content=ai_response,
                    created_at=datetime.now()
                )
                db.session.add(ai_msg)
                
                # 3. 更新会话时间
                current_db_session.updated_at = datetime.now()
                db.session.commit()
                
            except Exception as db_err:
                print(f"⚠️ 保存对话记录失败: {db_err}")
                db.session.rollback()
                # 不影响返回结果
            
            return jsonify({
                'success': True,
                'message': '查询成功',
                'sessionId': session_id,
                'data': {
                    'content': result.get('result', ''),
                    'qaMode': qa_mode,
                    'references': references,
                    'timestamp': datetime.now().isoformat(),
                    'source_documents': [] # 暂时不返回源文档以简化
                }
            })
            
        except Exception as e:
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'执行查询失败: {str(e)}'
            }), 500
        
    except Exception as e:
        print(f"❌ 教师端对话处理失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'对话处理失败: {str(e)}'
        }), 500

@teacher_assistant_bp.route('/chat/stream', methods=['POST'])
@token_required
@role_required('teacher')
def teacher_chat_stream():
    """
    教师端流式对话接口
    支持实时流式响应
    """
    try:
        data = request.get_json()
        
        # 提取请求参数
        content = data.get('content', '').strip()
        session_id = data.get('sessionId') or str(uuid.uuid4()) # 确保有session_id
        qa_mode = data.get('qaMode', 'teacher_general')
        references = data.get('references', [])
        history = data.get('history', [])  # 添加历史记录支持
        
        # 获取教师ID
        teacher_id = request.current_user.get('user_id')
        
        if not content:
            return jsonify({
                'success': False,
                'message': '请输入问题内容'
            }), 400
        
        print(f"🎓 教师端流式对话请求: teacher_id={teacher_id}, qa_mode={qa_mode}")

        from queue import Queue
        from threading import Thread
        from services.callbacks import CustomStreamingCallback, StatusNotifier
        from services.chat_service import chat_service

        # 1. 准备流式所需对象
        queue = Queue()
        callback = CustomStreamingCallback(queue)
        
        # 定义后台执行函数
        def run_search(app):
            with app.app_context():
                try:
                    notifier = StatusNotifier(queue)
                    notifier.notify_analysis_start()
                    
                    # 2. 创建教师Agent
                    agent_executor, error = teacher_agent_service.create_teacher_agent(
                        teacher_id=teacher_id,
                        qa_mode=qa_mode,
                        references=references,
                        streaming_callback=callback  # 传入回调
                    )
                    
                    if error or not agent_executor:
                        raise Exception(error or "无法创建Helper Agent")
                    
                    
                    notifier.notify_search_start()
                    
                    # 3. 执行查询 (注意这里使用 query_teacher_agent 同步方法，但因为传入了 callback，agent 内部会触发 put)
                    # 或者是直接调用内部链
                    # 由于 teacher_agent_service.query_teacher_agent 复用了 qa_service，
                    # 只要 agent 是带 callback 初始化的，执行时就会有流式输出。
                    
                    result = teacher_agent_service.query_teacher_agent(
                        agent_executor=agent_executor,
                        question=content,
                        history=history
                    )
                    
                    # 4. 保存对话记录到数据库
                    # 注意：需要把 AI 的最终回答提取出来
                    ai_response = result.get('result', '')
                    
                    # 确保会话存在
                    chat_service.create_or_get_session(
                        session_id=session_id,
                        user_id=teacher_id,
                        title=content[:20] if content else "新对话"
                    )

                    # 保存用户提问
                    chat_service.save_message_to_db(
                        session_id=session_id,
                        role='user',
                        content=content
                    )
                    
                    # 保存AI回答
                    chat_service.save_message_to_db(
                        session_id=session_id,
                        role='assistant',
                        content=ai_response
                    )

                    notifier.notify_complete()
                    
                except Exception as e:
                    print(f"流式生成出错: {e}")
                    traceback.print_exc()
                    queue.put(f"data: {json.dumps({'error': str(e)})}\n\n")
                    queue.put(None)  # 结束信号
                finally:
                    # 确保无论如何都发送结束信号(如果 callback 没有发的话)
                    # CustomStreamingCallback 会处理 None
                    pass

        # 启动后台线程
        app = current_app._get_current_object()
        thread = Thread(target=run_search, args=(app,))
        thread.start()

        # 定义生成器
        def generate():
            while True:
                token = queue.get()
                if token is None:
                    break
                
                # 如果已经是格式化的SSE消息，直接发送
                if isinstance(token, str) and token.startswith('data: '):
                    yield token
                else:
                    # 否则包装为SSE消息
                    yield f"data: {token}\n\n"

        # 返回响应
        resp = Response(
            stream_with_context(generate()),
            content_type='text/event-stream'
        )
        resp.headers['X-Session-Id'] = str(session_id)
        resp.headers['Cache-Control'] = 'no-cache'
        return resp

    except Exception as e:
        print(f"❌ 教师端流式接口异常: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'系统错误: {str(e)}'
        }), 500


@teacher_assistant_bp.route('/history/<teacher_id>', methods=['GET'])
@token_required
@role_required('teacher')
def get_teacher_chat_history(teacher_id):
    """
    获取教师端聊天历史
    返回教师所有的聊天会话列表
    """
    try:
        # 验证权限：只能查看自己的聊天历史
        current_teacher_id = request.current_user.get('user_id')
        if current_teacher_id != teacher_id:
            return jsonify({
                'success': False,
                'message': '无权访问其他教师的聊天历史'
            }), 403
        
        print(f"📚 获取教师端聊天历史: teacher_id={teacher_id}")
        
        # 从数据库查询该教师的所有未删除会话
        sessions = ChatSession.query.filter_by(
            user_id=teacher_id, 
            is_deleted=False
        ).order_by(ChatSession.updated_at.desc()).all()
        
        history_data = []
        for session in sessions:
            # 简单起见，这里不需要返回所有消息，只返回会话信息
            # 如果前端需要显示最后一条消息，可以查询
            last_message = ChatMessage.query.filter_by(
                session_id=session.id
            ).order_by(ChatMessage.created_at.desc()).first()
            
            history_data.append({
                'id': str(session.id),
                'sessionId': str(session.id),
                'title': session.title,
                'lastMessage': last_message.content if last_message else '',
                'updatedAt': session.updated_at.isoformat() if session.updated_at else None,
                'createdAt': session.created_at.isoformat() if session.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': history_data,
            'message': '聊天历史获取成功'
        })
        
    except Exception as e:
        print(f"❌ 获取教师端聊天历史失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取聊天历史失败: {str(e)}'
        }), 500

@teacher_assistant_bp.route('/session', methods=['POST'])
@token_required
@role_required('teacher')
def create_teacher_session():
    """
    创建教师端聊天会话
    """
    try:
        data = request.get_json() or {}
        teacher_id = request.current_user.get('user_id')
        title = data.get('title', f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        print(f"🆕 创建教师端聊天会话: teacher_id={teacher_id}")
        
        # 生成新的会话ID
        session_id = str(uuid.uuid4())
        
        # 创建数据库记录
        new_session = ChatSession(
            id=session_id,
            user_id=teacher_id,
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'message': '会话创建成功',
            'data': {
                'id': session_id,
                'title': title,
                'createdAt': new_session.created_at.isoformat()
            }
        })
        
    except Exception as e:
        print(f"❌ 创建教师端聊天会话失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'创建会话失败: {str(e)}'
        }), 500

@teacher_assistant_bp.route('/session/<session_id>', methods=['DELETE'])
@token_required
@role_required('teacher')
def delete_teacher_session(session_id):
    """
    删除教师端聊天会话
    """
    try:
        teacher_id = request.current_user.get('user_id')
        
        print(f"🗑️ 删除教师端聊天会话: teacher_id={teacher_id}, session_id={session_id}")
        
        # 查找会话
        session = ChatSession.query.filter_by(id=session_id, user_id=teacher_id).first()
        
        if not session:
            return jsonify({
                'success': False,
                'message': '会话不存在或无权访问'
            }), 404
            
        # 软删除
        session.is_deleted = True
        session.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '会话删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 删除教师端聊天会话失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除会话失败: {str(e)}'
        }), 500

@teacher_assistant_bp.route('/session/<session_id>', methods=['PATCH'])
@token_required
@role_required('teacher')
def update_teacher_session(session_id):
    """
    更新教师端聊天会话（如标题）
    """
    try:
        data = request.get_json()
        teacher_id = request.current_user.get('user_id')
        title = data.get('title')
        
        print(f"📝 更新教师端聊天会话: teacher_id={teacher_id}, session_id={session_id}, title={title}")
        
        # 查找会话
        session = ChatSession.query.filter_by(id=session_id, user_id=teacher_id).first()
        
        if not session:
            return jsonify({
                'success': False,
                'message': '会话不存在或无权访问'
            }), 404
            
        if title:
            session.title = title
            session.updated_at = datetime.now()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '会话更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 更新教师端聊天会话失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新会话失败: {str(e)}'
        }), 500

@teacher_assistant_bp.route('/tools/available', methods=['GET'])
@token_required
@role_required('teacher')
def get_available_tools():
    """
    获取教师端可用工具列表
    """
    try:
        teacher_id = request.current_user.get('user_id')
        
        print(f"🔧 获取教师端可用工具: teacher_id={teacher_id}")
        
        # 当前版本返回预定义的教师端工具列表
        # 后续版本可改为从AgentService动态获取注册工具
        tools = [
            {
                'name': 'course_analysis',
                'display_name': '课程分析',
                'description': '分析课程内容和结构',
                'icon': 'mdi-book-search',
                'status': 'development'
            },
            {
                'name': 'student_insights',
                'display_name': '学生洞察',
                'description': '分析学生学习情况',
                'icon': 'mdi-account-search',
                'status': 'development'
            },
            {
                'name': 'teaching_suggestions',
                'display_name': '教学建议',
                'description': '生成个性化教学建议',
                'icon': 'mdi-lightbulb',
                'status': 'development'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': tools,
            'message': '工具列表获取成功'
        })
        
    except Exception as e:
        print(f"❌ 获取教师端可用工具失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取工具列表失败: {str(e)}'
        }), 500 