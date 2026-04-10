import sys
sys.path.append('/opt/AgentEducator2/backend')
from app import create_app
from models.models import db, Video, VideoProcessingTask, TaskLog, VideoSummary

app = create_app()
with app.app_context():
    video_id = '067cb9f0-e7c5-460b-b4b9-eea27b35bc7e'
    v = Video.query.get(video_id)
    if not v:
        print("Video not found.")
        sys.exit(0)
    
    print(f"Video Title: {v.title}")
    print(f"Video process_status: {v.process_status if hasattr(v, 'process_status') else getattr(v, 'status', 'Unknown')}")
    print(f"Video duration: {v.duration}")
    
    summary = VideoSummary.query.filter_by(video_id=video_id).first()
    print(f"Has Summary: {'Yes' if summary else 'No'}")
    
    ptasks = VideoProcessingTask.query.filter_by(video_id=video_id).all()
    print("Processing Tasks:")
    for t in ptasks:
        print(f" - ID: {t.id}, Status: {t.status}, Error: {t.error_message}")
        
    logs = TaskLog.query.filter_by(video_id=video_id).order_by(TaskLog.created_at.desc()).limit(5).all()
    print("Task Logs (Last 5):")
    for l in logs:
        print(f" - [{l.status}] {l.message} (Error: {l.error_message})")
