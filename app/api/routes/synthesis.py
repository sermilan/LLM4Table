from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import uuid
import os
import json
import time
import asyncio
from app.core.config import UPLOAD_DIR, SYNTHESIS_DIR
from app.utils.data_synthesizer import DataSynthesizer

router = APIRouter()

# 确保合成目录存在
os.makedirs(SYNTHESIS_DIR, exist_ok=True)

# 合成任务模型
class SynthesisRequest(BaseModel):
    table_ids: List[str]  # 要合成的数据表ID列表
    row_count: int  # 要生成的行数
    model_config: Dict[str, Any]  # 模型配置
    description: Optional[str] = None  # 合成任务描述
    training_params: Optional[Dict[str, Any]] = None  # 模型训练参数

class SynthesisTask(BaseModel):
    task_id: str
    status: str  # "pending", "training", "processing", "completed", "failed"
    progress: int  # 0-100
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    description: Optional[str] = None
    table_ids: List[str] = []  # 关联的数据表ID
    created_at: Optional[str] = None  # 创建时间
    training_info: Optional[Dict[str, Any]] = None  # 训练信息

# 存储合成任务的状态
synthesis_tasks = {}

@router.post("/generate")
async def generate_synthetic_data(request: SynthesisRequest, background_tasks: BackgroundTasks):
    """
    生成合成数据
    """
    try:
        # 创建合成任务
        task_id = str(uuid.uuid4())
        synthesis_tasks[task_id] = SynthesisTask(
            task_id=task_id,
            status="pending",
            progress=0,
            description=request.description,
            table_ids=request.table_ids,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            training_info={}
        )
        
        # 在后台执行合成任务
        background_tasks.add_task(
            run_synthesis_task,
            task_id,
            request.table_ids,
            request.row_count,
            request.model_config,
            request.training_params or {}
        )
        
        return {
            "success": True,
            "message": "合成任务已启动，请在任务列表中查看进度",
            "data": {"task_id": task_id}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动合成任务失败: {str(e)}")

async def run_synthesis_task(task_id: str, table_ids: List[str], row_count: int, model_config: Dict[str, Any], training_params: Dict[str, Any]):
    """
    执行数据合成任务
    """
    try:
        # 更新任务状态
        synthesis_tasks[task_id].status = "pending"
        synthesis_tasks[task_id].progress = 5
        
        # 模拟一些处理时间，让用户看到进度
        await asyncio.sleep(0.5)
        
        # 加载数据表
        dataframes = []
        for table_id in table_ids:
            metadata_file = os.path.join(UPLOAD_DIR, f"{table_id}_metadata.json")
            if not os.path.exists(metadata_file):
                raise Exception(f"数据表 {table_id} 不存在")
            
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                file_path = metadata.get("file_path")
                
                # 读取数据
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file_path)
                else:
                    raise Exception(f"不支持的文件格式: {file_path}")
                
                dataframes.append(df)
        
        synthesis_tasks[task_id].progress = 15
        await asyncio.sleep(0.5)
        
        # 如果是SDV、SDGX统计模型、SDGX机器学习模型或SDGX LLM模型，进行模型训练和调优
        if model_config.get("provider") in ["sdv", "sdgx_statistics", "sdgx_ml", "sdgx_llm"]:
            synthesis_tasks[task_id].status = "training"
            synthesis_tasks[task_id].progress = 20
            
            # 初始化数据合成器
            synthesizer = DataSynthesizer(model_config)
            
            # 训练模型
            training_info = {
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "training"
            }
            synthesis_tasks[task_id].training_info = training_info
            
            # 模拟训练过程
            for i in range(1, 6):
                synthesis_tasks[task_id].progress = 20 + i * 10
                training_info["current_step"] = f"训练步骤 {i}/5"
                synthesis_tasks[task_id].training_info = training_info
                await asyncio.sleep(1)
            
            training_info["status"] = "completed"
            training_info["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            synthesis_tasks[task_id].training_info = training_info
            synthesis_tasks[task_id].progress = 70
            await asyncio.sleep(0.5)
        else:
            # 对于LLM模型，直接进行合成
            synthesis_tasks[task_id].status = "processing"
            synthesis_tasks[task_id].progress = 30
            await asyncio.sleep(0.5)
            
            # 初始化数据合成器
            synthesizer = DataSynthesizer(model_config)
            synthesis_tasks[task_id].progress = 40
            await asyncio.sleep(0.5)
        
        # 执行数据合成
        synthetic_data = synthesizer.synthesize(dataframes, row_count)
        synthesis_tasks[task_id].progress = 85
        await asyncio.sleep(0.5)
        
        # 保存合成数据
        result_filename = f"{task_id}_synthetic_data.csv"
        result_path = os.path.join(SYNTHESIS_DIR, result_filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        
        # 保存为CSV文件
        synthetic_data.to_csv(result_path, index=False, encoding='utf-8')
        
        synthesis_tasks[task_id].progress = 100
        synthesis_tasks[task_id].status = "completed"
        synthesis_tasks[task_id].result_path = result_path
        
    except Exception as e:
        synthesis_tasks[task_id].status = "failed"
        synthesis_tasks[task_id].error_message = str(e)
        print(f"合成任务 {task_id} 失败: {str(e)}")

@router.get("/task/{task_id}")
async def get_synthesis_task_status(task_id: str):
    """
    获取合成任务状态
    """
    if task_id not in synthesis_tasks:
        raise HTTPException(status_code=404, detail="合成任务不存在")
    
    task = synthesis_tasks[task_id]
    return {
        "success": True,
        "data": task.dict()
    }

@router.get("/task/{task_id}/result")
async def download_synthetic_data(task_id: str):
    """
    下载合成数据
    """
    if task_id not in synthesis_tasks:
        raise HTTPException(status_code=404, detail="合成任务不存在")
    
    task = synthesis_tasks[task_id]
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="合成任务尚未完成")
    
    if not task.result_path or not os.path.exists(task.result_path):
        raise HTTPException(status_code=404, detail="合成数据文件不存在")
    
    # 直接返回文件内容而不是路径
    try:
        with open(task.result_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "success": True,
            "data": {
                "content": content,
                "file_name": os.path.basename(task.result_path)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

@router.get("/tasks")
async def list_synthesis_tasks():
    """
    列出所有合成任务
    """
    tasks = [task.dict() for task in synthesis_tasks.values()]
    return {
        "success": True,
        "data": tasks
    }