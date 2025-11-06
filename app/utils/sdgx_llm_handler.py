import pandas as pd
from typing import Dict, Any, List
import json

try:
    # 尝试导入SDG的LLM模型
    from sdgx.models.LLM.single_table.gpt import SingleTableGPTModel
    from sdgx.data_models.metadata import Metadata
    from sdgx.data_loader import DataLoader
    HAS_SDGX = True
except ImportError:
    HAS_SDGX = False
    print("SDGX LLM models not available. Please install synthetic-data-generator.")

class SDGXLLMHandler:
    def __init__(self):
        """
        初始化SDGX LLM模型处理器
        """
        if not HAS_SDGX:
            raise ImportError("SDGX LLM models not available. Please install synthetic-data-generator.")
        
        self.model = None
        self.model_type = None
    
    def create_model(self, model_type: str, parameters: Dict[str, Any] = None) -> Any:
        """
        创建LLM模型
        
        Args:
            model_type: 模型类型 ("gpt")
            parameters: 模型参数
            
        Returns:
            模型实例
        """
        if parameters is None:
            parameters = {}
            
        if model_type == "gpt":
            # GPT模型
            self.model_type = "gpt"
            self.model = SingleTableGPTModel(
                openai_API_key=parameters.get("openai_API_key", ""),
                openai_API_url=parameters.get("openai_API_url", "https://api.openai.com/v1/"),
                max_tokens=parameters.get("max_tokens", 4000),
                temperature=parameters.get("temperature", 0.1),
                timeout=parameters.get("timeout", 90),
                gpt_model=parameters.get("gpt_model", "gpt-3.5-turbo"),
                query_batch=parameters.get("query_batch", 30)
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
            
        return self.model
    
    def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
        """
        训练LLM模型
        
        Args:
            data: 训练数据
            parameters: 训练参数
        """
        if self.model is None:
            raise ValueError("Model not created. Please call create_model() first.")
        
        if parameters is None:
            parameters = {}
            
        # 创建元数据
        metadata = Metadata.from_dataframe(data)
        
        # 训练模型
        self.model.fit(data, metadata)
    
    def sample(self, num_rows: int, dataset_description: str = "") -> pd.DataFrame:
        """
        生成合成数据
        
        Args:
            num_rows: 生成行数
            dataset_description: 数据集描述
            
        Returns:
            合成数据框
        """
        if self.model is None:
            raise ValueError("Model not fitted. Please call fit() first.")
        
        return self.model.sample(num_rows, dataset_description)
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        获取可用的LLM模型列表
        
        Returns:
            模型信息列表
        """
        return [
            {
                "id": "gpt",
                "name": "GPT (SDGX)",
                "description": "基于GPT的LLM模型"
            }
        ]
    
    def get_model_parameters_template(self) -> Dict[str, Any]:
        """
        获取模型参数模板
        
        Returns:
            参数模板字典
        """
        return {
            "gpt": {
                "openai_API_key": "",
                "openai_API_url": "https://api.openai.com/v1/",
                "max_tokens": 4000,
                "temperature": 0.1,
                "timeout": 90,
                "gpt_model": "gpt-3.5-turbo",
                "query_batch": 30
            }
        }

# 兼容性处理
if not HAS_SDGX:
    class SDGXLLMHandler:
        def __init__(self):
            pass
        
        def create_model(self, model_type: str, parameters: Dict[str, Any] = None):
            raise ImportError("SDGX LLM models not available.")
        
        def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
            raise ImportError("SDGX LLM models not available.")
        
        def sample(self, num_rows: int, dataset_description: str = "") -> pd.DataFrame:
            raise ImportError("SDGX LLM models not available.")
        
        def get_available_models(self) -> List[Dict[str, str]]:
            return []
        
        def get_model_parameters_template(self) -> Dict[str, Any]:
            return {}