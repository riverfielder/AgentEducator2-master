import time
import requests
import concurrent.futures

url = "http://152.42.253.248/api/categories/list"

def fetch(i):
    start = time.time()
    try:
        r = requests.get(url, timeout=5)
        return r.status_code, time.time() - start
    except Exception:
        return 500, time.time() - start

print(f"Starting load test on {url}...")
start_time = time.time()
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    results = list(executor.map(fetch, range(200)))

total_time = time.time() - start_time
successes = [r for r in results if r[0] == 200]
errors = [r for r in results if r[0] != 200]
avg_time = sum(r[1] for r in results) / len(results)

print(f"Total time: {total_time:.2f}s")
print(f"Requests: {len(results)}")
print(f"Successes: {len(successes)}")
print(f"Errors: {len(errors)}")
print(f"Error Rate: {len(errors)/len(results)*100:.2f}%")
print(f"RPS: {len(results)/total_time:.2f}")
print(f"Average Latency: {avg_time*1000:.2f}ms")
