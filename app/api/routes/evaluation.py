from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import os
import json
from app.utils.quality_evaluator import QualityEvaluator
from app.core.config import UPLOAD_DIR

router = APIRouter()

class EvaluationRequest(BaseModel):
    original_table_ids: List[str]  # 原始数据表ID列表
    synthetic_data_path: str  # 合成数据文件路径

class EvaluationResult(BaseModel):
    similarity_score: float  # 相似度得分 (0-1)
    column_correlations: Dict[str, float]  # 各列相关性
    distribution_similarity: Dict[str, float]  # 分布相似度
    privacy_score: float  # 隐私保护得分 (0-1)
    overall_quality: float  # 总体质量得分 (0-1)
    # 为SDMetrics准备的额外字段
    detailed_metrics: Dict[str, Any] = {}  # 详细指标
    visualization_data: Dict[str, Any] = {}  # 可视化数据

@router.post("/evaluate")
async def evaluate_synthetic_data(request: EvaluationRequest):
    """
    评估合成数据质量
    """
    try:
        # 加载原始数据
        original_dataframes = []
        for table_id in request.original_table_ids:
            metadata_file = os.path.join(UPLOAD_DIR, f"{table_id}_metadata.json")
            if not os.path.exists(metadata_file):
                raise HTTPException(status_code=404, detail=f"原始数据表 {table_id} 不存在")
            
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                file_path = metadata.get("file_path")
                
                # 读取数据
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file_path)
                else:
                    raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_path}")
                
                original_dataframes.append(df)
        
        # 加载合成数据
        if not os.path.exists(request.synthetic_data_path):
            raise HTTPException(status_code=404, detail="合成数据文件不存在")
        
        if request.synthetic_data_path.endswith(".csv"):
            synthetic_df = pd.read_csv(request.synthetic_data_path)
        elif request.synthetic_data_path.endswith((".xlsx", ".xls")):
            synthetic_df = pd.read_excel(request.synthetic_data_path)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {request.synthetic_data_path}")
        
        # 执行质量评估
        evaluator = QualityEvaluator()
        evaluation_result = evaluator.evaluate(original_dataframes, synthetic_df)
        
        # 为SDMetrics准备额外的数据
        detailed_metrics = {
            "column_count": len(synthetic_df.columns),
            "row_count": len(synthetic_df),
            "missing_values": synthetic_df.isnull().sum().to_dict(),
            "data_types": {col: str(synthetic_df[col].dtype) for col in synthetic_df.columns}
        }
        
        # 准备可视化数据 - 保留所有可视化数据，不覆盖
        visualization_data = evaluation_result.get("visualization_data", {})
        
        # 确保基本的可视化数据存在
        if "column_names" not in visualization_data:
            visualization_data["column_names"] = list(synthetic_df.columns)
        if "data_shapes" not in visualization_data:
            visualization_data["data_shapes"] = {
                "original_count": sum(len(df) for df in original_dataframes),
                "synthetic_count": len(synthetic_df)
            }
        if "data_types" not in visualization_data:
            visualization_data["data_types"] = {col: str(synthetic_df[col].dtype) for col in synthetic_df.columns}
        
        # 合并结果
        full_result = {
            **evaluation_result,
            "detailed_metrics": detailed_metrics,
            "visualization_data": visualization_data
        }
        
        return {
            "success": True,
            "message": "数据质量评估完成",
            "data": full_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据质量评估失败: {str(e)}")

@router.post("/evaluate/upload")
async def evaluate_with_upload(
    original_table_ids: str,  # JSON字符串格式的ID列表
    synthetic_file: UploadFile = File(...)
):
    """
    通过上传文件评估合成数据质量
    """
    try:
        import json
        table_ids = json.loads(original_table_ids)
        
        # 保存上传的合成数据文件
        file_extension = os.path.splitext(synthetic_file.filename)[1]
        unique_filename = f"eval_temp_{os.urandom(8).hex()}{file_extension}"
        temp_file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(temp_file_path, "wb") as buffer:
            content = await synthetic_file.read()
            buffer.write(content)
        
        # 调用评估函数
        request = EvaluationRequest(
            original_table_ids=table_ids,
            synthetic_data_path=temp_file_path
        )
        
        # 重新调用评估逻辑
        # 加载原始数据
        original_dataframes = []
        for table_id in request.original_table_ids:
            metadata_file = os.path.join(UPLOAD_DIR, f"{table_id}_metadata.json")
            if not os.path.exists(metadata_file):
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                raise HTTPException(status_code=404, detail=f"原始数据表 {table_id} 不存在")
            
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                file_path = metadata.get("file_path")
                
                # 读取数据
                if file_path.endswith(".csv"):
                    df = pd.read_csv(file_path)
                elif file_path.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file_path)
                else:
                    # 清理临时文件
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_path}")
                
                original_dataframes.append(df)
        
        # 加载合成数据
        if not os.path.exists(request.synthetic_data_path):
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise HTTPException(status_code=404, detail="合成数据文件不存在")
        
        if request.synthetic_data_path.endswith(".csv"):
            synthetic_df = pd.read_csv(request.synthetic_data_path)
        elif request.synthetic_data_path.endswith((".xlsx", ".xls")):
            synthetic_df = pd.read_excel(request.synthetic_data_path)
        else:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {request.synthetic_data_path}")
        
        # 执行质量评估
        evaluator = QualityEvaluator()
        evaluation_result = evaluator.evaluate(original_dataframes, synthetic_df)
        
        # 为SDMetrics准备额外的数据
        detailed_metrics = {
            "column_count": len(synthetic_df.columns),
            "row_count": len(synthetic_df),
            "missing_values": synthetic_df.isnull().sum().to_dict(),
            "data_types": {col: str(synthetic_df[col].dtype) for col in synthetic_df.columns}
        }
        
        # 准备可视化数据 - 保留所有可视化数据，不覆盖
        visualization_data = evaluation_result.get("visualization_data", {})
        
        # 确保基本的可视化数据存在
        if "column_names" not in visualization_data:
            visualization_data["column_names"] = list(synthetic_df.columns)
        if "data_shapes" not in visualization_data:
            visualization_data["data_shapes"] = {
                "original_count": sum(len(df) for df in original_dataframes),
                "synthetic_count": len(synthetic_df)
            }
        if "data_types" not in visualization_data:
            visualization_data["data_types"] = {col: str(synthetic_df[col].dtype) for col in synthetic_df.columns}
        
        # 合并结果
        full_result = {
            **evaluation_result,
            "detailed_metrics": detailed_metrics,
            "visualization_data": visualization_data
        }
        
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return {
            "success": True,
            "message": "数据质量评估完成",
            "data": full_result
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="原始数据表ID列表格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据质量评估失败: {str(e)}")

@router.get("/metrics/templates")
async def get_metrics_templates():
    """
    获取SDMetrics评估模板
    """
    templates = {
        "default": {
            "name": "默认评估模板",
            "description": "包含基本的相似度、分布和隐私评估指标",
            "metrics": ["similarity", "distribution", "privacy"]
        },
        "comprehensive": {
            "name": "综合评估模板",
            "description": "包含所有可用的评估指标",
            "metrics": ["similarity", "distribution", "privacy", "correlation", "utility"]
        },
        "custom": {
            "name": "自定义评估模板",
            "description": "允许用户选择特定的评估指标",
            "metrics": []
        }
    }
    
    return {
        "success": True,
        "data": templates
    }