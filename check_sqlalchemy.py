import sys
import json
import os
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Users, TaskLog, Video, VideoProcessingTask

app = create_app()
with app.app_context():
    users = Users.query.filter(Users.email.like('%2474381478@%')).all()
    print("USER:")
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}")
    
    stuck_tasks = TaskLog.query.filter(TaskLog.status.in_(['processing', 'running', 'pending'])).all()
    print("STUCK LOGS:")
    for t in stuck_tasks:
        print(f"Task ID: {t.id}, File: {t.file_name}, Status: {t.status}")

    stuck_videos = Video.query.filter(Video.process_status.in_(['processing', 'running', 'pending'])).all()
    print("STUCK VIDEOS:")
    for v in stuck_videos:
        print(f"Video ID: {v.id}, Title: {v.title}, Status: {v.process_status}")
    
    # Just fix them directly on the server to 'failed' so user can retry, or 'completed' if we don't have a way to restart without user interaction.
    # Actually wait, let's just mark them as 'failed' with error message so user can rebuild them. Or better, just 'completed' if they are already processed? Let's check status first.
