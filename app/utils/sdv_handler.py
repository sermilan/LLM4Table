import pandas as pd
from typing import Dict, Any, List
import json

# 尝试导入SDV
try:
    from sdv.single_table import GaussianCopulaSynthesizer
    from sdv.metadata import SingleTableMetadata
    HAS_SDV = True
except ImportError:
    HAS_SDV = False
    print("SDV not installed. Please install it with: pip install sdv")

# 尝试导入SDGX统计模型
try:
    from app.utils.sdgx_statistics_handler import SDGXStatisticsHandler
    HAS_SDGX_STATS = True
except ImportError:
    HAS_SDGX_STATS = False
    print("SDGX statistics handler not available.")

# 尝试导入SDGX机器学习模型
try:
    from app.utils.sdgx_ml_handler import SDGXMLHandler
    HAS_SDGX_ML = True
except ImportError:
    HAS_SDGX_ML = False
    print("SDGX ML handler not available.")

# 尝试导入SDGX LLM模型
try:
    from app.utils.sdgx_llm_handler import SDGXLLMHandler
    HAS_SDGX_LLM = True
except ImportError:
    HAS_SDGX_LLM = False
    print("SDGX LLM handler not available.")

# 尝试导入OpenDP模型
try:
    from app.utils.opendp_handler import OpenDPHandler
    HAS_OPENDP = True
except ImportError:
    HAS_OPENDP = False
    print("OpenDP handler not available.")

