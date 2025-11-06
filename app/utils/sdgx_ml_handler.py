import pandas as pd
from typing import Dict, Any, List
import json

try:
    # 尝试导入SDG的机器学习模型
    from sdgx.models.ml.single_table.ctgan import CTGANSynthesizerModel
    from sdgx.data_models.metadata import Metadata
    from sdgx.data_loader import DataLoader
    HAS_SDGX = True
except ImportError:
    HAS_SDGX = False
    print("SDGX ML models not available. Please install synthetic-data-generator.")

class SDGXMLHandler:
    def __init__(self):
        """
        初始化SDGX机器学习模型处理器
        """
        if not HAS_SDGX:
            raise ImportError("SDGX ML models not available. Please install synthetic-data-generator.")
        
        self.model = None
        self.model_type = None
    
    def create_model(self, model_type: str, parameters: Dict[str, Any] = None) -> Any:
        """
        创建机器学习模型
        
        Args:
            model_type: 模型类型 ("ctgan")
            parameters: 模型参数
            
        Returns:
            模型实例
        """
        if parameters is None:
            parameters = {}
            
        if model_type == "ctgan":
            # CTGAN模型
            self.model_type = "ctgan"
            self.model = CTGANSynthesizerModel(
                embedding_dim=parameters.get("embedding_dim", 128),
                generator_dim=parameters.get("generator_dim", (256, 256)),
                discriminator_dim=parameters.get("discriminator_dim", (256, 256)),
                generator_lr=parameters.get("generator_lr", 2e-4),
                generator_decay=parameters.get("generator_decay", 1e-6),
                discriminator_lr=parameters.get("discriminator_lr", 2e-4),
                discriminator_decay=parameters.get("discriminator_decay", 1e-6),
                batch_size=parameters.get("batch_size", 500),
                discriminator_steps=parameters.get("discriminator_steps", 1),
                log_frequency=parameters.get("log_frequency", True),
                epochs=parameters.get("epochs", 300),
                pac=parameters.get("pac", 10)
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
            
        return self.model
    
    def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
        """
        训练机器学习模型
        
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
        
        # 创建数据加载器
        dataloader = DataLoader(data)
        
        # 训练模型
        self.model.fit(metadata, dataloader, epochs=parameters.get("epochs", 300))
    
    def sample(self, num_rows: int) -> pd.DataFrame:
        """
        生成合成数据
        
        Args:
            num_rows: 生成行数
            
        Returns:
            合成数据框
        """
        if self.model is None:
            raise ValueError("Model not fitted. Please call fit() first.")
        
        return self.model.sample(num_rows)
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        获取可用的机器学习模型列表
        
        Returns:
            模型信息列表
        """
        return [
            {
                "id": "ctgan",
                "name": "CTGAN",
                "description": "条件表格GAN模型"
            }
        ]
    
    def get_model_parameters_template(self) -> Dict[str, Any]:
        """
        获取模型参数模板
        
        Returns:
            参数模板字典
        """
        return {
            "ctgan": {
                "embedding_dim": 128,
                "generator_dim": [256, 256],
                "discriminator_dim": [256, 256],
                "generator_lr": 2e-4,
                "generator_decay": 1e-6,
                "discriminator_lr": 2e-4,
                "discriminator_decay": 1e-6,
                "batch_size": 500,
                "discriminator_steps": 1,
                "log_frequency": True,
                "epochs": 300,
                "pac": 10
            }
        }

# 兼容性处理
if not HAS_SDGX:
    class SDGXMLHandler:
        def __init__(self):
            pass
        
        def create_model(self, model_type: str, parameters: Dict[str, Any] = None):
            raise ImportError("SDGX ML models not available.")
        
        def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
            raise ImportError("SDGX ML models not available.")
        
        def sample(self, num_rows: int) -> pd.DataFrame:
            raise ImportError("SDGX ML models not available.")
        
        def get_available_models(self) -> List[Dict[str, str]]:
            return []
        
        def get_model_parameters_template(self) -> Dict[str, Any]:
            return {}