import sys
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Users, TaskLog, Video
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        try:
            res1 = conn.execute(text("UPDATE task_logs SET status='failed', error_message='System restarted' WHERE status IN ('processing', 'running', 'pending')"))
            print("Updated task_logs:", res1.rowcount)
        except Exception as e:
            pass
            
        try:
            res3 = conn.execute(text("UPDATE videos SET process_status='failed' WHERE process_status IN ('processing', 'running', 'pending')"))
            print("Updated videos process_status:", res3.rowcount)
        except Exception as e:
            pass
        conn.commit()
