#!/bin/bash

# LLM4Table Docker 部署脚本
# 适用于 Ubuntu 24.0

set -e  # 遇到错误时停止执行

echo "开始使用 Docker 部署 LLM4Table 应用..."

# 检查是否安装了 Docker
if ! command -v docker &> /dev/null
then
    echo "Docker 未安装，正在安装 Docker..."
    sudo apt update
    sudo apt install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "Docker 安装完成，请重新登录或运行 'newgrp docker' 后再次运行此脚本"
    exit 1
fi

# 检查是否安装了 Docker Compose
if ! command -v docker-compose &> /dev/null
then
    echo "Docker Compose 未安装，正在安装..."
    sudo apt install -y docker-compose
fi

# 进入项目目录
cd ~/LLM4Table

# 构建并启动 Docker 容器
echo "构建并启动 Docker 容器..."
sudo docker-compose up -d --build

echo "Docker 部署完成！"

echo "应用将在以下地址运行："
echo "API 后端: http://localhost:8000"
echo "前端界面: http://localhost:3000"

echo "使用以下命令管理容器："
echo "查看容器状态: docker-compose ps"
echo "查看日志: docker-compose logs"
echo "停止容器: docker-compose down"