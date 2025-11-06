# LLM4Table - 基于大语言模型的表格数据合成系统

LLM4Table 是一个基于大语言模型（LLM）的表格数据合成软件，可以生成高质量的合成表格数据，用于数据隐私保护、机器学习训练等场景。

## 功能特性

1. **数据上传** - 支持CSV、Excel等格式的多表数据上传和关联
2. **模型选择** - 支持多种大语言模型（OpenAI GPT系列、LLaMA等）和SDV模型
3. **参数配置** - 可配置模型参数以优化生成效果
4. **数据合成** - 基于LLM和SDV生成高质量合成数据
5. **质量评估** - 全面评估合成数据质量（相似度、分布、隐私等）
6. **数据下载** - 支持合成数据的下载和导出

## 新增功能

### SDV模型集成
- 集成SDV（Synthetic Data Vault）能力，支持多种统计模型
- 支持Gaussian Copula、CTGAN、CopulaGAN等模型
- 提供模型参数自定义配置能力

### 图表可视化功能
- 支持多种图表类型展示数据质量评估结果
- 包括表格、柱状图、曲线图等多种可视化形式
- 不同质量得分使用颜色编码便于识别

### CSV数据预览优化
- 支持表格形式显示CSV数据
- 添加数据搜索功能，便于快速查找
- 表格列支持排序功能
- 优化了预览界面布局和用户体验

## 技术架构

- 后端：FastAPI + Python
- 前端：React + Ant Design
- 数据处理：Pandas, NumPy, Scikit-learn
- LLM集成：OpenAI API, Hugging Face Transformers
- SDV集成：Synthetic Data Vault
- 图表可视化：Recharts
- 部署：PM2

## 部署环境

- 操作系统：Ubuntu 24.0
- Python版本：3.8+

## 安装部署

### 直接部署（推荐）

1. 克隆项目代码：
```bash
git clone <repository-url>
cd LLM4Table
```

2. 运行部署脚本：
```bash
chmod +x deploy/setup.sh
./deploy/setup.sh
```

3. 启动应用：
```bash
chmod +x start.sh
./start.sh
```

应用将使用PM2进行管理，可以通过以下命令管理应用：
```bash
# 查看应用状态
pm2 list

# 停止应用
pm2 stop LLM4Table

# 重启应用
pm2 restart LLM4Table

# 查看应用日志
pm2 logs LLM4Table
```

### 手动部署步骤

1. 克隆项目代码：
```bash
git clone <repository-url>
cd LLM4Table
```

2. 创建虚拟环境并安装依赖：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. 安装前端依赖并构建：
```bash
cd frontend
npm install
npm run build
cd ..
```

4. 启动应用：
```bash
pm2 start ecosystem.config.js
```

## 问题修复记录

### Excel文件上传支持
- 问题：上传.xlsx文件时出现"Missing optional dependency 'openpyxl'"错误
- 解决方案：在requirements.txt中添加openpyxl依赖

## 访问应用

启动服务后，访问以下URL：
- 应用界面: http://localhost:8000
- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 前端构建故障排除

如果在构建前端应用时遇到问题，请尝试以下解决方案：

1. 确保已安装Node.js和npm
2. 删除node_modules目录并重新安装依赖：
   ```bash
   cd frontend
   rm -rf node_modules
   npm install
   ```
3. 检查index.html文件是否存在
4. 检查Ant Design样式导入问题：
   - Ant Design 5.x版本不需要在CSS中手动导入样式
   - 样式已在main.jsx中通过JavaScript导入

## 使用说明

1. 上传原始数据表格
2. 选择和配置合适的LLM或SDV模型
3. 设置合成参数并启动数据生成任务
4. 监控任务进度并等待完成
5. 评估生成数据的质量
6. 下载合成数据

## 目录结构

```
LLM4Table/
├── app/                 # 后端应用代码
│   ├── api/            # API路由
│   │   └── routes/     # 各模块路由
│   ├── core/           # 核心配置
│   ├── models/         # 数据模型
│   └── utils/          # 工具函数
├── frontend/           # 前端应用代码
│   ├── src/            # 前端源代码
│   └── package.json    # 前端依赖
├── uploads/            # 上传文件存储目录
├── synthetic_data/     # 合成数据存储目录
├── model_cache/        # 模型缓存目录
├── deploy/             # 部署脚本
├── main.py             # 应用入口
├── requirements.txt    # 依赖包列表
├── ecosystem.config.js # PM2配置文件
├── start.sh            # 启动脚本
└── README.md           # 项目说明文档
```

## 开发计划

- [x] 后端API框架搭建
- [x] 数据上传和管理功能
- [x] 模型配置和管理功能
- [x] 数据合成核心功能
- [x] 质量评估功能
- [x] 前端界面开发
- [x] 数据表详情查看功能
- [x] 图表可视化功能
- [x] CSV数据预览优化
- [x] Excel文件上传支持
- [x] SDV模型集成
- [ ] LLM模型集成优化
- [ ] 数据关联关系处理
- [ ] 高级参数配置
- [ ] 用户权限管理

## 贡献指南

欢迎提交Issue和Pull Request来改进本项目。

## 许可证

[MIT License](LICENSE)