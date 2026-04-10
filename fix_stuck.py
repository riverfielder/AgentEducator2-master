import sys
import json
import os
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Users, TaskLog, Video, VideoProcessingTask

app = create_app()
with app.app_context():
    
    stuck_tasks = TaskLog.query.filter(TaskLog.status.in_(['processing', 'running', 'pending'])).all()
    print("STUCK LOGS:")
    for t in stuck_tasks:
        print(f"Task ID: {t.id}, File: {t.file_name}, Status: {t.status}")
        t.status = 'failed'
        t.error_message = 'Interrupted by server restart or bug'

    stuck_videos = Video.query.filter(Video.process_status.in_(['processing', 'running', 'pending'])).all()
    print("STUCK VIDEOS:")
    for v in stuck_videos:
        print(f"Video ID: {v.id}, Title: {v.title}, Status: {v.process_status}")
        v.process_status = 'failed'
        
    db.session.commit()
    print("ALL STUCK UPDATED to FAILED.")
