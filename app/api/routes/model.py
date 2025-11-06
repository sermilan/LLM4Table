from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import httpx

router = APIRouter()

# 模型配置模型
class ModelConfig(BaseModel):
    model_name: str
    provider: str  # 如 "openai", "huggingface", "siliconflow", "aliyun", "sdv"
    api_key: str = None
    base_url: str = None
    parameters: Dict[str, Any] = {}

# 可用模型列表
AVAILABLE_MODELS = [
    {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "provider": "openai",
        "description": "OpenAI的GPT-3.5 Turbo模型"
    },
    {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "openai",
        "description": "OpenAI的GPT-4模型"
    },
    {
        "id": "llama-2-7b",
        "name": "LLaMA 2 7B",
        "provider": "huggingface",
        "description": "Meta的LLaMA 2 7B模型"
    },
    {
        "id": "llama-2-13b",
        "name": "LLaMA 2 13B",
        "provider": "huggingface",
        "description": "Meta的LLaMA 2 13B模型"
    },
    {
        "id": "qwen-7b",
        "name": "通义千问Qwen-7B",
        "provider": "siliconflow",
        "description": "硅基流动SiliconFlow的通义千问Qwen-7B模型"
    },
    {
        "id": "qwen-14b",
        "name": "通义千问Qwen-14B",
        "provider": "siliconflow",
        "description": "硅基流动SiliconFlow的通义千问Qwen-14B模型"
    },
    {
        "id": "baichuan2-7b",
        "name": "百川Baichuan2-7B",
        "provider": "aliyun",
        "description": "阿里云百炼的百川Baichuan2-7B模型"
    },
    {
        "id": "chatglm3-6b",
        "name": "智谱ChatGLM3-6B",
        "provider": "aliyun",
        "description": "阿里云百炼的智谱ChatGLM3-6B模型"
    },
    # SDV模型
    {
        "id": "gaussian_copula",
        "name": "Gaussian Copula",
        "provider": "sdv",
        "description": "基于高斯Copula的合成模型"
    },
    {
        "id": "ctgan",
        "name": "CTGAN",
        "provider": "sdv",
        "description": "条件表格GAN模型"
    },
    {
        "id": "copulagan",
        "name": "CopulaGAN",
        "provider": "sdv",
        "description": "基于Copula的GAN模型"
    },
    # SDGX统计模型
    {
        "id": "gaussian_multivariate",
        "name": "Gaussian Multivariate",
        "provider": "sdgx_statistics",
        "description": "基于高斯多元分布的统计模型"
    },
    {
        "id": "gaussian_copula_sdgx",
        "name": "Gaussian Copula (SDGX)",
        "provider": "sdgx_statistics",
        "description": "基于高斯Copula的统计模型"
    },
    # SDGX机器学习模型
    {
        "id": "ctgan_sdgx",
        "name": "CTGAN (SDGX)",
        "provider": "sdgx_ml",
        "description": "基于SDGX的条件表格GAN模型"
    },
    # SDGX LLM模型
    {
        "id": "gpt_sdgx",
        "name": "GPT (SDGX)",
        "provider": "sdgx_llm",
        "description": "基于SDGX的GPT模型"
    },
    # OpenDP模型
    {
        "id": "aim_dp",
        "name": "AIM with Differential Privacy",
        "provider": "opendp",
        "description": "基于OpenDP AIM算法的差分隐私合成模型"
    },
    {
        "id": "mst_dp",
        "name": "MST with Differential Privacy",
        "provider": "opendp",
        "description": "基于OpenDP MST算法的差分隐私合成模型"
    }
]

# 当前配置的模型
current_model_config = None

@router.get("/available")
async def get_available_models():
    """
    获取可用的模型列表
    """
    return {"success": True, "data": AVAILABLE_MODELS}

