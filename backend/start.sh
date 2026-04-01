#!/bin/bash
# 启动后端服务（Gunicorn）
# 使用方式: ./start.sh
# 前提: 已激活虚拟环境 或 venv 目录存在于当前路径下

if [ -f "venv/bin/gunicorn" ]; then
    venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
elif command -v gunicorn &> /dev/null; then
    gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
else
    echo "错误: 未找到 gunicorn，请先安装: pip install gunicorn"
    exit 1
fi
