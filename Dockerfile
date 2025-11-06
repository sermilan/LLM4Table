# 使用 Python 3.10 作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装系统依赖和Python依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制应用代码
COPY . .

# 构建前端应用
RUN cd frontend && npm install && npm run build

# 创建必要的目录
RUN mkdir -p uploads synthetic_data model_cache

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]