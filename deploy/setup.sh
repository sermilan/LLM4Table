#!/bin/bash

# LLM4Table 部署脚本
# 适用于 Ubuntu 24.0

set -e  # 遇到错误时停止执行

echo "开始部署 LLM4Table 应用..."

# 更新系统包
echo "更新系统包..."
sudo apt update

# 安装 Python 3 和 pip（如果尚未安装）
echo "检查并安装 Python 3 和 pip..."
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js 和 npm（用于前端构建）
#echo "安装 Node.js 和 npm..."
#sudo apt install -y nodejs npm

# 升级 npm 到最新版本
#echo "升级 npm..."
#sudo npm install -g npm@latest

# 创建 Python 虚拟环境
echo "创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip install -r requirements.txt

# 确保安装了OpenDP的MBI扩展
echo "安装 OpenDP MBI 扩展..."
pip install 'opendp[mbi]'

# 安装 PM2 用于进程管理
echo "安装 PM2..."
sudo npm install -g pm2

# 构建前端应用
echo "构建前端应用..."
cd frontend

# 安装前端依赖
echo "安装前端依赖..."
npm install

# 构建前端应用
echo "构建前端应用..."
npm run build

cd ..

echo "部署完成！"

echo "使用以下命令启动应用："
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 使用 PM2 启动应用: pm2 start ecosystem.config.js"
echo "3. 查看应用状态: pm2 status"
echo "4. 查看应用日志: pm2 logs"

echo "应用将在 http://localhost:8000 上运行"
echo "前端界面可通过 http://localhost:8000 访问"