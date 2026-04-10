import pathlib

ch6_path = pathlib.Path(r'D:\hxjbs\AgentEducator2-master\thesis\pages\chapter6.tex')
ch6_text = ch6_path.read_text(encoding='utf-8')

# Fix UI Sandbox image reference
ch6_text = ch6_text.replace(r'{logo/ui_sandbox.png}', r'{code_training.png}')
ch6_text = ch6_text.replace(r'% 请用户截取一张：左侧有对话辅导、右侧有代码编辑器和代码运行结果效果的图片，命名为 ui_sandbox.png 放入 logo 或 images 文件夹', r'% 使用真实的代码实训图 code_training.png')

# Fix UI Video image reference
ch6_text = ch6_text.replace(r'{logo/ui_video.png}', r'{video_qa.png}')
ch6_text = ch6_text.replace(r'% 请用户截取一张：视频播放界面与右侧问答流联动的高保真图片，命名为 ui_video.png', r'% 使用真实的视频QA图 video_qa.png')

# Fix UI Recommend image reference - we leave this as a prompt, unless there's an image. There is no `recommend_*.png`, so maybe we keep it as a todo or ask the user to provide it. Wait, maybe I can just ask the user if they've taken `ui_recommend.png`.
# For the performance chart, I need to add it to the Performance Testing section
perf_text = r'''得出量化性能指标（压测性能监控报告详见图 \ref{fig:perf_chart}）：

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.85\textwidth,keepaspectratio]{performance_chart.png} 
  \caption{基于 Locust 的大模型沙箱与全站业务并发压测性能报告}
  \label{fig:perf_chart}
\end{figure}

\begin{itemize}'''

ch6_text = ch6_text.replace(r'''得出量化性能指标：

\begin{itemize}''', perf_text)


# For whitebox_test.png, maybe I shouldn't just leave it unused. Let's add it to the black-box or white-box test matrix section. "功能测试：黑盒等价类测试矩阵"
whitebox_text = r'''该矩阵全面覆盖了安全隔离与语法树前置拦截路径，实现了业务级 $100\%$ 的验证通过率。测试平台的管理记录（功能及白盒执行拦截日志）如图 \ref{fig:whitebox} 所示。

\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.85\textwidth,keepaspectratio]{whitebox_test.png} 
  \caption{系统实训模块沙箱隔离黑白盒测试与日志反馈截图}
  \label{fig:whitebox}
\end{figure}

\section{系统核心界面与功能展示}'''

ch6_text = ch6_text.replace(r'''该矩阵全面覆盖了安全隔离与死锁熔断及语法树前置拦截路径，实现了业务级 $100\%$ 的验证通过率。

\section{系统核心界面与功能展示}''', whitebox_text)


ch6_path.write_text(ch6_text, encoding='utf-8')
print("Patched Chapter 6 images.")
