import sys
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Users, VideoProcessingTask, DocumentProcessingTask
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("VideoProcessingTask cols:", VideoProcessingTask.__table__.columns.keys())
    with db.engine.connect() as conn:
        try:
            res0 = conn.execute(text("UPDATE video_processing_tasks SET status='failed', error_message='System restarted' WHERE status IN ('processing', 'running', 'pending')"))
            print("Updated video_processing_tasks:", res0.rowcount)
        except Exception as e:
            print("Error tasks:", e)
            
        try:
            res1 = conn.execute(text("UPDATE document_processing_tasks SET status='failed', error_message='System restarted' WHERE status IN ('processing', 'running', 'pending')"))
            print("Updated doc tasks:", res1.rowcount)
        except Exception as e:
            pass
            
        conn.commit()
