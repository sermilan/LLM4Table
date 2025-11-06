#!/bin/bash

# LLM4Table 重启脚本

echo "重启 LLM4Table 应用..."

# 进入项目目录
cd ~/LLM4Table

# 激活虚拟环境
source venv/bin/activate

# 重启 PM2 应用
pm2 restart ecosystem.config.js

echo "LLM4Table 应用已重启！"
echo "使用 'pm2 status' 查看应用状态"
echo "使用 'pm2 logs' 查看应用日志"