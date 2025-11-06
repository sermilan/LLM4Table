import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据上传目录
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# 合成数据目录
SYNTHESIS_DIR = os.path.join(BASE_DIR, "synthetic_data")

# 模型缓存目录
MODEL_CACHE_DIR = os.path.join(BASE_DIR, "model_cache")

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SYNTHESIS_DIR, exist_ok=True)
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# 数据库配置（示例）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# API配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))