# LLM4Table 项目结构说明

## 目录结构

```
LLM4Table/
├── app/                    # 后端应用代码
│   ├── api/               # API路由
│   │   └── routes/        # 各模块路由
│   │       ├── data.py    # 数据管理路由
│   │       ├── model.py   # 模型管理路由
│   │       ├── synthesis.py# 数据合成路由
│   │       └── evaluation.py# 质量评估路由
│   ├── core/              # 核心配置
│   │   └── config.py      # 应用配置
│   ├── models/            # 数据模型
│   │   └── data_model.py  # 数据模型定义
│   └── utils/             # 工具函数
│       ├── data_synthesizer.py # 数据合成器
│       └── quality_evaluator.py # 质量评估器
├── frontend/              # 前端应用代码
│   ├── src/               # 前端源代码
│   │   ├── components/    # React组件
│   │   │   ├── DataUpload.jsx     # 数据上传组件
│   │   │   ├── ModelSelection.jsx # 模型选择组件
│   │   │   ├── DataSynthesis.jsx  # 数据合成组件
│   │   │   ├── QualityEvaluation.jsx # 质量评估组件
│   │   │   └── DataDownload.jsx   # 数据下载组件
│   │   ├── App.jsx        # 主应用组件
│   │   ├── App.css        # 应用样式
│   │   ├── main.jsx       # 入口文件
│   │   └── index.css      # 全局样式
│   ├── package.json       # 前端依赖
│   ├── vite.config.js     # Vite配置
│   └── ...                # 其他前端配置文件
├── uploads/               # 上传文件存储目录
├── synthetic_data/        # 合成数据存储目录
├── model_cache/           # 模型缓存目录
├── deploy/                # 部署脚本
│   ├── setup.sh           # 安装部署脚本
│   ├── start.sh           # 启动脚本
│   ├── stop.sh            # 停止脚本
│   └── restart.sh         # 重启脚本
├── main.py                # 应用入口
├── requirements.txt       # Python依赖包列表
├── start.sh               # 一键启动脚本
├── ecosystem.config.js    # PM2配置文件
├── README.md              # 项目说明文档
└── PROJECT_STRUCTURE.md   # 项目结构说明
```

## 核心模块说明

### 1. 数据管理模块 (Data Management)
- **文件**: `app/api/routes/data.py`
- **功能**: 
  - 上传CSV/Excel格式的数据表
  - 管理已上传的数据表（查看、删除）
  - 存储数据表元信息
  - 提供数据预览功能

### 2. 模型管理模块 (Model Management)
- **文件**: `app/api/routes/model.py`
- **功能**: 
  - 配置和管理LLM模型
  - 支持OpenAI和Hugging Face模型
  - 模型参数配置

### 3. 数据合成模块 (Data Synthesis)
- **文件**: `app/api/routes/synthesis.py`
- **功能**: 
  - 基于LLM生成合成数据
  - 支持多表关联合成
  - 异步任务处理

### 4. 质量评估模块 (Quality Evaluation)
- **文件**: `app/api/routes/evaluation.py`
- **功能**: 
  - 评估合成数据质量
  - 计算相似度、分布、隐私等指标
  - 提供可视化评估结果

### 5. 工具类模块 (Utils)
- **文件**: 
  - `app/utils/data_synthesizer.py`
  - `app/utils/quality_evaluator.py`
- **功能**: 
  - 核心算法实现
  - 数据处理和分析

## 前端组件说明

### 1. 数据上传组件 (DataUpload)
- 文件选择和上传
- 已上传数据表管理
- 数据表详情查看（包含实际数据预览）

### 2. 模型选择组件 (ModelSelection)
- 模型配置和选择
- 参数设置

### 3. 数据合成组件 (DataSynthesis)
- 合成任务配置和启动
- 任务进度监控

### 4. 质量评估组件 (QualityEvaluation)
- 数据质量评估
- 评估结果展示

### 5. 数据下载组件 (DataDownload)
- 合成数据下载
- 结果预览

## 部署相关

### 脚本文件
- `deploy/setup.sh`: 完整安装部署脚本
- `start.sh`: 应用启动脚本（使用PM2管理）
- `deploy/stop.sh`: 应用停止脚本
- `deploy/restart.sh`: 应用重启脚本

### 配置文件
- `ecosystem.config.js`: PM2配置文件