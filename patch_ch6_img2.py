import pathlib
import sys
import re

ch6_path = pathlib.Path(r'D:\hxjbs\AgentEducator2-master\thesis\pages\chapter6.tex')
ch6_text = ch6_path.read_text(encoding='utf-8')

# --- 1. Replace placeholder UI screenshots with the real ones ---
ch6_text = ch6_text.replace(r'{logo/ui_sandbox.png}', r'{code_training.png}')
ch6_text = ch6_text.replace(r'% 璇风敤鎴锋埅鍙栦竴寮狅細宸︿晶鏈夊璇濊緟瀵笺€佸彸渚ф湁浠ｇ爜缂栬緫鍣ㄥ拰浠 ｇ爜杩愯缁撴灉鏁堟灉鐨勫浘鐗囷紝鍛藉悕涓?ui_sandbox.png 鏀惧叆 logo 鎴?images  鏂囦欢澶?', r'% 使用真实代码实训图像')

ch6_text = ch6_text.replace(r'{logo/ui_video.png}', r'{video_qa.png}')
ch6_text = ch6_text.replace(r'% 璇风敤鎴锋埅鍙栦竴寮狅細瑙嗛鎾斁鐣岄潰涓庡彸渚ч棶绛旀祦鑱斿姩鐨勯珮淇濈湡 鍥剧墖锛屽懡鍚嶄负 ui_video.png', r'% 使用真实视频与QA图像')

# --- 2. Add Whitebox testing screenshot ---
whitebox_old = r'成为了业务级 \$100\%\$ 的验证通过率。'
if '验证通过率。' in ch6_text:
    idx = ch6_text.find('验证通过率。') + len('验证通过率。')
    insert_whitebox = r'''

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.75\textwidth,keepaspectratio]{whitebox_test.png} 
  \caption{系统实训模块沙箱隔离黑白盒测试与执行拦截反馈截图}
  \label{fig:whitebox}
\end{figure}
'''
    if 'whitebox_test.png' not in ch6_text:
        ch6_text = ch6_text[:idx] + insert_whitebox + ch6_text[idx:]

# --- 3. Add Performance Chart screenshot ---
perf_old = r'得出量化性能指标：'
if perf_old in ch6_text:
    idx = ch6_text.find(perf_old) + len(perf_old)
    insert_perf = r'''（压测图表详见图 \ref{fig:perf_chart}）

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.85\textwidth,keepaspectratio]{performance_chart.png} 
  \caption{基于 Locust 的系统高并发与 TTFT 发压测监控报告}
  \label{fig:perf_chart}
\end{figure}

'''
    if 'performance_chart.png' not in ch6_text:
        ch6_text = ch6_text[:idx] + insert_perf + ch6_text[idx:]

ch6_path.write_text(ch6_text, encoding='utf-8')
print("Successfully patched real diagrams into chapter6.tex")
