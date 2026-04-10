import urllib.request
import json
import urllib.error

data = json.dumps({'keyword':'Python', 'count':3}).encode('utf-8')
req = urllib.request.Request('http://152.42.253.248/api/training/generate-personalized', data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code} Error details:")
    print(e.read().decode('utf-8'))
except Exception as e:
    print("Other Error:", str(e))
