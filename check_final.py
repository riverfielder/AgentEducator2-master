import sys
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, VideoProcessingTask

app = create_app()
with app.app_context():
    stuck_tasks = VideoProcessingTask.query.filter(VideoProcessingTask.status.in_(['processing', 'running', 'pending'])).all()
    if len(stuck_tasks) == 0:
        print("YES ALL CLEARED")
    else:
        print("NO NOT CLEARED")
