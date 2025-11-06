import pandas as pd
import numpy as np
from typing import List, Dict, Any
import random
import os
import json

# 尝试导入SDV
try:
    from app.utils.sdv_handler import SDVHandler
    HAS_SDV = True
except ImportError:
    HAS_SDV = False
    print("SDV handler not available")

# 尝试导入SDGX统计模型
try:
    from app.utils.sdgx_statistics_handler import SDGXStatisticsHandler
    HAS_SDGX_STATS = True
except ImportError:
    HAS_SDGX_STATS = False
    print("SDGX statistics handler not available")

# 尝试导入SDGX机器学习模型
try:
    from app.utils.sdgx_ml_handler import SDGXMLHandler
    HAS_SDGX_ML = True
except ImportError:
    HAS_SDGX_ML = False
    print("SDGX ML handler not available")

# 尝试导入SDGX LLM模型
try:
    from app.utils.sdgx_llm_handler import SDGXLLMHandler
    HAS_SDGX_LLM = True
except ImportError:
    HAS_SDGX_LLM = False
    print("SDGX LLM handler not available")

# 尝试导入OpenDP模型
try:
    from app.utils.opendp_handler import OpenDPHandler
    HAS_OPENDP = True
except ImportError:
    HAS_OPENDP = False
    print("OpenDP handler not available")

