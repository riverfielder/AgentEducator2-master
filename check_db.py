import sqlite3
import json

conn = sqlite3.connect('/opt/AgentEducator2/backend/instance/agent_educator.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id, task_type, status, file_name, created_at, user_id FROM task_logs WHERE status IN ('processing', 'running', 'pending')")
rows = [dict(row) for row in cursor.fetchall()]
print(json.dumps(rows, indent=2, ensure_ascii=False))

cursor.execute("SELECT email, id FROM users WHERE email='2474381478@qq.com'")
users = [dict(row) for row in cursor.fetchall()]
print("USER:")
print(json.dumps(users, indent=2, ensure_ascii=False))

# check video table too
cursor.execute("SELECT id, title, process_status, status FROM videos WHERE process_status IN ('processing', 'running', 'pending') OR status IN ('processing', 'running', 'pending')")
videos = [dict(row) for row in cursor.fetchall()]
print("VIDEOS:")
print(json.dumps(videos, indent=2, ensure_ascii=False))

