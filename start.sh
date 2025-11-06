#!/bin/bash

# LLM4Table 一键启动脚本

set -e

echo "启动 LLM4Table 应用..."

# 检查是否在项目根目录
if [ ! -f "main.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查并安装依赖
if [ ! -f "venv/installed" ]; then
    echo "安装 Python 依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/installed
fi

# 构建前端
echo "构建前端应用..."
cd frontend
npm install
npm run build
cd ..

# 启动后端服务（将提供前端界面）
echo "启动后端服务..."
# 检查是否安装了PM2
if ! command -v pm2 &> /dev/null
then
    echo "安装 PM2..."
    npm install -g pm2
fi

# 使用PM2启动应用
pm2 start ecosystem.config.js

echo "LLM4Table 应用已启动！"
echo "应用界面: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "使用 'pm2 status' 查看应用状态"
echo "使用 'pm2 logs' 查看应用日志"