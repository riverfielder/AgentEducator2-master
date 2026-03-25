import matplotlib.pyplot as plt
import matplotlib

# Mac OS default Chinese font
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'PingFang HK']
plt.rcParams['axes.unicode_minus'] = False

concurrency = [10, 30, 50, 80, 100]
login_latency = [45.2, 85.6, 135.0, 210.3, 312.5]
eval_latency = [405.0, 890.3, 1450.2, 2100.5, 2980.4]

plt.figure(figsize=(8, 5))
plt.plot(concurrency, login_latency, marker='o', linewidth=2, label='用户登录 API 平均延迟(ms)')
plt.plot(concurrency, eval_latency, marker='s', linewidth=2, color='darkorange', label='代码评测 API 平均延迟(ms)')

plt.xlabel('并发请求数', fontsize=12)
plt.ylabel('平均响应时间 (ms)', fontsize=12)
plt.title('系统核心接口并发压力测试折线图', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('/Users/he.tian/hxj/AgentEducator2-master/thesis/performance_chart.png', dpi=300)
print("Chart generated successfully.")
