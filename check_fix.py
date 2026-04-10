import sys
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Users, TaskLog, Video

app = create_app()
with app.app_context():
    stuck_videos = Video.query.filter(Video.process_status.in_(['processing', 'running', 'pending'])).all()
    print("STUCK VIDEOS AFTER FIX:", len(stuck_videos))
    for v in stuck_videos:
        print(v.id, v.title, v.process_status)