class SDVHandler:
    def __init__(self):
        """
        初始化SDV处理器
        """
        if not HAS_SDV:
            raise ImportError("SDV is not installed. Please install it with: pip install sdv")
        
        self.synthesizer = None
        self.metadata = None
        self.opendp_handler = OpenDPHandler() if HAS_OPENDP else None
    
    def prepare_metadata(self, data: pd.DataFrame) -> SingleTableMetadata:
        """
        为数据准备元数据
        
        Args:
            data: 输入数据框
            
        Returns:
            SingleTableMetadata对象
        """
        # 创建元数据对象
        metadata = SingleTableMetadata()
        
        # 自动检测列类型
        metadata.detect_from_dataframe(data)
        
        self.metadata = metadata
        return metadata
    
    def create_synthesizer(self, metadata: SingleTableMetadata, parameters: Dict[str, Any] = None) -> GaussianCopulaSynthesizer:
        """
        创建合成器
        
        Args:
            metadata: 数据元数据
            parameters: 合成器参数
            
        Returns:
            GaussianCopulaSynthesizer对象
        """
        if parameters is None:
            parameters = {}
        
        # 提取训练参数
        training_params = {
            'default_distribution': parameters.get('default_distribution', 'beta'),
            'enforce_min_max_values': parameters.get('enforce_min_max_values', True),
            'enforce_rounding': parameters.get('enforce_rounding', True)
        }
        
        # 创建合成器
        synthesizer = GaussianCopulaSynthesizer(
            metadata,
            **training_params
        )
        
        self.synthesizer = synthesizer
        return synthesizer
    
    def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
        """
        训练合成器
        
        Args:
            data: 训练数据
            parameters: 训练参数
        """
        # 检查是否为SDGX统计模型
        if parameters and parameters.get("provider") == "sdgx_statistics":
            if HAS_SDGX_STATS:
                from app.utils.sdgx_statistics_handler import SDGXStatisticsHandler
                self.sdgx_stats_handler = SDGXStatisticsHandler()
                model_type = parameters.get("model_type", "gaussian_copula")
                self.sdgx_stats_handler.create_model(model_type, parameters)
                self.sdgx_stats_handler.fit(data, parameters)
                return
            else:
                raise ImportError("SDGX statistics models not available.")
        
        # 检查是否为SDGX机器学习模型
        if parameters and parameters.get("provider") == "sdgx_ml":
            if HAS_SDGX_ML:
                from app.utils.sdgx_ml_handler import SDGXMLHandler
                self.sdgx_ml_handler = SDGXMLHandler()
                model_type = parameters.get("model_type", "ctgan")
                self.sdgx_ml_handler.create_model(model_type, parameters)
                self.sdgx_ml_handler.fit(data, parameters)
                return
            else:
                raise ImportError("SDGX ML models not available.")
        
        # 检查是否为SDGX LLM模型
        if parameters and parameters.get("provider") == "sdgx_llm":
            if HAS_SDGX_LLM:
                from app.utils.sdgx_llm_handler import SDGXLLMHandler
                self.sdgx_llm_handler = SDGXLLMHandler()
                model_type = parameters.get("model_type", "gpt")
                self.sdgx_llm_handler.create_model(model_type, parameters)
                self.sdgx_llm_handler.fit(data, parameters)
                return
            else:
                raise ImportError("SDGX LLM models not available.")
        
        # 检查是否为OpenDP模型
        if parameters and parameters.get("provider") == "opendp":
            if HAS_OPENDP:
                from app.utils.opendp_handler import OpenDPHandler
                self.opendp_handler = OpenDPHandler()
                algorithm = parameters.get("algorithm", "AIM")
                self.opendp_handler.fit(data, {"algorithm": algorithm, **parameters})
                return
            else:
                raise ImportError("OpenDP models not available.")
        
        if self.metadata is None:
            self.prepare_metadata(data)
        
        if self.synthesizer is None:
            self.create_synthesizer(self.metadata, parameters)
        
        # 训练合成器
        self.synthesizer.fit(data)
    
    def sample(self, num_rows: int) -> pd.DataFrame:
        """
        生成合成数据
        
        Args:
            num_rows: 生成行数
            
        Returns:
            合成数据框
        """
        # 检查是否为SDGX统计模型
        if hasattr(self, 'sdgx_stats_handler') and self.sdgx_stats_handler is not None:
            return self.sdgx_stats_handler.sample(num_rows)
        
        # 检查是否为SDGX机器学习模型
        if hasattr(self, 'sdgx_ml_handler') and self.sdgx_ml_handler is not None:
            return self.sdgx_ml_handler.sample(num_rows)
        
        # 检查是否为SDGX LLM模型
        if hasattr(self, 'sdgx_llm_handler') and self.sdgx_llm_handler is not None:
            return self.sdgx_llm_handler.sample(num_rows)
        
        # 检查是否为OpenDP模型
        if hasattr(self, 'opendp_handler') and self.opendp_handler is not None:
            return self.opendp_handler.sample(num_rows)
        
        if self.synthesizer is None:
            raise ValueError("Synthesizer not fitted. Please call fit() first.")
        
        return self.synthesizer.sample(num_rows)
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        获取可用的SDV模型列表
        
        Returns:
            模型信息列表
        """
        models = [
            {
                "id": "gaussian_copula",
                "name": "Gaussian Copula",
                "description": "基于高斯Copula的合成模型"
            },
            {
                "id": "ctgan",
                "name": "CTGAN",
                "description": "条件表格GAN模型"
            },
            {
                "id": "copulagan",
                "name": "CopulaGAN",
                "description": "基于Copula的GAN模型"
            }
        ]
        
        # 如果SDGX统计模型可用，添加到模型列表中
        if HAS_SDGX_STATS:
            try:
                sdgx_stats_handler = SDGXStatisticsHandler()
                sdgx_models = sdgx_stats_handler.get_available_models()
                models.extend(sdgx_models)
            except Exception as e:
                print(f"Failed to load SDGX statistics models: {e}")
        
        # 如果SDGX机器学习模型可用，添加到模型列表中
        if HAS_SDGX_ML:
            try:
                sdgx_ml_handler = SDGXMLHandler()
                sdgx_ml_models = sdgx_ml_handler.get_available_models()
                models.extend(sdgx_ml_models)
            except Exception as e:
                print(f"Failed to load SDGX ML models: {e}")
        
        # 如果SDGX LLM模型可用，添加到模型列表中
        if HAS_SDGX_LLM:
            try:
                sdgx_llm_handler = SDGXLLMHandler()
                sdgx_llm_models = sdgx_llm_handler.get_available_models()
                models.extend(sdgx_llm_models)
            except Exception as e:
                print(f"Failed to load SDGX LLM models: {e}")
        
        # 如果OpenDP模型可用，添加到模型列表中
        if HAS_OPENDP:
            try:
                opendp_handler = OpenDPHandler()
                opendp_models = [
                    {
                        "id": "aim_dp",
                        "name": "AIM with Differential Privacy",
                        "description": "基于OpenDP AIM算法的差分隐私合成模型"
                    },
                    {
                        "id": "mst_dp",
                        "name": "MST with Differential Privacy",
                        "description": "基于OpenDP MST算法的差分隐私合成模型"
                    }
                ]
                models.extend(opendp_models)
            except Exception as e:
                print(f"Failed to load OpenDP models: {e}")
        
        return models
    
    def get_model_parameters_template(self) -> Dict[str, Any]:
        """
        获取模型参数模板
        
        Returns:
            参数模板字典
        """
        template = {
            "default_distribution": "beta",
            "enforce_min_max_values": True,
            "enforce_rounding": True,
            "numerical_distributions": {}
        }
        
        # 如果SDGX统计模型可用，添加其参数模板
        if HAS_SDGX_STATS:
            try:
                sdgx_stats_handler = SDGXStatisticsHandler()
                sdgx_template = sdgx_stats_handler.get_model_parameters_template()
                template.update(sdgx_template)
            except Exception as e:
                print(f"Failed to load SDGX statistics templates: {e}")
        
        # 如果SDGX机器学习模型可用，添加其参数模板
        if HAS_SDGX_ML:
            try:
                sdgx_ml_handler = SDGXMLHandler()
                sdgx_ml_template = sdgx_ml_handler.get_model_parameters_template()
                template.update(sdgx_ml_template)
            except Exception as e:
                print(f"Failed to load SDGX ML templates: {e}")
        
        # 如果SDGX LLM模型可用，添加其参数模板
        if HAS_SDGX_LLM:
            try:
                sdgx_llm_handler = SDGXLLMHandler()
                sdgx_llm_template = sdgx_llm_handler.get_model_parameters_template()
                template.update(sdgx_llm_template)
            except Exception as e:
                print(f"Failed to load SDGX LLM templates: {e}")
        
        # 如果OpenDP模型可用，添加其参数模板
        if HAS_OPENDP:
            try:
                opendp_handler = OpenDPHandler()
                opendp_template = opendp_handler.get_algorithm_parameters_template()
                template["opendp"] = opendp_template
            except Exception as e:
                print(f"Failed to load OpenDP templates: {e}")
        
        return template

# 兼容性处理
if not HAS_SDV:
    class SDVHandler:
        def __init__(self):
            pass
        
        def prepare_metadata(self, data: pd.DataFrame):
            raise ImportError("SDV is not installed")
        
        def create_synthesizer(self, metadata: Any, parameters: Dict[str, Any] = None):
            raise ImportError("SDV is not installed")
        
        def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
            raise ImportError("SDV is not installed")
        
        def sample(self, num_rows: int) -> pd.DataFrame:
            raise ImportError("SDV is not installed")
        
        def get_available_models(self) -> List[Dict[str, str]]:
            return []
        
        def get_model_parameters_template(self) -> Dict[str, Any]:
            return {}