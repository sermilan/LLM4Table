from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import data, model, synthesis, evaluation
from app.api.routes import interactive_evaluation
import os

app = FastAPI(title="LLM4Table - 表格数据合成系统", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(model.router, prefix="/api/model", tags=["model"])
app.include_router(synthesis.router, prefix="/api/synthesis", tags=["synthesis"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(interactive_evaluation.router, prefix="/api/interactive-evaluation", tags=["interactive-evaluation"])

# 提供前端静态文件
if os.path.exists("frontend/dist"):
    # 挂载静态文件目录，确保在通配符路由之前
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    # 处理前端路由 - 注意API路由优先级更高
    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # 检查请求的是否是API路径
        if full_path.startswith("api/"):
            # 让API路由处理
            raise HTTPException(status_code=404, detail="API path should be handled by API router")
        
        # 检查请求的文件是否存在
        file_path = f"frontend/dist/{full_path}"
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            return FileResponse(file_path)
        # 否则返回index.html以支持前端路由
        index_path = "frontend/dist/index.html"
        if os.path.exists(index_path):
            return FileResponse(index_path)
        # 如果没有前端文件，返回API信息
        return {"message": "欢迎使用LLM4Table - 基于大语言模型的表格数据合成系统"}
else:
    print("前端静态文件目录不存在，将不提供前端界面")
    
    @app.get("/")
    async def root():
        return {"message": "欢迎使用LLM4Table - 基于大语言模型的表格数据合成系统"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)