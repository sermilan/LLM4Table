import pandas as pd
from typing import Dict, Any, List
import json

try:
    # 尝试导入SDG的统计模型
    from sdgx.models.statistics.single_table.gaussian import GaussianMultivariate
    from sdgx.models.statistics.single_table.copula import GaussianCopulaSynthesizerModel
    from sdgx.data_models.metadata import Metadata
    from sdgx.data_loader import DataLoader
    HAS_SDGX = True
except ImportError:
    HAS_SDGX = False
    print("SDGX statistics models not available. Please install synthetic-data-generator.")

class SDGXStatisticsHandler:
    def __init__(self):
        """
        初始化SDGX统计模型处理器
        """
        if not HAS_SDGX:
            raise ImportError("SDGX statistics models not available. Please install synthetic-data-generator.")
        
        self.model = None
        self.model_type = None
    
    def create_model(self, model_type: str, parameters: Dict[str, Any] = None) -> Any:
        """
        创建统计模型
        
        Args:
            model_type: 模型类型 ("gaussian_multivariate" 或 "gaussian_copula")
            parameters: 模型参数
            
        Returns:
            模型实例
        """
        if parameters is None:
            parameters = {}
            
        if model_type == "gaussian_multivariate":
            # 高斯多元分布模型
            self.model_type = "gaussian_multivariate"
            self.model = GaussianMultivariate(
                distribution=parameters.get("distribution", "norm")
            )
        elif model_type == "gaussian_copula":
            # 高斯Copula模型
            self.model_type = "gaussian_copula"
            self.model = GaussianCopulaSynthesizerModel(
                enforce_min_max_values=parameters.get("enforce_min_max_values", True),
                enforce_rounding=parameters.get("enforce_rounding", True),
                default_distribution=parameters.get("default_distribution", "beta")
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
            
        return self.model
    
    def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
        """
        训练统计模型
        
        Args:
            data: 训练数据
            parameters: 训练参数
        """
        if self.model is None:
            raise ValueError("Model not created. Please call create_model() first.")
        
        if parameters is None:
            parameters = {}
            
        # 创建数据加载器和元数据
        # 注意：这里简化处理，实际应用中可能需要更复杂的元数据处理
        metadata = Metadata()
        
        # 对于不同的模型类型，使用不同的fit方法
        if self.model_type == "gaussian_multivariate":
            self.model.fit(data)
        elif self.model_type == "gaussian_copula":
            # 创建数据加载器
            dataloader = DataLoader(data)
            # 训练模型
            self.model.fit(metadata, dataloader)
    
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
        获取可用的统计模型列表
        
        Returns:
            模型信息列表
        """
        return [
            {
                "id": "gaussian_multivariate",
                "name": "Gaussian Multivariate",
                "description": "基于高斯多元分布的统计模型"
            },
            {
                "id": "gaussian_copula",
                "name": "Gaussian Copula",
                "description": "基于高斯Copula的统计模型"
            }
        ]
    
    def get_model_parameters_template(self) -> Dict[str, Any]:
        """
        获取模型参数模板
        
        Returns:
            参数模板字典
        """
        return {
            "gaussian_multivariate": {
                "distribution": "norm"  # 可选: norm, beta, gamma, uniform等
            },
            "gaussian_copula": {
                "default_distribution": "beta",
                "enforce_min_max_values": True,
                "enforce_rounding": True
            }
        }

# 兼容性处理
if not HAS_SDGX:
    class SDGXStatisticsHandler:
        def __init__(self):
            pass
        
        def create_model(self, model_type: str, parameters: Dict[str, Any] = None):
            raise ImportError("SDGX statistics models not available.")
        
        def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
            raise ImportError("SDGX statistics models not available.")
        
        def sample(self, num_rows: int) -> pd.DataFrame:
            raise ImportError("SDGX statistics models not available.")
        
        def get_available_models(self) -> List[Dict[str, str]]:
            return []
        
        def get_model_parameters_template(self) -> Dict[str, Any]:
            return {}