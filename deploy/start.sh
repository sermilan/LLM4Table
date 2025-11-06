#!/bin/bash

# LLM4Table 启动脚本

set -e

echo "启动 LLM4Table 应用..."

# 进入项目目录
cd ~/LLM4Table

# 激活虚拟环境
source venv/bin/activate

# 使用 PM2 启动应用
pm2 start ecosystem.config.js

# 保存 PM2 进程列表
pm2 save

# 设置 PM2 开机自启
pm2 startup

echo "LLM4Table 应用已启动！"
echo "使用 'pm2 status' 查看应用状态"
echo "使用 'pm2 logs' 查看应用日志"