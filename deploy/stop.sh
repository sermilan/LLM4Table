#!/bin/bash

# LLM4Table 停止脚本

echo "停止 LLM4Table 应用..."

# 进入项目目录
cd ~/LLM4Table

# 停止 PM2 应用
pm2 stop ecosystem.config.js

echo "LLM4Table 应用已停止！"