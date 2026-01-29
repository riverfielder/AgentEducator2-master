"""聊天服务模块"""
import uuid
from flask import current_app
from models.models import ChatSession, ChatMessage, db


class ChatService:
    """聊天服务"""
    
    @staticmethod
    def create_or_get_session(session_id, user_id, title, video_id=None, course_id=None, is_new_session=False):
        """创建或获取聊天会话"""
        db_session = None
        
        if session_id and not is_new_session:
            db_session = ChatSession.query.filter_by(
                id=session_id, user_id=user_id, is_deleted=False
            ).first()
            
        if not db_session:
            db_session = ChatSession(
                id=session_id or str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                video_id=video_id,
                course_id=course_id
            )
            db.session.add(db_session)
            db.session.commit()
        
        return db_session.id
    
    @staticmethod
    def save_message_to_db(session_id, role, content, sources=None):
        """保存消息到数据库"""
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=role,
                content=content
            )
            if sources:
                message.set_time_references(sources)
            else:
                message.set_time_references(None)
            
            db.session.add(message)
            
            # 更新会话时间
            if role == 'assistant':
                session = ChatSession.query.get(session_id)
                if session:
                    session.updated_at = db.func.now()
            
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"保存消息失败: {str(e)}")
            db.session.rollback()
            return False


# 全局聊天服务实例
chat_service = ChatService()
