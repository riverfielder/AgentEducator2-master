import requests
import random
import string
import json

BASE_URL = "http://127.0.0.1:5000/api"

def generate_random_string(length=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def test_api_flow():
    print("=== 开始接口连通性测试 ===")
    
    # 1. 注册新用户
    username = f"test_{generate_random_string()}"
    email = f"{username}@test.com"
    password = "Start123!"
    
    print(f"\n[1] 测试注册接口 (/auth/register)")
    print(f"    注册用户: {username}, 邮箱: {email}")
    
    try:
        register_resp = requests.post(f"{BASE_URL}/auth/register", json={
            "username": username,
            "email": email,
            "password": password,
            "role": "student"
        })
        
        if register_resp.status_code == 200:
            print("    ✅ 注册成功")
        else:
            print(f"    ❌ 注册失败: {register_resp.status_code} - {register_resp.text}")
            return
    except Exception as e:
        print(f"    ❌ 请求异常: {e}")
        return

    # 2. 登录
    print(f"\n[2] 测试登录接口 (/auth/login)")
    try:
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if login_resp.status_code == 200:
            login_data = login_resp.json()
            # 根据代码，返回结构是 Result.success(vo.dict())，其中 Result.success 包装在 'data' 字段
            # 但 Result.success 返回的 json 结构通常是 {code: 200, msg: "...", data: {...}}
            if login_data.get("code") == 200:
                token = login_data["data"]["token"]
                print("    ✅ 登录成功，获取到Token")
            else:
                print(f"    ❌ 登录逻辑失败: {login_data}")
                return
        else:
            print(f"    ❌ 登录请求失败: {login_resp.status_code} - {login_resp.text}")
            return
    except Exception as e:
        print(f"    ❌ 请求异常: {e}")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 3. 获取课程列表
    print(f"\n[3] 测试课程列表接口 (/courses/list)")
    try:
        courses_resp = requests.get(f"{BASE_URL}/courses/list", headers=headers)
        
        if courses_resp.status_code == 200:
            print("    ✅ 获取课程列表成功")
            data = courses_resp.json()
            if data.get("code") == 200:
                count = len(data.get("data", []))
                print(f"    当前课程数量: {count}")
            else:
                 print(f"    ⚠️ 接口返回非成功状态: {data}")
        else:
            print(f"    ❌ 获取失败: {courses_resp.status_code} - {courses_resp.text}")
    except Exception as e:
        print(f"    ❌ 请求异常: {e}")

    # 4. 测试QA问答流
    print(f"\n[4] 测试AI问答接口 (/qa/ask-stream)")
    try:
        # QA接口通常需要一个 history 数组和 query 字符串
        # 还要看 `_parse_request_data` 的实现，它似乎只支持 JSON
        # 且可能需要 `session_id` 如果是继续对话，新对话可能不需要
        qa_payload = {
            "query": "Hello, AI!",
            "history": [],
            "course_id": None, # 可选
            "video_id": None   # 可选
        }
        
        qa_resp = requests.post(f"{BASE_URL}/qa/ask-stream", json=qa_payload, headers=headers, stream=True)
        
        if qa_resp.status_code == 200:
            print("    ✅ 连接AI服务成功 (流式响应)")
            # 读取一点数据证明流是通的
            chunk_count = 0
            for chunk in qa_resp.iter_content(chunk_size=1024):
                if chunk:
                    chunk_count += 1
                    if chunk_count >= 1: # 只要收到任何数据就算通了
                        print("    ✅ 成功接收到流数据")
                        break
        else:
            error_msg = qa_resp.text[:200] # 只截取前200字符
            print(f"    ❌ AI服务请求失败: {qa_resp.status_code} - {error_msg}")
            
    except Exception as e:
        print(f"    ❌ 请求异常: {e}")

    print("\n=== 测试结束 ===")

if __name__ == "__main__":
    test_api_flow()
