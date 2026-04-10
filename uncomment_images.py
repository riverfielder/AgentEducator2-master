import re
from pathlib import Path

file_path = Path(r"D:\hxjbs\AgentEducator2-master\thesis\pages\chapter6.tex")
content = file_path.read_text("utf-8")

# Uncomment images
content = re.sub(r'%\s*\\includegraphics', r'\\includegraphics', content)

# Remove placeholder text in captions
content = content.replace("[图片替换占位] 请替换为：", "")

file_path.write_text(content, "utf-8")
print("chapter6.tex updated.")
