#!/bin/bash

# 前端构建测试脚本

echo "开始测试前端构建..."

# 检查必要文件是否存在
if [ ! -f "frontend/index.html" ]; then
    echo "错误: frontend/index.html 文件不存在"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo "错误: frontend/package.json 文件不存在"
    exit 1
fi

if [ ! -d "frontend/src" ]; then
    echo "错误: frontend/src 目录不存在"
    exit 1
fi

echo "所有必要文件都存在"

# 检查是否安装了Node.js
if ! command -v node &> /dev/null
then
    echo "警告: Node.js 未安装，将使用Docker进行构建测试"
    # 使用Docker进行构建测试
    if command -v docker &> /dev/null
    then
        echo "使用Docker构建前端应用..."
        docker build -f Dockerfile.frontend -t llm4table-frontend-test .
        if [ $? -eq 0 ]; then
            echo "Docker构建成功"
        else
            echo "Docker构建失败"
            exit 1
        fi
    else
        echo "错误: 未安装Docker，无法进行构建测试"
        exit 1
    fi
else
    echo "Node.js 版本: $(node --version)"
    echo "NPM 版本: $(npm --version)"
    
    # 尝试构建前端
    echo "构建前端应用..."
    cd frontend
    npm install
    npm run build
    
    if [ $? -eq 0 ]; then
        echo "前端构建成功"
    else
        echo "前端构建失败"
        exit 1
    fi
fi

echo "前端构建测试完成"