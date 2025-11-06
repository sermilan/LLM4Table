import pandas as pd
import numpy as np
from typing import List, Dict, Any
import json
try:
    from sdmetrics.reports.single_table import QualityReport
    from sdmetrics.reports.single_table._properties import ColumnShapes, ColumnPairTrends
    from sdmetrics.single_column import StatisticSimilarity
    HAS_SDMETRICS = True
except ImportError:
    HAS_SDMETRICS = False
    print("SDMetrics not installed. Please install it with: pip install sdmetrics")

class SDMetricsEvaluator:
    def __init__(self):
        """
        初始化SDMetrics评估器
        """
        if not HAS_SDMETRICS:
            raise ImportError("SDMetrics is not installed. Please install it with: pip install sdmetrics")
    
    def evaluate_with_sdmetrics(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame, 
                              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        使用SDMetrics评估合成数据质量
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            metadata: 数据元信息（可选）
            
        Returns:
            评估结果字典
        """
        try:
            # 如果没有提供metadata，自动生成
            if metadata is None:
                metadata = self._generate_metadata(real_data)
            
            # 创建质量报告
            report = QualityReport()
            
            # 生成报告
            report.generate(real_data, synthetic_data, metadata)
            
            # 获取详细指标
            score = report.get_score()
            properties = report.get_properties()
            details = report.get_details()
            
            # 提取关键指标
            column_shapes_score = None
            column_pair_trends_score = None
            
            for prop in properties:
                if prop['Property'] == 'Column Shapes':
                    column_shapes_score = prop['Score']
                elif prop['Property'] == 'Column Pair Trends':
                    column_pair_trends_score = prop['Score']
            
            return {
                "overall_score": score,
                "column_shapes_score": column_shapes_score,
                "column_pair_trends_score": column_pair_trends_score,
                "properties": properties,
                "details": details,
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_metadata(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        自动生成数据元信息
        
        Args:
            data: 数据框
            
        Returns:
            元信息字典
        """
        columns = {}
        for column in data.columns:
            dtype = str(data[column].dtype)
            if 'int' in dtype or 'float' in dtype:
                columns[column] = {"sdtype": "numerical"}
            elif 'datetime' in dtype:
                columns[column] = {"sdtype": "datetime"}
            else:
                columns[column] = {"sdtype": "categorical"}
        
        return {
            "columns": columns
        }
    
    def get_visualization_data(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame,
                              metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取可视化数据，包括SDMetrics热力图数据
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            metadata: 数据元信息（可选）
            
        Returns:
            可视化数据字典
        """
        try:
            if metadata is None:
                metadata = self._generate_metadata(real_data)
            
            # 准备可视化数据
            visualization_data = {
                "column_names": list(real_data.columns),
                "data_shapes": {
                    "real_count": len(real_data),
                    "synthetic_count": len(synthetic_data)
                },
                "data_types": {col: str(real_data[col].dtype) for col in real_data.columns},
                # 为图表准备数据
                "correlation_data": self._prepare_correlation_data(real_data, synthetic_data),
                "distribution_data": self._prepare_distribution_data(real_data, synthetic_data),
                "summary_stats": self._prepare_summary_stats(real_data, synthetic_data),
                # SDMetrics热力图数据
                "sdmetrics_heatmap_data": self._prepare_sdmetrics_heatmap_data(real_data, synthetic_data, metadata)
            }
            
            return {
                "success": True,
                "data": visualization_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_sdmetrics_heatmap_data(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame, 
                                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备SDMetrics热力图数据，用于显示原始数据和合成数据之间的相似性
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            metadata: 数据元信息
            
        Returns:
            热力图数据字典
        """
        heatmap_data = {}
        
        # 为每个列计算相似性得分
        for column in real_data.columns:
            if column not in synthetic_data.columns:
                continue
                
            try:
                # 获取列的类型
                col_metadata = metadata.get("columns", {}).get(column, {})
                col_type = col_metadata.get("sdtype", "categorical")
                
                # 计算相似性得分
                if col_type == "numerical":
                    # 对数值列使用统计相似性
                    similarity_score = self._calculate_numerical_similarity(
                        real_data[column].dropna(), 
                        synthetic_data[column].dropna()
                    )
                else:
                    # 对分类列使用统计相似性
                    similarity_score = self._calculate_categorical_similarity(
                        real_data[column].dropna(), 
                        synthetic_data[column].dropna()
                    )
                
                heatmap_data[column] = {
                    "similarity_score": similarity_score,
                    "type": col_type
                }
            except Exception as e:
                heatmap_data[column] = {
                    "similarity_score": 0.0,
                    "type": "unknown",
                    "error": str(e)
                }
        
        # 准备列对趋势热力图数据（参考SDMetrics的Column Pair Trends）
        column_pair_trends_data = self._prepare_column_pair_trends_heatmap(real_data, synthetic_data, metadata)
        
        return {
            "column_similarity": heatmap_data,
            "column_pair_trends": column_pair_trends_data
        }
    
    def _calculate_numerical_similarity(self, real_data: pd.Series, synth_data: pd.Series) -> float:
        """
        计算数值列的相似性得分
        
        Args:
            real_data: 真实数据列
            synth_data: 合成数据列
            
        Returns:
            相似性得分 (0-1)
        """
        if len(real_data) == 0 or len(synth_data) == 0:
            return 0.0
            
        # 采样到相同长度
        min_len = min(len(real_data), len(synth_data))
        real_sample = np.random.choice(real_data, min_len) if len(real_data) > min_len else real_data
        synth_sample = np.random.choice(synth_data, min_len) if len(synth_data) > min_len else synth_data
        
        # 使用统计相似性计算
        try:
            similarity = StatisticSimilarity.compute(real_sample, synth_sample)
            return float(similarity) if not np.isnan(similarity) else 0.0
        except:
            # 如果SDMetrics方法失败，使用简单的相关性计算
            if np.std(real_sample) > 0 and np.std(synth_sample) > 0:
                corr = np.corrcoef(real_sample, synth_sample)[0, 1]
                return abs(corr) if not np.isnan(corr) else 0.0
            else:
                return 1.0 if np.mean(real_sample) == np.mean(synth_sample) else 0.0
    
    def _prepare_column_pair_trends_heatmap(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame, 
                                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备列对趋势热力图数据，参考SDMetrics的Column Pair Trends实现
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            metadata: 数据元信息
            
        Returns:
            列对趋势热力图数据字典
        """
        try:
            # 获取数值列
            numerical_columns = []
            for column in real_data.columns:
                if column in synthetic_data.columns:
                    col_metadata = metadata.get("columns", {}).get(column, {})
                    col_type = col_metadata.get("sdtype", "categorical")
                    if col_type == "numerical":
                        numerical_columns.append(column)
            
            # 计算列对之间的相关性相似度
            correlation_matrix_real = pd.DataFrame(index=numerical_columns, columns=numerical_columns)
            correlation_matrix_synth = pd.DataFrame(index=numerical_columns, columns=numerical_columns)
            similarity_matrix = pd.DataFrame(index=numerical_columns, columns=numerical_columns)
            
            for i, col1 in enumerate(numerical_columns):
                for j, col2 in enumerate(numerical_columns):
                    if i <= j:  # 只计算上三角矩阵（包括对角线）
                        try:
                            real_col1_data = real_data[col1].dropna()
                            real_col2_data = real_data[col2].dropna()
                            synth_col1_data = synthetic_data[col1].dropna()
                            synth_col2_data = synthetic_data[col2].dropna()
                            
                            # 计算相关性
                            if len(real_col1_data) > 1 and len(real_col2_data) > 1:
                                # 采样到相同长度
                                min_len_real = min(len(real_col1_data), len(real_col2_data))
                                real_col1_sample = np.random.choice(real_col1_data, min_len_real) if len(real_col1_data) > min_len_real else real_col1_data
                                real_col2_sample = np.random.choice(real_col2_data, min_len_real) if len(real_col2_data) > min_len_real else real_col2_data
                                
                                if np.std(real_col1_sample) > 0 and np.std(real_col2_sample) > 0:
                                    corr_real = np.corrcoef(real_col1_sample, real_col2_sample)[0, 1]
                                else:
                                    corr_real = 0.0
                            else:
                                corr_real = 0.0
                            
                            if len(synth_col1_data) > 1 and len(synth_col2_data) > 1:
                                # 采样到相同长度
                                min_len_synth = min(len(synth_col1_data), len(synth_col2_data))
                                synth_col1_sample = np.random.choice(synth_col1_data, min_len_synth) if len(synth_col1_data) > min_len_synth else synth_col1_data
                                synth_col2_sample = np.random.choice(synth_col2_data, min_len_synth) if len(synth_col2_data) > min_len_synth else synth_col2_data
                                
                                if np.std(synth_col1_sample) > 0 and np.std(synth_col2_sample) > 0:
                                    corr_synth = np.corrcoef(synth_col1_sample, synth_col2_sample)[0, 1]
                                else:
                                    corr_synth = 0.0
                            else:
                                corr_synth = 0.0
                            
                            correlation_matrix_real.loc[col1, col2] = corr_real
                            correlation_matrix_synth.loc[col1, col2] = corr_synth
                            
                            # 计算相似度（使用绝对差值）
                            similarity = 1.0 - abs(corr_real - corr_synth)
                            similarity_matrix.loc[col1, col2] = max(0.0, similarity)  # 确保非负
                            
                            # 对称填充
                            if i != j:
                                correlation_matrix_real.loc[col2, col1] = corr_real
                                correlation_matrix_synth.loc[col2, col1] = corr_synth
                                similarity_matrix.loc[col2, col1] = max(0.0, similarity)
                        except Exception as e:
                            correlation_matrix_real.loc[col1, col2] = 0.0
                            correlation_matrix_synth.loc[col1, col2] = 0.0
                            similarity_matrix.loc[col1, col2] = 0.0
                            
                            if i != j:
                                correlation_matrix_real.loc[col2, col1] = 0.0
                                correlation_matrix_synth.loc[col2, col1] = 0.0
                                similarity_matrix.loc[col2, col1] = 0.0
            
            # 转换为字典格式
            return {
                "numerical_columns": numerical_columns,
                "real_correlations": correlation_matrix_real.to_dict(),
                "synthetic_correlations": correlation_matrix_synth.to_dict(),
                "similarity_scores": similarity_matrix.to_dict(),
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_categorical_similarity(self, real_data: pd.Series, synth_data: pd.Series) -> float:
        """
        计算分类列的相似性得分
        
        Args:
            real_data: 真实数据列
            synth_data: 合成数据列
            
        Returns:
            相似性得分 (0-1)
        """
        if len(real_data) == 0 or len(synth_data) == 0:
            return 0.0
            
        # 计算值分布
        real_counts = real_data.value_counts(normalize=True)
        synth_counts = synth_data.value_counts(normalize=True)
        
        # 获取共同的值
        common_values = set(real_counts.index) & set(synth_counts.index)
        
        if len(common_values) == 0:
            return 0.0
            
        # 计算余弦相似度
        real_freq = [real_counts.get(val, 0) for val in common_values]
        synth_freq = [synth_counts.get(val, 0) for val in common_values]
        
        # 归一化频率
        real_freq = np.array(real_freq)
        synth_freq = np.array(synth_freq)
        
        if np.sum(real_freq) == 0 or np.sum(synth_freq) == 0:
            return 0.0
            
        real_freq = real_freq / np.sum(real_freq)
        synth_freq = synth_freq / np.sum(synth_freq)
        
        # 计算余弦相似度
        dot_product = np.dot(real_freq, synth_freq)
        norms = np.linalg.norm(real_freq) * np.linalg.norm(synth_freq)
        
        if norms == 0:
            return 0.0
            
        return float(dot_product / norms)
    
    def _prepare_correlation_data(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
        """
        准备相关性数据用于可视化
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            
        Returns:
            相关性数据字典
        """
        correlation_data = {}
        
        # 获取数值列
        numerical_columns = [col for col in real_data.columns 
                           if np.issubdtype(real_data[col].dtype, np.number) 
                           and np.issubdtype(synthetic_data[col].dtype, np.number)]
        
        for col in numerical_columns:
            try:
                real_col_data = real_data[col].dropna()
                synth_col_data = synthetic_data[col].dropna()
                
                if len(real_col_data) > 1 and len(synth_col_data) > 1:
                    # 计算相关系数
                    min_len = min(len(real_col_data), len(synth_col_data))
                    real_sample = np.random.choice(real_col_data, min_len)
                    synth_sample = np.random.choice(synth_col_data, min_len)
                    
                    if np.std(real_sample) > 0 and np.std(synth_sample) > 0:
                        correlation = np.corrcoef(real_sample, synth_sample)[0, 1]
                        correlation_data[col] = {
                            "correlation": correlation if not np.isnan(correlation) else 0,
                            "real_mean": float(real_col_data.mean()),
                            "synth_mean": float(synth_col_data.mean()),
                            "real_std": float(real_col_data.std()),
                            "synth_std": float(synth_col_data.std())
                        }
            except Exception as e:
                correlation_data[col] = {"error": str(e)}
        
        return correlation_data
    
    def _prepare_distribution_data(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
        """
        准备分布数据用于可视化
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            
        Returns:
            分布数据字典
        """
        distribution_data = {}
        
        for col in real_data.columns:
            try:
                real_col_data = real_data[col].dropna()
                synth_col_data = synthetic_data[col].dropna()
                
                if len(real_col_data) > 0 and len(synth_col_data) > 0:
                    # 对于数值列，计算基本统计信息
                    if np.issubdtype(real_col_data.dtype, np.number):
                        distribution_data[col] = {
                            "type": "numerical",
                            "real_stats": {
                                "mean": float(real_col_data.mean()),
                                "std": float(real_col_data.std()),
                                "min": float(real_col_data.min()),
                                "max": float(real_col_data.max())
                            },
                            "synth_stats": {
                                "mean": float(synth_col_data.mean()),
                                "std": float(synth_col_data.std()),
                                "min": float(synth_col_data.min()),
                                "max": float(synth_col_data.max())
                            }
                        }
                    else:
                        # 对于分类列，计算值计数
                        real_counts = real_col_data.value_counts().head(10).to_dict()  # 只取前10个
                        synth_counts = synth_col_data.value_counts().head(10).to_dict()
                        
                        distribution_data[col] = {
                            "type": "categorical",
                            "real_counts": real_counts,
                            "synth_counts": synth_counts
                        }
            except Exception as e:
                distribution_data[col] = {"error": str(e)}
        
        return distribution_data
    
    def _prepare_summary_stats(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame) -> Dict[str, Any]:
        """
        准备汇总统计信息
        
        Args:
            real_data: 真实数据
            synthetic_data: 合成数据
            
        Returns:
            汇总统计信息字典
        """
        return {
            "real_data_shape": real_data.shape,
            "synthetic_data_shape": synthetic_data.shape,
            "common_columns": list(set(real_data.columns) & set(synthetic_data.columns)),
            "missing_columns_in_real": list(set(synthetic_data.columns) - set(real_data.columns)),
            "missing_columns_in_synth": list(set(real_data.columns) - set(synthetic_data.columns))
        }

# 兼容性处理
if not HAS_SDMETRICS:
    class SDMetricsEvaluator:
        def __init__(self):
            pass
        
        def evaluate_with_sdmetrics(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame, 
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
            return {
                "success": False,
                "error": "SDMetrics is not installed"
            }
        
        def get_visualization_data(self, real_data: pd.DataFrame, synthetic_data: pd.DataFrame,
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
            return {
                "success": False,
                "error": "SDMetrics is not installed"
            }