import sys
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Users, TaskLog, Video

app = create_app()
with app.app_context():
    stuck_tasks = TaskLog.query.filter(TaskLog.status.in_(['processing', 'running', 'pending'])).all()
    stuck_videos = Video.query.filter(Video.process_status.in_(['processing', 'running', 'pending'])).count()
    if stuck_videos == 0 and len(stuck_tasks) == 0:
        print("======== ALL CLEAR! =========")
    else:
        print("======== STILL STUCK! =========")
        print(f"Tasks: {len(stuck_tasks)}, Videos: {stuck_videos}")