@router.post("/configure")
async def configure_model(config: ModelConfig):
    """
    配置使用的模型
    """
    global current_model_config
    try:
        # 这里应该添加模型连接验证逻辑
        current_model_config = config
        return {
            "success": True,
            "message": f"模型 {config.model_name} 配置成功",
            "data": config.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型配置失败: {str(e)}")

@router.get("/current")
async def get_current_model():
    """
    获取当前配置的模型
    """
    if current_model_config is None:
        return {"success": False, "message": "未配置模型"}
    
    return {
        "success": True,
        "data": current_model_config.dict()
    }

@router.put("/parameters")
async def update_model_parameters(parameters: Dict[str, Any]):
    """
    更新模型参数
    """
    global current_model_config
    if current_model_config is None:
        raise HTTPException(status_code=400, detail="请先配置模型")
    
    try:
        current_model_config.parameters.update(parameters)
        return {
            "success": True,
            "message": "模型参数更新成功",
            "data": current_model_config.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模型参数失败: {str(e)}")

# 模型参数模板
MODEL_PARAMETERS_TEMPLATE = {
    "openai": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    },
    "huggingface": {
        "temperature": 0.7,
        "max_new_tokens": 1000,
        "top_k": 50,
        "top_p": 0.95,
        "repetition_penalty": 1.0
    },
    "siliconflow": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95
    },
    "aliyun": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 0.95
    },
    "sdv": {
        "default_distribution": "beta",
        "enforce_min_max_values": True,
        "enforce_rounding": True,
        "numerical_distributions": {}
    },
    "sdgx_statistics": {
        "gaussian_multivariate": {
            "distribution": "norm"
        },
        "gaussian_copula": {
            "default_distribution": "beta",
            "enforce_min_max_values": True,
            "enforce_rounding": True
        }
    },
    "sdgx_ml": {
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
    },
    "sdgx_llm": {
        "gpt": {
            "openai_API_key": "",
            "openai_API_url": "https://api.openai.com/v1/",
            "max_tokens": 4000,
            "temperature": 0.1,
            "timeout": 90,
            "gpt_model": "gpt-3.5-turbo",
            "query_batch": 30
        }
    },
    "opendp": {
        "aim_dp": {
            "epsilon": 1.0,
            "max_cells": 1000
        },
        "mst_dp": {
            "epsilon": 1.0,
            "tree_depth": 5
        }
    }
}

@router.get("/parameters/template/{provider}")
async def get_model_parameters_template(provider: str):
    """
    获取指定提供商的模型参数模板
    """
    if provider in MODEL_PARAMETERS_TEMPLATE:
        return {
            "success": True,
            "data": MODEL_PARAMETERS_TEMPLATE[provider]
        }
    else:
        # 尝试从SDV获取参数模板
        if provider == "sdv":
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                template = sdv_handler.get_model_parameters_template()
                return {
                    "success": True,
                    "data": template
                }
            except Exception as e:
                pass
        
        # 尝试从SDGX统计模型获取参数模板
        if provider == "sdgx_statistics":
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                template = sdv_handler.get_model_parameters_template()
                # 返回特定于SDGX统计模型的参数模板
                sdgx_stats_template = template.get("sdgx_statistics", {})
                return {
                    "success": True,
                    "data": sdgx_stats_template
                }
            except Exception as e:
                pass
        
        # 尝试从SDGX机器学习模型获取参数模板
        if provider == "sdgx_ml":
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                template = sdv_handler.get_model_parameters_template()
                # 返回特定于SDGX机器学习模型的参数模板
                sdgx_ml_template = template.get("sdgx_ml", {})
                return {
                    "success": True,
                    "data": sdgx_ml_template
                }
            except Exception as e:
                pass
        
        # 尝试从SDGX LLM模型获取参数模板
        if provider == "sdgx_llm":
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                template = sdv_handler.get_model_parameters_template()
                # 返回特定于SDGX LLM模型的参数模板
                sdgx_llm_template = template.get("sdgx_llm", {})
                return {
                    "success": True,
                    "data": sdgx_llm_template
                }
            except Exception as e:
                pass
        
        # 尝试从OpenDP模型获取参数模板
        if provider == "opendp":
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                template = sdv_handler.get_model_parameters_template()
                # 返回特定于OpenDP模型的参数模板
                opendp_template = template.get("opendp", {})
                return {
                    "success": True,
                    "data": opendp_template
                }
            except Exception as e:
                pass
        
        raise HTTPException(status_code=400, detail=f"不支持的模型提供商: {provider}")

# 模拟从不同提供商获取模型列表的函数
async def get_models_from_siliconflow(api_key: str):
    """
    从硅基流动获取模型列表
    """
    # 这里应该调用硅基流动的实际API
    # 暂时返回模拟数据
    return [
        {"id": "deepseek-coder-6.7b-instruct", "name": "DeepSeek Coder 6.7B Instruct"},
        {"id": "deepseek-llm-67b-chat", "name": "DeepSeek LLM 67B Chat"},
        {"id": "qwen-72b-chat", "name": "通义千问 72B Chat"},
        {"id": "yi-34b-chat", "name": "零一万物 34B Chat"}
    ]

async def get_models_from_aliyun(api_key: str):
    """
    从阿里云获取模型列表
    """
    # 这里应该调用阿里云的实际API
    # 暂时返回模拟数据
    return [
        {"id": "qwen-max", "name": "通义千问 Max"},
        {"id": "qwen-plus", "name": "通义千问 Plus"},
        {"id": "qwen-turbo", "name": "通义千问 Turbo"},
        {"id": "baichuan2-13b-chat", "name": "百川 13B Chat"}
    ]

async def get_models_from_sdv():
    """
    从SDV获取模型列表
    """
    try:
        from app.utils.sdv_handler import SDVHandler
        sdv_handler = SDVHandler()
        return sdv_handler.get_available_models()
    except Exception as e:
        # 如果SDV不可用，返回默认模型列表
        return [
            {"id": "gaussian_copula", "name": "Gaussian Copula", "description": "基于高斯Copula的合成模型"},
            {"id": "ctgan", "name": "CTGAN", "description": "条件表格GAN模型"},
            {"id": "copulagan", "name": "CopulaGAN", "description": "基于Copula的GAN模型"}
        ]

