import pandas as pd
from typing import Dict, Any, List
import json

# 尝试导入OpenDP
try:
    import opendp.prelude as dp
    from opendp.extras.mbi import AIM, MST
    HAS_OPENDP = True
    # 启用OpenDP的特性
    dp.enable_features("contrib")
except ImportError:
    HAS_OPENDP = False
    print("OpenDP not installed. Please install it with: pip install 'opendp[mbi]'")

class OpenDPHandler:
    def __init__(self):
        """
        初始化OpenDP处理器
        """
        if not HAS_OPENDP:
            raise ImportError("OpenDP is not installed. Please install it with: pip install 'opendp[mbi]'")
        
        self.context = None
        self.privacy_budget = 1.0  # 默认隐私预算
        self.components = {}  # 存储OpenDP组件
        self.contingency_table = None  # 存储差分隐私的列联表
    
    def prepare_context(self, data: pd.DataFrame, privacy_budget: float = 1.0) -> Any:
        """
        为数据准备OpenDP上下文
        
        Args:
            data: 输入数据框
            privacy_budget: 隐私预算
            
        Returns:
            OpenDP上下文对象
        """
        self.privacy_budget = privacy_budget
        
        # 使用Polars处理数据
        import polars as pl
        # 将pandas DataFrame转换为Polars DataFrame
        polars_data = pl.from_pandas(data)
        
        # 创建OpenDP上下文
        context = dp.Context.compositor(
            data=polars_data.lazy(),
            privacy_unit=dp.unit_of(contributions=1),
            privacy_loss=dp.loss_of(epsilon=privacy_budget, delta=1e-7),
        )
        
        self.context = context
        return context
    
    def _extract_metadata(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        提取数据元信息
        
        Args:
            data: 输入数据框
            
        Returns:
            元信息字典
        """
        metadata = {}
        for column in data.columns:
            dtype = str(data[column].dtype)
            if 'int' in dtype or 'float' in dtype:
                metadata[column] = {"type": "numerical", "dtype": dtype}
            elif 'datetime' in dtype:
                metadata[column] = {"type": "datetime", "dtype": dtype}
            else:
                metadata[column] = {"type": "categorical", "dtype": dtype}
        
        return metadata
    
    def create_dp_synthesizer(self, parameters: Dict[str, Any] = None) -> Any:
        """
        创建差分隐私合成器
        
        Args:
            parameters: 合成器参数
            
        Returns:
            OpenDP合成器对象
        """
        if parameters is None:
            parameters = {}
        
        # 提取参数
        algorithm = parameters.get('algorithm', 'AIM')  # 默认使用AIM算法
        epsilon = parameters.get('epsilon', self.privacy_budget)
        
        # 创建合成器
        synthesizer = {
            "algorithm": algorithm,
            "epsilon": epsilon,
            "parameters": parameters
        }
        
        return synthesizer
    
    def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
        """
        训练差分隐私合成器
        
        Args:
            data: 训练数据
            parameters: 训练参数
        """
        if parameters is None:
            parameters = {}
        
        # 准备上下文
        privacy_budget = parameters.get('epsilon', 1.0)
        self.prepare_context(data, privacy_budget)
        
        # 创建合成器
        self.synthesizer = self.create_dp_synthesizer(parameters)
        
        # 根据算法类型进行训练
        if self.synthesizer["algorithm"] == "AIM":
            self._fit_aim(data, parameters)
        elif self.synthesizer["algorithm"] == "MST":
            self._fit_mst(data, parameters)
        else:
            raise ValueError(f"Unsupported algorithm: {self.synthesizer['algorithm']}")
    
    def _fit_aim(self, data: pd.DataFrame, parameters: Dict[str, Any]):
        """
        使用AIM算法训练
        
        Args:
            data: 训练数据
            parameters: 训练参数
        """
        # 使用OpenDP的AIM算法进行训练
        epsilon = parameters.get('epsilon', self.privacy_budget)
        delta = parameters.get('delta', 1e-7)
        
        # 选择所有列进行处理
        columns = list(data.columns)
        
        # 创建AIM算法实例
        aim_algorithm = AIM()
        
        # 构建查询
        query = (
            self.context.query()
            .select(*columns)
            .contingency_table(
                algorithm=aim_algorithm
            )
        )
        
        # 执行查询并获取结果
        self.contingency_table = query.release()
        
        # 保存结果到synthesizer
        self.synthesizer["contingency_table"] = self.contingency_table
    
    def _fit_mst(self, data: pd.DataFrame, parameters: Dict[str, Any]):
        """
        使用MST算法训练
        
        Args:
            data: 训练数据
            parameters: 训练参数
        """
        # 使用OpenDP的MST算法进行训练
        epsilon = parameters.get('epsilon', self.privacy_budget)
        delta = parameters.get('delta', 1e-7)
        
        # 选择所有列进行处理
        columns = list(data.columns)
        
        # 创建MST算法实例
        mst_algorithm = MST()
        
        # 构建查询
        query = (
            self.context.query()
            .select(*columns)
            .contingency_table(
                algorithm=mst_algorithm
            )
        )
        
        # 执行查询并获取结果
        self.contingency_table = query.release()
        
        # 保存结果到synthesizer
        self.synthesizer["contingency_table"] = self.contingency_table
    
    def _apply_dp_to_marginals(self, marginals: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        对边缘分布应用差分隐私保护
        
        Args:
            marginals: 边缘分布
            parameters: 参数
            
        Returns:
            差分隐私保护后的边缘分布
        """
        dp_marginals = {}
        epsilon = parameters.get('epsilon', self.privacy_budget)
        
        for column, distribution in marginals.items():
            if isinstance(distribution, dict):
                # 对分类分布应用拉普拉斯机制
                dp_distribution = {}
                total_epsilon = epsilon / len(distribution)  # 简单的隐私预算分配
                
                for value, probability in distribution.items():
                    # 这里应该使用OpenDP的拉普拉斯机制
                    # 由于简化实现，这里直接添加噪声
                    noise = self._add_laplace_noise(0, 1/total_epsilon)
                    dp_probability = max(0, min(1, probability + noise))  # 确保概率在[0,1]范围内
                    dp_distribution[value] = dp_probability
                
                # 归一化概率分布
                total = sum(dp_distribution.values())
                if total > 0:
                    dp_distribution = {k: v/total for k, v in dp_distribution.items()}
                
                dp_marginals[column] = dp_distribution
            else:
                # 对数值统计信息应用差分隐私保护
                dp_marginals[column] = distribution  # 简化处理
        
        return dp_marginals
    
    def _add_laplace_noise(self, value: float, scale: float) -> float:
        """
        添加拉普拉斯噪声
        
        Args:
            value: 原始值
            scale: 噪声尺度
            
        Returns:
            添加噪声后的值
        """
        # 简化的拉普拉斯噪声生成
        # 实际应用中应该使用OpenDP的噪声生成机制
        import random
        import math
        
        u = random.uniform(-0.5, 0.5)
        return value - scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))
    
    def sample(self, num_rows: int) -> pd.DataFrame:
        """
        生成合成数据
        
        Args:
            num_rows: 生成行数
            
        Returns:
            合成数据框
        """
        if not hasattr(self, 'synthesizer') or self.synthesizer is None:
            raise ValueError("Synthesizer not fitted. Please call fit() first.")
        
        # 根据算法类型生成数据
        if self.synthesizer["algorithm"] == "AIM":
            return self._sample_aim(num_rows)
        elif self.synthesizer["algorithm"] == "MST":
            return self._sample_mst(num_rows)
        else:
            raise ValueError(f"Unsupported algorithm: {self.synthesizer['algorithm']}")
    
    def _sample_aim(self, num_rows: int) -> pd.DataFrame:
        """
        使用AIM算法生成数据
        
        Args:
            num_rows: 生成行数
            
        Returns:
            合成数据框
        """
        if "contingency_table" not in self.synthesizer or self.synthesizer["contingency_table"] is None:
            raise ValueError("AIM synthesizer not properly fitted.")
        
        # 使用OpenDP的合成数据生成功能
        contingency_table = self.synthesizer["contingency_table"]
        synthetic_data = contingency_table.synthesize(rows=num_rows)
        
        # 将Polars DataFrame转换为Pandas DataFrame
        import polars as pl
        if isinstance(synthetic_data, pl.DataFrame):
            return synthetic_data.to_pandas()
        else:
            return synthetic_data
    
    def _sample_mst(self, num_rows: int) -> pd.DataFrame:
        """
        使用MST算法生成数据
        
        Args:
            num_rows: 生成行数
            
        Returns:
            合成数据框
        """
        if "contingency_table" not in self.synthesizer or self.synthesizer["contingency_table"] is None:
            raise ValueError("MST synthesizer not properly fitted.")
        
        # 使用OpenDP的合成数据生成功能
        contingency_table = self.synthesizer["contingency_table"]
        synthetic_data = contingency_table.synthesize(rows=num_rows)
        
        # 将Polars DataFrame转换为Pandas DataFrame
        import polars as pl
        if isinstance(synthetic_data, pl.DataFrame):
            return synthetic_data.to_pandas()
        else:
            return synthetic_data
    
    def get_available_algorithms(self) -> List[Dict[str, str]]:
        """
        获取可用的OpenDP算法列表
        
        Returns:
            算法信息列表
        """
        algorithms = [
            {
                "id": "AIM",
                "name": "AIM Algorithm",
                "description": "基于边缘分布的差分隐私合成算法"
            },
            {
                "id": "MST",
                "name": "MST Algorithm",
                "description": "基于最小生成树的差分隐私合成算法"
            }
        ]
        
        return algorithms
    
    def get_algorithm_parameters_template(self) -> Dict[str, Any]:
        """
        获取算法参数模板
        
        Returns:
            参数模板字典
        """
        template = {
            "AIM": {
                "epsilon": 1.0,
                "delta": 1e-7,
                "max_cells": 1000
            },
            "MST": {
                "epsilon": 1.0,
                "delta": 1e-7,
                "tree_depth": 5
            }
        }
        
        return template

# 兼容性处理
if not HAS_OPENDP:
    class OpenDPHandler:
        def __init__(self):
            pass
        
        def prepare_context(self, data: pd.DataFrame, privacy_budget: float = 1.0):
            raise ImportError("OpenDP is not installed. Please install it with: pip install 'opendp[mbi]'")
        
        def create_dp_synthesizer(self, parameters: Dict[str, Any] = None):
            raise ImportError("OpenDP is not installed. Please install it with: pip install 'opendp[mbi]'")
        
        def fit(self, data: pd.DataFrame, parameters: Dict[str, Any] = None):
            raise ImportError("OpenDP is not installed. Please install it with: pip install 'opendp[mbi]'")
        
        def sample(self, num_rows: int) -> pd.DataFrame:
            raise ImportError("OpenDP is not installed. Please install it with: pip install 'opendp[mbi]'")
        
        def get_available_algorithms(self) -> List[Dict[str, str]]:
            return []
        
        def get_algorithm_parameters_template(self) -> Dict[str, Any]:
            return {}