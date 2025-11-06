import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import mean_squared_error
from typing import List, Dict, Any

# 尝试导入SDMetrics
try:
    from app.utils.sdmetrics_evaluator import SDMetricsEvaluator
    HAS_SDMETRICS = True
except ImportError:
    HAS_SDMETRICS = False
    print("SDMetrics evaluator not available")

class QualityEvaluator:
    def __init__(self):
        """
        初始化质量评估器
        """
        self.sdmetrics_evaluator = SDMetricsEvaluator() if HAS_SDMETRICS else None
    
    def evaluate(self, original_dataframes: List[pd.DataFrame], synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        评估合成数据质量
        
        Args:
            original_dataframes: 原始数据框列表
            synthetic_df: 合成数据框
            
        Returns:
            评估结果字典
        """
        # 合并所有原始数据框
        combined_original = pd.concat(original_dataframes, ignore_index=True) if len(original_dataframes) > 1 else original_dataframes[0]
        
        # 计算各项指标
        similarity_score = self._calculate_similarity_score(combined_original, synthetic_df)
        column_correlations = self._calculate_column_correlations(combined_original, synthetic_df)
        distribution_similarity = self._calculate_distribution_similarity(combined_original, synthetic_df)
        privacy_score = self._calculate_privacy_score(combined_original, synthetic_df)
        overall_quality = self._calculate_overall_quality(similarity_score, column_correlations, distribution_similarity, privacy_score)
        
        # 如果SDMetrics可用，使用它进行额外评估
        sdmetrics_result = {}
        visualization_data_ext = {}
        if self.sdmetrics_evaluator:
            try:
                sdmetrics_result = self.sdmetrics_evaluator.evaluate_with_sdmetrics(combined_original, synthetic_df)
                visualization_data_ext = self.sdmetrics_evaluator.get_visualization_data(combined_original, synthetic_df)
            except Exception as e:
                print(f"SDMetrics evaluation failed: {e}")
        
        # 准备详细指标和可视化数据
        detailed_metrics = {
            "column_count": len(synthetic_df.columns),
            "row_count": len(synthetic_df),
            "missing_values": synthetic_df.isnull().sum().to_dict(),
            "data_types": {col: str(synthetic_df[col].dtype) for col in synthetic_df.columns}
        }
        
        visualization_data = {
            "column_names": list(synthetic_df.columns),
            "data_shapes": {
                "original_count": sum(len(df) for df in original_dataframes),
                "synthetic_count": len(synthetic_df)
            },
            "correlation_comparison": self._prepare_correlation_comparison(combined_original, synthetic_df),
            "distribution_comparison": self._prepare_distribution_comparison(combined_original, synthetic_df),
            "detailed_comparison": self._prepare_detailed_comparison(combined_original, synthetic_df),
            "marginal_distribution_comparison": self._prepare_marginal_distribution_comparison(combined_original, synthetic_df),
            "column_correlation_comparison": self._prepare_column_correlation_comparison(combined_original, synthetic_df)
        }
        
        # 合并SDMetrics的可视化数据
        if visualization_data_ext.get("success", False):
            visualization_data.update(visualization_data_ext.get("data", {}))
        
        result = {
            "similarity_score": similarity_score,
            "column_correlations": column_correlations,
            "distribution_similarity": distribution_similarity,
            "privacy_score": privacy_score,
            "overall_quality": overall_quality,
            "detailed_metrics": detailed_metrics,
            "visualization_data": visualization_data
        }
        
        # 如果SDMetrics评估成功，合并结果
        if sdmetrics_result.get("success", False):
            result["sdmetrics_result"] = sdmetrics_result
        
        return result
    
    def _calculate_similarity_score(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> float:
        """
        计算整体相似度得分
        """
        # 确保两个数据框有相同的列
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        
        if not common_columns:
            return 0.0
        
        # 对于数值列，计算相关性
        numerical_columns = [col for col in common_columns if np.issubdtype(original_df[col].dtype, np.number)]
        
        if not numerical_columns:
            return 0.5  # 如果没有数值列，返回中等分数
        
        correlations = []
        for col in numerical_columns:
            orig_data = original_df[col].dropna()
            synth_data = synthetic_df[col].dropna()
            
            # 如果任一数据集为空，跳过
            if len(orig_data) == 0 or len(synth_data) == 0:
                continue
            
            # 采样到相同长度进行比较
            min_len = min(len(orig_data), len(synth_data))
            if min_len == 0:
                continue
                
            orig_sample = np.random.choice(orig_data, min_len)
            synth_sample = np.random.choice(synth_data, min_len)
            
            # 计算皮尔逊相关系数
            if np.std(orig_sample) > 0 and np.std(synth_sample) > 0:
                corr = np.corrcoef(orig_sample, synth_sample)[0, 1]
                correlations.append(abs(corr) if not np.isnan(corr) else 0)
        
        if not correlations:
            return 0.5
            
        return float(np.mean(correlations))
    
    def _calculate_column_correlations(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, float]:
        """
        计算各列相关性
        """
        correlations = {}
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        
        for col in common_columns:
            if np.issubdtype(original_df[col].dtype, np.number) and np.issubdtype(synthetic_df[col].dtype, np.number):
                orig_data = original_df[col].dropna()
                synth_data = synthetic_df[col].dropna()
                
                # 采样到相同长度
                min_len = min(len(orig_data), len(synth_data))
                if min_len > 1:  # 需要至少2个点来计算相关性
                    orig_sample = np.random.choice(orig_data, min_len)
                    synth_sample = np.random.choice(synth_data, min_len)
                    
                    if np.std(orig_sample) > 0 and np.std(synth_sample) > 0:
                        corr = np.corrcoef(orig_sample, synth_sample)[0, 1]
                        correlations[col] = abs(corr) if not np.isnan(corr) else 0.0
                    else:
                        correlations[col] = 1.0 if np.mean(orig_sample) == np.mean(synth_sample) else 0.0
                else:
                    correlations[col] = 0.0
            else:
                # 对于非数值列，检查值的分布相似性
                orig_counts = original_df[col].value_counts(normalize=True)
                synth_counts = synthetic_df[col].value_counts(normalize=True)
                
                # 计算分布的相似性（使用卡方检验的思想）
                common_values = set(orig_counts.index) & set(synth_counts.index)
                if len(common_values) > 0:
                    # 简单的重叠度量
                    correlations[col] = len(common_values) / max(len(orig_counts), len(synth_counts))
                else:
                    correlations[col] = 0.0
        
        return correlations
    
    def _calculate_distribution_similarity(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, float]:
        """
        计算分布相似度
        """
        similarities = {}
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        
        for col in common_columns:
            orig_data = original_df[col].dropna()
            synth_data = synthetic_df[col].dropna()
            
            if len(orig_data) == 0 or len(synth_data) == 0:
                similarities[col] = 0.0
                continue
            
            # 对于数值列，使用KL散度的近似
            if np.issubdtype(orig_data.dtype, np.number) and np.issubdtype(synth_data.dtype, np.number):
                # 创建直方图
                min_val = min(orig_data.min(), synth_data.min())
                max_val = max(orig_data.max(), synth_data.max())
                
                if min_val == max_val:
                    similarities[col] = 1.0 if orig_data.mean() == synth_data.mean() else 0.0
                    continue
                
                # 计算直方图
                orig_hist, bin_edges = np.histogram(orig_data, bins=50, range=(min_val, max_val), density=True)
                synth_hist, _ = np.histogram(synth_data, bins=bin_edges, density=True)
                
                # 添加小的epsilon避免除零错误
                orig_hist = orig_hist + 1e-10
                synth_hist = synth_hist + 1e-10
                
                # 计算KL散度的对称版本
                kl_div = 0.5 * (stats.entropy(orig_hist, synth_hist) + stats.entropy(synth_hist, orig_hist))
                
                # 转换为相似度得分 (0-1)
                similarity = np.exp(-kl_div)
                similarities[col] = float(similarity)
            else:
                # 对于分类列，使用卡方检验
                orig_counts = orig_data.value_counts()
                synth_counts = synth_data.value_counts()
                
                # 获取所有唯一值
                all_values = set(orig_counts.index) | set(synth_counts.index)
                
                # 创建期望和观察频数
                orig_freq = [orig_counts.get(val, 0) for val in all_values]
                synth_freq = [synth_counts.get(val, 0) for val in all_values]
                
                # 如果任何一个数组全为0，返回0
                if sum(orig_freq) == 0 or sum(synth_freq) == 0:
                    similarities[col] = 0.0
                    continue
                
                # 归一化频率
                orig_freq = np.array(orig_freq) / sum(orig_freq)
                synth_freq = np.array(synth_freq) / sum(synth_freq)
                
                # 计算余弦相似度
                dot_product = np.dot(orig_freq, synth_freq)
                norms = np.linalg.norm(orig_freq) * np.linalg.norm(synth_freq)
                
                if norms == 0:
                    similarities[col] = 0.0
                else:
                    similarities[col] = float(dot_product / norms)
        
        return similarities
    
    def _calculate_privacy_score(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> float:
        """
        计算隐私保护得分
        """
        # 简单的隐私评分基于是否完全复制了原始数据
        # 在实际应用中，这可能涉及更复杂的分析，如重识别风险评估
        
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        if not common_columns:
            return 1.0  # 没有共同列，认为隐私保护得很好
        
        # 检查是否有完全相同的行
        try:
            # 只考虑共同列
            orig_subset = original_df[common_columns].drop_duplicates()
            synth_subset = synthetic_df[common_columns].drop_duplicates()
            
            # 检查合成数据中是否包含原始数据的行
            merged = pd.merge(orig_subset, synth_subset, how='inner', on=common_columns)
            
            # 计算重复行的比例
            if len(synth_subset) > 0:
                duplicate_ratio = len(merged) / len(synth_subset)
                # 隐私得分是1减去重复比例（越高越好）
                return float(1.0 - duplicate_ratio)
            else:
                return 1.0
        except:
            # 如果出现任何错误，返回中等分数
            return 0.5
    
    def _calculate_overall_quality(self, similarity_score: float, column_correlations: Dict[str, float], 
                                 distribution_similarity: Dict[str, float], privacy_score: float) -> float:
        """
        计算总体质量得分
        """
        # 计算各部分的平均得分
        avg_correlation = np.mean(list(column_correlations.values())) if column_correlations else 0.0
        avg_distribution = np.mean(list(distribution_similarity.values())) if distribution_similarity else 0.0
        
        # 加权平均 (可以根据需要调整权重)
        weights = {
            'similarity': 0.3,
            'correlation': 0.3,
            'distribution': 0.25,
            'privacy': 0.15
        }
        
        overall_score = (
            weights['similarity'] * similarity_score +
            weights['correlation'] * avg_correlation +
            weights['distribution'] * avg_distribution +
            weights['privacy'] * privacy_score
        )
        
        return float(overall_score)
    
    def _prepare_correlation_comparison(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        准备相关性比较数据
        
        Args:
            original_df: 原始数据框
            synthetic_df: 合成数据框
            
        Returns:
            相关性比较数据字典
        """
        correlation_comparison = {}
        
        # 获取数值列
        numerical_columns = [col for col in original_df.columns 
                           if np.issubdtype(original_df[col].dtype, np.number) 
                           and col in synthetic_df.columns 
                           and np.issubdtype(synthetic_df[col].dtype, np.number)]
        
        for col in numerical_columns:
            try:
                orig_data = original_df[col].dropna()
                synth_data = synthetic_df[col].dropna()
                
                if len(orig_data) > 1 and len(synth_data) > 1:
                    # 采样到相同长度
                    min_len = min(len(orig_data), len(synth_data))
                    orig_sample = np.random.choice(orig_data, min_len)
                    synth_sample = np.random.choice(synth_data, min_len)
                    
                    # 计算统计信息
                    correlation_comparison[col] = {
                        "original": {
                            "mean": float(orig_data.mean()),
                            "std": float(orig_data.std()),
                            "min": float(orig_data.min()),
                            "max": float(orig_data.max())
                        },
                        "synthetic": {
                            "mean": float(synth_data.mean()),
                            "std": float(synth_data.std()),
                            "min": float(synth_data.min()),
                            "max": float(synth_data.max())
                        }
                    }
            except Exception as e:
                correlation_comparison[col] = {"error": str(e)}
        
        return correlation_comparison
    
    def _prepare_distribution_comparison(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        准备分布比较数据
        
        Args:
            original_df: 原始数据框
            synthetic_df: 合成数据框
            
        Returns:
            分布比较数据字典
        """
        distribution_comparison = {}
        
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        
        for col in common_columns:
            try:
                orig_data = original_df[col].dropna()
                synth_data = synthetic_df[col].dropna()
                
                if len(orig_data) > 0 and len(synth_data) > 0:
                    if np.issubdtype(orig_data.dtype, np.number) and np.issubdtype(synth_data.dtype, np.number):
                        # 数值列的分布比较
                        distribution_comparison[col] = {
                            "type": "numerical",
                            "original": {
                                "mean": float(orig_data.mean()),
                                "std": float(orig_data.std()),
                                "min": float(orig_data.min()),
                                "max": float(orig_data.max()),
                                "median": float(orig_data.median())
                            },
                            "synthetic": {
                                "mean": float(synth_data.mean()),
                                "std": float(synth_data.std()),
                                "min": float(synth_data.min()),
                                "max": float(synth_data.max()),
                                "median": float(synth_data.median())
                            }
                        }
                    else:
                        # 分类列的分布比较（只取前10个最常见的值）
                        orig_counts = orig_data.value_counts().head(10).to_dict()
                        synth_counts = synth_data.value_counts().head(10).to_dict()
                        
                        distribution_comparison[col] = {
                            "type": "categorical",
                            "original": orig_counts,
                            "synthetic": synth_counts
                        }
            except Exception as e:
                distribution_comparison[col] = {"error": str(e)}
        
        return distribution_comparison
    
    def _prepare_detailed_comparison(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        准备详细的原始数据与合成数据对比
        
        Args:
            original_df: 原始数据框
            synthetic_df: 合成数据框
            
        Returns:
            详细对比数据字典
        """
        detailed_comparison = {}
        
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        
        for col in common_columns:
            try:
                orig_data = original_df[col].dropna()
                synth_data = synthetic_df[col].dropna()
                
                if len(orig_data) > 0 and len(synth_data) > 0:
                    if np.issubdtype(orig_data.dtype, np.number) and np.issubdtype(synth_data.dtype, np.number):
                        # 数值列的详细对比
                        detailed_comparison[col] = {
                            "type": "numerical",
                            "original": {
                                "count": len(orig_data),
                                "mean": float(orig_data.mean()),
                                "std": float(orig_data.std()),
                                "min": float(orig_data.min()),
                                "max": float(orig_data.max()),
                                "median": float(orig_data.median()),
                                "q25": float(orig_data.quantile(0.25)),
                                "q75": float(orig_data.quantile(0.75))
                            },
                            "synthetic": {
                                "count": len(synth_data),
                                "mean": float(synth_data.mean()),
                                "std": float(synth_data.std()),
                                "min": float(synth_data.min()),
                                "max": float(synth_data.max()),
                                "median": float(synth_data.median()),
                                "q25": float(synth_data.quantile(0.25)),
                                "q75": float(synth_data.quantile(0.75))
                            },
                            "difference": {
                                "mean_diff": float(abs(orig_data.mean() - synth_data.mean())),
                                "std_diff": float(abs(orig_data.std() - synth_data.std())),
                                "min_diff": float(abs(orig_data.min() - synth_data.min())),
                                "max_diff": float(abs(orig_data.max() - synth_data.max()))
                            }
                        }
                    else:
                        # 分类列的详细对比
                        orig_counts = orig_data.value_counts()
                        synth_counts = synth_data.value_counts()
                        
                        # 获取共同值
                        common_values = set(orig_counts.index) & set(synth_counts.index)
                        
                        detailed_comparison[col] = {
                            "type": "categorical",
                            "original": {
                                "count": len(orig_data),
                                "unique": len(orig_counts),
                                "top_values": orig_counts.head(5).to_dict()
                            },
                            "synthetic": {
                                "count": len(synth_data),
                                "unique": len(synth_counts),
                                "top_values": synth_counts.head(5).to_dict()
                            },
                            "similarity": {
                                "common_values_count": len(common_values),
                                "overlap_ratio": len(common_values) / max(len(orig_counts), len(synth_counts)) if max(len(orig_counts), len(synth_counts)) > 0 else 0
                            }
                        }
            except Exception as e:
                detailed_comparison[col] = {"error": str(e)}
        
        return detailed_comparison
    
    def _prepare_marginal_distribution_comparison(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        准备边际分布比较数据，用于增强可视化效果
        
        Args:
            original_df: 原始数据框
            synthetic_df: 合成数据框
            
        Returns:
            边际分布比较数据字典
        """
        marginal_comparison = {}
        
        common_columns = list(set(original_df.columns) & set(synthetic_df.columns))
        
        for col in common_columns:
            try:
                orig_data = original_df[col].dropna()
                synth_data = synthetic_df[col].dropna()
                
                if len(orig_data) > 0 and len(synth_data) > 0:
                    if np.issubdtype(orig_data.dtype, np.number) and np.issubdtype(synth_data.dtype, np.number):
                        # 数值列的边际分布比较
                        # 计算更多统计信息用于可视化
                        orig_stats = {
                            "count": len(orig_data),
                            "mean": float(orig_data.mean()),
                            "std": float(orig_data.std()),
                            "min": float(orig_data.min()),
                            "max": float(orig_data.max()),
                            "median": float(orig_data.median()),
                            "q25": float(orig_data.quantile(0.25)),
                            "q75": float(orig_data.quantile(0.75)),
                            "skewness": float(orig_data.skew()) if len(orig_data) > 2 else 0.0,
                            "kurtosis": float(orig_data.kurtosis()) if len(orig_data) > 3 else 0.0
                        }
                        
                        synth_stats = {
                            "count": len(synth_data),
                            "mean": float(synth_data.mean()),
                            "std": float(synth_data.std()),
                            "min": float(synth_data.min()),
                            "max": float(synth_data.max()),
                            "median": float(synth_data.median()),
                            "q25": float(synth_data.quantile(0.25)),
                            "q75": float(synth_data.quantile(0.75)),
                            "skewness": float(synth_data.skew()) if len(synth_data) > 2 else 0.0,
                            "kurtosis": float(synth_data.kurtosis()) if len(synth_data) > 3 else 0.0
                        }
                        
                        # 计算分布差异
                        diff_stats = {
                            "mean_diff": float(abs(orig_stats["mean"] - synth_stats["mean"])),
                            "std_diff": float(abs(orig_stats["std"] - synth_stats["std"])),
                            "median_diff": float(abs(orig_stats["median"] - synth_stats["median"])),
                            "min_diff": float(abs(orig_stats["min"] - synth_stats["min"])),
                            "max_diff": float(abs(orig_stats["max"] - synth_stats["max"])),
                            "q25_diff": float(abs(orig_stats["q25"] - synth_stats["q25"])),
                            "q75_diff": float(abs(orig_stats["q75"] - synth_stats["q75"]))
                        }
                        
                        marginal_comparison[col] = {
                            "type": "numerical",
                            "original": orig_stats,
                            "synthetic": synth_stats,
                            "difference": diff_stats
                        }
                    else:
                        # 分类列的边际分布比较
                        orig_counts = orig_data.value_counts()
                        synth_counts = synth_data.value_counts()
                        
                        # 获取所有唯一值并计算相对频率
                        all_values = set(orig_counts.index) | set(synth_counts.index)
                        orig_freq = {val: orig_counts.get(val, 0) / len(orig_data) for val in all_values}
                        synth_freq = {val: synth_counts.get(val, 0) / len(synth_data) for val in all_values}
                        
                        # 计算分布差异
                        diff_freq = {val: abs(orig_freq[val] - synth_freq[val]) for val in all_values}
                        
                        marginal_comparison[col] = {
                            "type": "categorical",
                            "original": {
                                "count": len(orig_data),
                                "unique": len(orig_counts),
                                "value_counts": orig_counts.to_dict(),
                                "value_frequencies": orig_freq
                            },
                            "synthetic": {
                                "count": len(synth_data),
                                "unique": len(synth_counts),
                                "value_counts": synth_counts.to_dict(),
                                "value_frequencies": synth_freq
                            },
                            "difference": {
                                "frequency_differences": diff_freq,
                                "max_difference": max(diff_freq.values()) if diff_freq else 0.0,
                                "mean_difference": np.mean(list(diff_freq.values())) if diff_freq else 0.0
                            }
                        }
            except Exception as e:
                marginal_comparison[col] = {"error": str(e)}
        
        return marginal_comparison

    def _prepare_column_correlation_comparison(self, original_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> Dict[str, Any]:
        """
        准备列相关性比较数据，用于增强可视化效果
        
        Args:
            original_df: 原始数据框
            synthetic_df: 合成数据框
            
        Returns:
            列相关性比较数据字典
        """
        correlation_comparison = {}
        
        # 获取数值列
        numerical_columns = [col for col in original_df.columns 
                           if np.issubdtype(original_df[col].dtype, np.number) 
                           and col in synthetic_df.columns 
                           and np.issubdtype(synthetic_df[col].dtype, np.number)]
        
        # 计算列间的相关性矩阵
        if len(numerical_columns) > 1:
            try:
                # 计算原始数据和合成数据的相关性矩阵
                orig_corr_matrix = original_df[numerical_columns].corr()
                synth_corr_matrix = synthetic_df[numerical_columns].corr()
                
                # 计算相关性差异
                corr_diff_matrix = abs(orig_corr_matrix - synth_corr_matrix)
                
                # 为每个数值列准备详细的相关性信息
                for col in numerical_columns:
                    try:
                        orig_data = original_df[col].dropna()
                        synth_data = synthetic_df[col].dropna()
                        
                        if len(orig_data) > 1 and len(synth_data) > 1:
                            # 采样到相同长度
                            min_len = min(len(orig_data), len(synth_data))
                            orig_sample = np.random.choice(orig_data, min_len)
                            synth_sample = np.random.choice(synth_data, min_len)
                            
                            # 计算统计信息
                            orig_stats = {
                                "mean": float(orig_data.mean()),
                                "std": float(orig_data.std()),
                                "min": float(orig_data.min()),
                                "max": float(orig_data.max()),
                                "median": float(orig_data.median()),
                                "skewness": float(orig_data.skew()) if len(orig_data) > 2 else 0.0,
                                "kurtosis": float(orig_data.kurtosis()) if len(orig_data) > 3 else 0.0
                            }
                            
                            synth_stats = {
                                "mean": float(synth_data.mean()),
                                "std": float(synth_data.std()),
                                "min": float(synth_data.min()),
                                "max": float(synth_data.max()),
                                "median": float(synth_data.median()),
                                "skewness": float(synth_data.skew()) if len(synth_data) > 2 else 0.0,
                                "kurtosis": float(synth_data.kurtosis()) if len(synth_data) > 3 else 0.0
                            }
                            
                            # 计算差异
                            diff_stats = {
                                "mean_diff": float(abs(orig_stats["mean"] - synth_stats["mean"])),
                                "std_diff": float(abs(orig_stats["std"] - synth_stats["std"])),
                                "median_diff": float(abs(orig_stats["median"] - synth_stats["median"])),
                                "min_diff": float(abs(orig_stats["min"] - synth_stats["min"])),
                                "max_diff": float(abs(orig_stats["max"] - synth_stats["max"]))
                            }
                            
                            # 获取该列与其他列的相关性
                            orig_col_correlations = {}
                            synth_col_correlations = {}
                            corr_differences = {}
                            
                            if col in orig_corr_matrix.index and col in synth_corr_matrix.index:
                                for other_col in numerical_columns:
                                    if other_col != col and other_col in orig_corr_matrix.columns and other_col in synth_corr_matrix.columns:
                                        orig_col_correlations[other_col] = float(orig_corr_matrix.loc[col, other_col])
                                        synth_col_correlations[other_col] = float(synth_corr_matrix.loc[col, other_col])
                                        corr_differences[other_col] = float(corr_diff_matrix.loc[col, other_col])
                            
                            correlation_comparison[col] = {
                                "type": "numerical",
                                "original": orig_stats,
                                "synthetic": synth_stats,
                                "difference": diff_stats,
                                "correlations": {
                                    "original_with_others": orig_col_correlations,
                                    "synthetic_with_others": synth_col_correlations,
                                    "differences": corr_differences
                                }
                            }
                    except Exception as e:
                        correlation_comparison[col] = {"error": str(e)}
                        
            except Exception as e:
                # 如果计算相关性矩阵失败，回退到简单的方法
                for col in numerical_columns:
                    try:
                        orig_data = original_df[col].dropna()
                        synth_data = synthetic_df[col].dropna()
                        
                        if len(orig_data) > 1 and len(synth_data) > 1:
                            # 采样到相同长度
                            min_len = min(len(orig_data), len(synth_data))
                            orig_sample = np.random.choice(orig_data, min_len)
                            synth_sample = np.random.choice(synth_data, min_len)
                            
                            # 计算统计信息
                            correlation_comparison[col] = {
                                "type": "numerical",
                                "original": {
                                    "mean": float(orig_data.mean()),
                                    "std": float(orig_data.std()),
                                    "min": float(orig_data.min()),
                                    "max": float(orig_data.max()),
                                    "median": float(orig_data.median())
                                },
                                "synthetic": {
                                    "mean": float(synth_data.mean()),
                                    "std": float(synth_data.std()),
                                    "min": float(synth_data.min()),
                                    "max": float(synth_data.max()),
                                    "median": float(synth_data.median())
                                }
                            }
                    except Exception as e:
                        correlation_comparison[col] = {"error": str(e)}
        else:
            # 如果数值列少于2个，使用简单的方法
            for col in numerical_columns:
                try:
                    orig_data = original_df[col].dropna()
                    synth_data = synthetic_df[col].dropna()
                    
                    if len(orig_data) > 1 and len(synth_data) > 1:
                        # 采样到相同长度
                        min_len = min(len(orig_data), len(synth_data))
                        orig_sample = np.random.choice(orig_data, min_len)
                        synth_sample = np.random.choice(synth_data, min_len)
                        
                        # 计算统计信息
                        correlation_comparison[col] = {
                            "type": "numerical",
                            "original": {
                                "mean": float(orig_data.mean()),
                                "std": float(orig_data.std()),
                                "min": float(orig_data.min()),
                                "max": float(orig_data.max()),
                                "median": float(orig_data.median())
                            },
                            "synthetic": {
                                "mean": float(synth_data.mean()),
                                "std": float(synth_data.std()),
                                "min": float(synth_data.min()),
                                "max": float(synth_data.max()),
                                "median": float(synth_data.median())
                            }
                        }
                except Exception as e:
                    correlation_comparison[col] = {"error": str(e)}
        
        return correlation_comparison