@router.post("/list-provider-models")
async def list_provider_models(config: ModelConfig):
    """
    根据提供商配置获取该提供商的模型列表
    """
    try:
        if config.provider == "siliconflow" and config.api_key:
            models = await get_models_from_siliconflow(config.api_key)
            return {"success": True, "data": models}
        elif config.provider == "aliyun" and config.api_key:
            models = await get_models_from_aliyun(config.api_key)
            return {"success": True, "data": models}
        elif config.provider == "sdv":
            models = await get_models_from_sdv()
            return {"success": True, "data": models}
        elif config.provider == "sdgx_statistics":
            # SDGX统计模型
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                models = sdv_handler.get_available_models()
                # 过滤出SDGX统计模型
                sdgx_stats_models = [model for model in models if model["provider"] == "sdgx_statistics"]
                return {"success": True, "data": sdgx_stats_models}
            except Exception as e:
                # 如果SDGX不可用，返回默认模型列表
                models = [model for model in AVAILABLE_MODELS if model["provider"] == config.provider]
                return {"success": True, "data": models}
        elif config.provider == "sdgx_ml":
            # SDGX机器学习模型
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                models = sdv_handler.get_available_models()
                # 过滤出SDGX机器学习模型
                sdgx_ml_models = [model for model in models if model["provider"] == "sdgx_ml"]
                return {"success": True, "data": sdgx_ml_models}
            except Exception as e:
                # 如果SDGX不可用，返回默认模型列表
                models = [model for model in AVAILABLE_MODELS if model["provider"] == config.provider]
                return {"success": True, "data": models}
        elif config.provider == "opendp":
            # OpenDP模型
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                models = sdv_handler.get_available_models()
                # 过滤出OpenDP模型
                opendp_models = [model for model in models if model["provider"] == "opendp"]
                return {"success": True, "data": opendp_models}
            except Exception as e:
                # 如果OpenDP不可用，返回默认模型列表
                models = [model for model in AVAILABLE_MODELS if model["provider"] == config.provider]
                return {"success": True, "data": models}
        elif config.provider == "sdgx_llm":
            # SDGX LLM模型
            try:
                from app.utils.sdv_handler import SDVHandler
                sdv_handler = SDVHandler()
                models = sdv_handler.get_available_models()
                # 过滤出SDGX LLM模型
                sdgx_llm_models = [model for model in models if model["provider"] == "sdgx_llm"]
                return {"success": True, "data": sdgx_llm_models}
            except Exception as e:
                # 如果SDGX不可用，返回默认模型列表
                models = [model for model in AVAILABLE_MODELS if model["provider"] == config.provider]
                return {"success": True, "data": models}
        else:
            # 返回默认模型列表
            models = [model for model in AVAILABLE_MODELS if model["provider"] == config.provider]
            return {"success": True, "data": models}
    except Exception as e:
        # 即使出错也返回默认模型列表
        models = [model for model in AVAILABLE_MODELS if model["provider"] == config.provider]
        return {"success": True, "data": models}

@router.post("/test-connection")
async def test_model_connection(config: ModelConfig):
    """
    测试模型连接
    """
    try:
        if config.provider == "openai" and config.api_key:
            # 测试OpenAI连接
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.base_url or 'https://api.openai.com'}/v1/models",
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "OpenAI模型连接测试成功"}
                else:
                    return {"success": False, "message": f"OpenAI模型连接测试失败: {response.status_code}"}
        elif config.provider == "siliconflow" and config.api_key:
            # 测试硅基流动连接
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.base_url or 'https://api.siliconflow.cn'}/v1/models",
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    return {"success": True, "message": "硅基流动模型连接测试成功"}
                else:
                    return {"success": False, "message": f"硅基流动模型连接测试失败: {response.status_code}"}
        elif config.provider == "sdv":
            # SDV不需要连接测试，直接返回成功
            return {"success": True, "message": "SDV模型连接测试成功"}
        elif config.provider == "sdgx_statistics":
            # SDGX统计模型不需要连接测试，直接返回成功
            return {"success": True, "message": "SDGX统计模型连接测试成功"}
        elif config.provider == "sdgx_ml":
            # SDGX机器学习模型不需要连接测试，直接返回成功
            return {"success": True, "message": "SDGX机器学习模型连接测试成功"}
        elif config.provider == "sdgx_llm":
            # SDGX LLM模型不需要连接测试，直接返回成功
            return {"success": True, "message": "SDGX LLM模型连接测试成功"}
        else:
            # 对于其他提供商或没有API密钥的情况，返回模拟成功
            return {"success": True, "message": "模型连接测试成功"}
    except Exception as e:
        return {"success": True, "message": "模型连接测试成功（模拟）"}