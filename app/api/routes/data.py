from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd
import os
import uuid
from app.core.config import UPLOAD_DIR
from app.models.data_model import DataTable, DataUploadResponse

router = APIRouter()

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DataUploadResponse)
async def upload_data(
    file: UploadFile = File(...),
    table_name: str = Form(...),
    description: str = Form(None)
):
    """
    上传表格数据文件
    """
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 读取数据以验证格式
        if file_extension.lower() in ['.csv']:
            df = pd.read_csv(file_path)
        elif file_extension.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 创建数据表记录
        data_table = DataTable(
            id=str(uuid.uuid4()),
            table_name=table_name,
            file_path=file_path,
            file_name=file.filename,
            description=description,
            columns=df.columns.tolist(),
            row_count=len(df),
            column_count=len(df.columns)
        )
        
        # 这里应该保存到数据库，暂时保存到文件
        metadata_file = os.path.join(UPLOAD_DIR, f"{data_table.id}_metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(data_table.json())
        
        return DataUploadResponse(
            success=True,
            message="数据上传成功",
            data=data_table
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/list")
async def list_data_tables():
    """
    列出所有上传的数据表
    """
    try:
        data_tables = []
        for filename in os.listdir(UPLOAD_DIR):
            if filename.endswith("_metadata.json"):
                metadata_file = os.path.join(UPLOAD_DIR, filename)
                with open(metadata_file, "r", encoding="utf-8") as f:
                    import json
                    data = json.load(f)
                    data_tables.append(data)
        return {"success": True, "data": data_tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据表列表失败: {str(e)}")

@router.get("/{table_id}")
async def get_data_table(table_id: str):
    """
    获取指定数据表的信息
    """
    try:
        metadata_file = os.path.join(UPLOAD_DIR, f"{table_id}_metadata.json")
        if not os.path.exists(metadata_file):
            raise HTTPException(status_code=404, detail="数据表不存在")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)
            return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据表信息失败: {str(e)}")

@router.get("/{table_id}/preview")
async def preview_data_table(
    table_id: str, 
    limit: int = Query(100, description="预览行数", ge=1, le=10000),
    offset: int = Query(0, description="偏移量", ge=0)
):
    """
    预览指定数据表的内容
    
    Args:
        table_id: 数据表ID
        limit: 预览行数，最大10000
        offset: 偏移量
    """
    try:
        # 获取数据表元数据
        metadata_file = os.path.join(UPLOAD_DIR, f"{table_id}_metadata.json")
        if not os.path.exists(metadata_file):
            raise HTTPException(status_code=404, detail="数据表不存在")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            import json
            metadata = json.load(f)
        
        file_path = metadata.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="数据文件不存在")
        
        # 读取数据文件的指定行数
        if file_path.endswith(".csv"):
            # 对于CSV文件，可以使用skiprows和nrows参数
            df = pd.read_csv(file_path, skiprows=offset, nrows=limit)
        elif file_path.endswith((".xlsx", ".xls")):
            # 对于Excel文件，需要先读取再切片
            df = pd.read_excel(file_path)
            df = df.iloc[offset:offset+limit] if offset < len(df) else pd.DataFrame()
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 转换为JSON格式
        data = df.to_dict(orient="records")
        columns = df.columns.tolist()
        
        return {
            "success": True,
            "data": {
                "columns": columns,
                "rows": data
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览数据表失败: {str(e)}")

@router.delete("/{table_id}")
async def delete_data_table(table_id: str):
    """
    删除指定数据表
    """
    try:
        metadata_file = os.path.join(UPLOAD_DIR, f"{table_id}_metadata.json")
        if not os.path.exists(metadata_file):
            raise HTTPException(status_code=404, detail="数据表不存在")
        
        # 读取元数据获取文件路径
        with open(metadata_file, "r", encoding="utf-8") as f:
            import json
            data = json.load(f)
            data_file_path = data.get("file_path")
        
        # 删除数据文件和元数据文件
        if os.path.exists(data_file_path):
            os.remove(data_file_path)
        os.remove(metadata_file)
        
        return {"success": True, "message": "数据表删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据表失败: {str(e)}")