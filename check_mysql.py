import pymysql
import json

conn = pymysql.connect(
    host="localhost",
    user="wendao",
    password="wendao",
    database="wendao_platform",
    cursorclass=pymysql.cursors.DictCursor
)
with conn.cursor() as cursor:
    cursor.execute("SELECT id, email FROM users WHERE email LIKE '%2474381478@%'")
    users = cursor.fetchall()
    print("USER:")
    print(json.dumps(users, indent=2, ensure_ascii=False))

    cursor.execute("SELECT id, file_name, status, task_type FROM task_logs WHERE status IN ('processing', 'running', 'pending')")
    print("STUCK TASKS:")
    print(json.dumps(cursor.fetchall(), indent=2, ensure_ascii=False))

    try:
        cursor.execute("SELECT id, title, process_status FROM video_materials WHERE process_status IN ('processing', 'running', 'pending')")
        print("STUCK VIDEOS :")
        print(json.dumps(cursor.fetchall(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error querying video_materials:", e)