class DataSynthesizer:
    def __init__(self, model_config: Dict[str, Any]):
        """
        初始化数据合成器
        
        Args:
            model_config: 模型配置字典
        """
        self.model_config = model_config
        self.model_name = model_config.get("model_name", "default")
        self.provider = model_config.get("provider", "default")
        self.parameters = model_config.get("parameters", {})
        self.sdv_handler = SDVHandler() if HAS_SDV and self.provider == "sdv" else None
        self.sdgx_stats_handler = SDGXStatisticsHandler() if HAS_SDGX_STATS and self.provider == "sdgx_statistics" else None
        self.sdgx_ml_handler = SDGXMLHandler() if HAS_SDGX_ML and self.provider == "sdgx_ml" else None
        self.sdgx_llm_handler = SDGXLLMHandler() if HAS_SDGX_LLM and self.provider == "sdgx_llm" else None
        self.opendp_handler = OpenDPHandler() if HAS_OPENDP and self.provider == "opendp" else None
    
    def synthesize(self, dataframes: List[pd.DataFrame], row_count: int, training_params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        基于输入数据框列表生成合成数据
        
        Args:
            dataframes: 原始数据框列表
            row_count: 要生成的行数
            training_params: 模型训练参数
            
        Returns:
            合成的数据框
        """
        if not dataframes:
            raise ValueError("至少需要一个数据框")
        
        # 如果使用SDV模型，使用SDV进行合成
        if self.provider == "sdv" and self.sdv_handler:
            return self._synthesize_with_sdv(dataframes[0], row_count, training_params or {})
        
        # 如果使用SDGX统计模型，使用SDGX进行合成
        if self.provider == "sdgx_statistics" and self.sdgx_stats_handler:
            return self._synthesize_with_sdgx_statistics(dataframes[0], row_count, training_params or {})
        
        # 如果使用SDGX机器学习模型，使用SDGX进行合成
        if self.provider == "sdgx_ml" and self.sdgx_ml_handler:
            return self._synthesize_with_sdgx_ml(dataframes[0], row_count, training_params or {})
        
        # 如果使用SDGX LLM模型，使用SDGX进行合成
        if self.provider == "sdgx_llm" and self.sdgx_llm_handler:
            return self._synthesize_with_sdgx_llm(dataframes[0], row_count, training_params or {})
        
        # 如果使用OpenDP模型，使用OpenDP进行合成
        if self.provider == "opendp" and self.opendp_handler:
            return self._synthesize_with_opendp(dataframes[0], row_count, training_params or {})
        
        # 合并所有数据框以分析整体模式
        combined_df = pd.concat(dataframes, ignore_index=True) if len(dataframes) > 1 else dataframes[0]
        
        # 创建空的合成数据框
        synthetic_df = pd.DataFrame()
        
        # 对每一列生成合成数据
        for column in combined_df.columns:
            synthetic_df[column] = self._generate_column_data_with_llm(
                combined_df[column], 
                row_count,
                column
            )
        
        return synthetic_df
    
    def _synthesize_with_sdv(self, data: pd.DataFrame, row_count: int, training_params: Dict[str, Any]) -> pd.DataFrame:
        """
        使用SDV生成合成数据
        
        Args:
            data: 原始数据框
            row_count: 要生成的行数
            training_params: 模型训练参数
            
        Returns:
            合成的数据框
        """
        if not self.sdv_handler:
            raise ValueError("SDV handler not available")
        
        try:
            # 训练SDV模型（使用训练参数）
            self.sdv_handler.fit(data, {**self.parameters, **training_params})
            
            # 生成合成数据
            synthetic_data = self.sdv_handler.sample(row_count)
            
            return synthetic_data
        except Exception as e:
            raise ValueError(f"SDV合成失败: {str(e)}")
    
    def _synthesize_with_sdgx_statistics(self, data: pd.DataFrame, row_count: int, training_params: Dict[str, Any]) -> pd.DataFrame:
        """
        使用SDGX统计模型生成合成数据
        
        Args:
            data: 原始数据框
            row_count: 要生成的行数
            training_params: 模型训练参数
            
        Returns:
            合成的数据框
        """
        if not self.sdgx_stats_handler:
            raise ValueError("SDGX statistics handler not available")
        
        try:
            # 获取模型类型
            model_type = self.model_config.get("model_name", "gaussian_copula")
            
            # 创建SDGX统计模型
            self.sdgx_stats_handler.create_model(model_type, {**self.parameters, **training_params})
            
            # 训练SDGX统计模型
            self.sdgx_stats_handler.fit(data, {**self.parameters, **training_params})
            
            # 生成合成数据
            synthetic_data = self.sdgx_stats_handler.sample(row_count)
            
            return synthetic_data
        except Exception as e:
            raise ValueError(f"SDGX统计模型合成失败: {str(e)}")
    
    def _synthesize_with_sdgx_ml(self, data: pd.DataFrame, row_count: int, training_params: Dict[str, Any]) -> pd.DataFrame:
        """
        使用SDGX机器学习模型生成合成数据
        
        Args:
            data: 原始数据框
            row_count: 要生成的行数
            training_params: 模型训练参数
            
        Returns:
            合成的数据框
        """
        if not self.sdgx_ml_handler:
            raise ValueError("SDGX ML handler not available")
        
        try:
            # 获取模型类型
            model_type = self.model_config.get("model_name", "ctgan")
            
            # 创建SDGX机器学习模型
            self.sdgx_ml_handler.create_model(model_type, {**self.parameters, **training_params})
            
            # 训练SDGX机器学习模型
            self.sdgx_ml_handler.fit(data, {**self.parameters, **training_params})
            
            # 生成合成数据
            synthetic_data = self.sdgx_ml_handler.sample(row_count)
            
            return synthetic_data
        except Exception as e:
            raise ValueError(f"SDGX机器学习模型合成失败: {str(e)}")
    
    def _synthesize_with_sdgx_llm(self, data: pd.DataFrame, row_count: int, training_params: Dict[str, Any]) -> pd.DataFrame:
        """
        使用SDGX LLM模型生成合成数据
        
        Args:
            data: 原始数据框
            row_count: 要生成的行数
            training_params: 模型训练参数
            
        Returns:
            合成的数据框
        """
        if not self.sdgx_llm_handler:
            raise ValueError("SDGX LLM handler not available")
        
        try:
            # 获取模型类型
            model_type = self.model_config.get("model_name", "gpt")
            
            # 创建SDGX LLM模型
            self.sdgx_llm_handler.create_model(model_type, {**self.parameters, **training_params})
            
            # 训练SDGX LLM模型
            self.sdgx_llm_handler.fit(data, {**self.parameters, **training_params})
            
            # 生成合成数据
            synthetic_data = self.sdgx_llm_handler.sample(row_count)
            
            return synthetic_data
        except Exception as e:
            raise ValueError(f"SDGX LLM模型合成失败: {str(e)}")
    
    def _synthesize_with_opendp(self, data: pd.DataFrame, row_count: int, training_params: Dict[str, Any]) -> pd.DataFrame:
        """
        使用OpenDP模型生成合成数据
        
        Args:
            data: 原始数据框
            row_count: 要生成的行数
            training_params: 模型训练参数
            
        Returns:
            合成的数据框
        """
        if not self.opendp_handler:
            raise ValueError("OpenDP handler not available")
        
        try:
            # 获取算法类型
            algorithm = self.model_config.get("model_name", "AIM")
            
            # 训练OpenDP模型
            self.opendp_handler.fit(data, {"algorithm": algorithm, **self.parameters, **training_params})
            
            # 生成合成数据
            synthetic_data = self.opendp_handler.sample(row_count)
            
            return synthetic_data
        except Exception as e:
            raise ValueError(f"OpenDP模型合成失败: {str(e)}")
    
    def _generate_column_data_with_llm(self, column_data: pd.Series, row_count: int, column_name: str) -> pd.Series:
        """
        使用LLM方法生成单个列的数据
        
        Args:
            column_data: 原始列数据
            row_count: 要生成的行数
            column_name: 列名
            
        Returns:
            合成的列数据
        """
        # 分析原始数据的模式
        data_info = self._analyze_column_data(column_data)
        
        # 根据数据类型和模式生成合成数据
        if data_info["type"] == "categorical":
            return self._generate_categorical_data_llm(data_info, row_count)
        elif data_info["type"] == "numerical":
            return self._generate_numerical_data_llm(data_info, row_count)
        elif data_info["type"] == "datetime":
            return self._generate_datetime_data_llm(data_info, row_count)
        else:
            return self._generate_text_data_llm(data_info, row_count, column_name)
    
    def _analyze_column_data(self, column_data: pd.Series) -> Dict[str, Any]:
        """
        分析列数据的特征
        
        Args:
            column_data: 原始列数据
            
        Returns:
            数据特征字典
        """
        # 移除空值
        clean_data = column_data.dropna()
        
        if len(clean_data) == 0:
            return {"type": "text", "samples": [], "unique_count": 0}
        
        # 判断数据类型
        if column_data.dtype in ['object', 'string'] or column_data.dtype == object:
            # 检查是否为分类数据
            unique_ratio = len(clean_data.unique()) / len(clean_data)
            if unique_ratio < 0.5:  # 如果唯一值比例小于50%，认为是分类数据
                return {
                    "type": "categorical",
                    "samples": clean_data.tolist(),
                    "unique_values": clean_data.unique().tolist(),
                    "value_counts": clean_data.value_counts().to_dict()
                }
            else:
                return {
                    "type": "text",
                    "samples": clean_data.tolist(),
                    "unique_count": len(clean_data.unique())
                }
        elif np.issubdtype(column_data.dtype, np.number):
            return {
                "type": "numerical",
                "samples": clean_data.tolist(),
                "min": clean_data.min(),
                "max": clean_data.max(),
                "mean": clean_data.mean(),
                "std": clean_data.std() if len(clean_data) > 1 else 0
            }
        elif np.issubdtype(column_data.dtype, np.datetime64):
            return {
                "type": "datetime",
                "samples": clean_data.tolist(),
                "min": clean_data.min(),
                "max": clean_data.max()
            }
        else:
            return {
                "type": "text",
                "samples": clean_data.tolist(),
                "unique_count": len(clean_data.unique())
            }
    
    def _generate_categorical_data_llm(self, data_info: Dict[str, Any], row_count: int) -> pd.Series:
        """
        使用LLM方法生成分类数据
        """
        if not data_info["value_counts"]:
            return pd.Series([f"category_{random.randint(1, 10)}" for _ in range(row_count)])
        
        # 根据原始分布生成数据
        values = list(data_info["value_counts"].keys())
        counts = list(data_info["value_counts"].values())
        probabilities = np.array(counts) / sum(counts)
        
        # 生成基础数据
        synthetic_data = np.random.choice(values, size=row_count, p=probabilities)
        
        # 添加一些变异（模拟LLM的创造性）
        variation_ratio = self.parameters.get("variation", 0.1)
        variation_count = int(row_count * variation_ratio)
        variation_indices = np.random.choice(row_count, variation_count, replace=False)
        
        # 为变异数据生成新的值
        for idx in variation_indices:
            original_value = synthetic_data[idx]
            # 基于原始值生成变异值
            synthetic_data[idx] = f"{original_value}_variant_{random.randint(1, 100)}"
        
        return pd.Series(synthetic_data)
    
    def _generate_numerical_data_llm(self, data_info: Dict[str, Any], row_count: int) -> pd.Series:
        """
        使用LLM方法生成数值数据
        """
        # 基于原始数据的统计特征生成数据
        mean = data_info["mean"]
        std = data_info["std"]
        min_val = data_info["min"]
        max_val = data_info["max"]
        
        # 如果标准差为0，生成固定值的变体
        if std == 0 or pd.isna(std):
            base_value = mean
            # 添加一些变异
            noise_factor = self.parameters.get("noise_factor", 0.1)
            synthetic_data = np.random.normal(base_value, base_value * noise_factor, row_count)
        else:
            # 生成正态分布数据
            synthetic_data = np.random.normal(mean, std, row_count)
            
            # 添加一些非线性变换（模拟LLM的复杂模式理解）
            transform_ratio = self.parameters.get("transform_ratio", 0.2)
            transform_count = int(row_count * transform_ratio)
            transform_indices = np.random.choice(row_count, transform_count, replace=False)
            
            for idx in transform_indices:
                # 应用一些非线性变换
                if random.random() < 0.5:
                    synthetic_data[idx] = synthetic_data[idx] * random.uniform(0.8, 1.2)  # 缩放
                else:
                    synthetic_data[idx] = synthetic_data[idx] + random.uniform(-std, std)  # 平移
        
        # 确保数据在合理范围内
        synthetic_data = np.clip(synthetic_data, min_val, max_val)
        
        return pd.Series(synthetic_data)
    
    def _generate_datetime_data_llm(self, data_info: Dict[str, Any], row_count: int) -> pd.Series:
        """
        使用LLM方法生成日期时间数据
        """
        min_date = data_info["min"]
        max_date = data_info["max"]
        
        # 生成在范围内的随机日期
        date_range = pd.date_range(start=min_date, end=max_date, freq='D')
        if len(date_range) > 0:
            synthetic_data = np.random.choice(date_range, size=row_count)
        else:
            synthetic_data = np.array([min_date] * row_count)
        
        # 添加一些时间模式（模拟LLM对时间序列的理解）
        pattern_ratio = self.parameters.get("pattern_ratio", 0.15)
        pattern_count = int(row_count * pattern_ratio)
        pattern_indices = np.random.choice(row_count, pattern_count, replace=False)
        
        # 为一些数据添加周期性模式
        for idx in pattern_indices:
            # 添加一些基于星期或月份的模式
            base_date = synthetic_data[idx]
            if random.random() < 0.5:
                # 添加工作日偏好
                if base_date.weekday() >= 5:  # 周末
                    synthetic_data[idx] = base_date - pd.Timedelta(days=random.randint(1, 2))
            else:
                # 添加月初偏好
                if base_date.day > 15:
                    synthetic_data[idx] = base_date.replace(day=1)
        
        return pd.Series(synthetic_data)
    
    def _generate_text_data_llm(self, data_info: Dict[str, Any], row_count: int, column_name: str) -> pd.Series:
        """
        使用LLM方法生成文本数据
        """
        samples = data_info["samples"]
        if not samples:
            return pd.Series([f"{column_name}_text_{random.randint(1000, 9999)}" for _ in range(row_count)])
        
        # 基于样本生成新的文本
        synthetic_data = []
        for i in range(row_count):
            # 随机选择一个样本作为基础
            base_sample = random.choice(samples)
            
            # 根据列名和基础样本生成新的文本
            if random.random() < 0.3:  # 30%概率生成完全新的文本
                new_text = f"{column_name}_synthetic_{random.randint(1000, 9999)}"
            else:
                # 基于原始文本生成变体
                if isinstance(base_sample, str):
                    # 添加前缀或后缀
                    prefix_suffix_options = [
                        f"synthetic_{base_sample}",
                        f"{base_sample}_variant",
                        f"generated_{base_sample}_{random.randint(1, 100)}",
                        base_sample.upper(),
                        base_sample.lower()
                    ]
                    new_text = random.choice(prefix_suffix_options)
                else:
                    new_text = str(base_sample)
            
            synthetic_data.append(new_text)
        
        return pd.Series(synthetic_data)