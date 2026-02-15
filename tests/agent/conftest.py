"""Agent 测试的共享 fixtures 和配置。

本模块提供了 agent 测试所需的共享 fixtures，包括：
- Mock LLM Provider
- Function Registry
- 测试用的函数和类
- 环境变量配置支持
"""
import pytest
import os
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, MagicMock
from dataclasses import dataclass

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall
from agent.functions.registry import FunctionRegistry
from agent.functions.executor import ToolExecutor


# 从环境变量读取测试配置
def get_test_config() -> Dict[str, Any]:
    """从环境变量读取测试配置。
    
    Returns:
        包含测试配置的字典：
        - use_real_api: 是否使用真实 API（默认 False）
        - provider_type: 提供商类型（openai/claude/open_source）
        - api_key: API Key（如果使用真实 API）
        - model: 模型名称
        - base_url: 基础 URL（开源模型需要）
    """
    return {
        "use_real_api": os.getenv("AGENT_TEST_USE_REAL_API", "false").lower() == "true",
        "provider_type": os.getenv("AGENT_TEST_PROVIDER_TYPE", "openai").lower(),
        "api_key": os.getenv("AGENT_TEST_API_KEY", ""),
        "model": os.getenv("AGENT_TEST_MODEL", "gpt-4o-mini"),
        "base_url": os.getenv("AGENT_TEST_BASE_URL", ""),
    }


@pytest.fixture
def test_config():
    """测试配置 fixture"""
    return get_test_config()


@pytest.fixture
def mock_llm_provider():
    """创建 Mock LLM Provider。
    
    返回一个实现了 LLMProvider 接口的 Mock 对象，可以用于测试
    而不需要真实的 API 调用。
    """
    provider = Mock(spec=LLMProvider)
    provider.model_name = "mock-model"
    provider.supports_function_calling = Mock(return_value=True)
    
    # 默认响应：普通文本回复
    async def mock_chat(messages, functions=None, **kwargs):
        return LLMResponse(
            content="这是一个测试回复",
            function_calls=None,
            finish_reason="stop"
        )
    
    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.fixture
def mock_llm_provider_with_function_calling():
    """创建支持函数调用的 Mock LLM Provider。
    
    返回一个 Mock Provider，会返回函数调用响应。
    """
    provider = Mock(spec=LLMProvider)
    provider.model_name = "mock-model"
    provider.supports_function_calling = Mock(return_value=True)
    
    # 第一次调用返回函数调用，第二次返回最终回复
    call_count = {"count": 0}
    
    async def mock_chat(messages, functions=None, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            # 第一次调用：返回函数调用
            return LLMResponse(
                content="",
                function_calls=[
                    FunctionCall(
                        name="test_function",
                        arguments={"param1": "value1"}
                    )
                ],
                finish_reason="tool_calls"
            )
        else:
            # 后续调用：返回最终回复
            return LLMResponse(
                content="函数执行完成，这是最终回复",
                function_calls=None,
                finish_reason="stop"
            )
    
    provider.chat = AsyncMock(side_effect=mock_chat)
    return provider


@pytest.fixture
def function_registry():
    """创建空的函数注册表"""
    return FunctionRegistry()


@pytest.fixture
def tool_executor(function_registry):
    """创建工具执行器"""
    return ToolExecutor(function_registry)


# 测试用的函数
def sync_test_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """同步测试函数"""
    return {"result": f"{param1}_{param2}", "type": "sync"}


async def async_test_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """异步测试函数"""
    return {"result": f"{param1}_{param2}", "type": "async"}


def sample_function_no_params() -> str:
    """无参数的测试函数"""
    return "no_params_result"


def sample_function_with_optional(param1: str, param2: Optional[str] = None) -> str:
    """带可选参数的测试函数"""
    if param2:
        return f"{param1}_{param2}"
    return param1


@pytest.fixture
def sample_functions():
    """提供示例函数列表"""
    return {
        "sync_test_function": sync_test_function,
        "async_test_function": async_test_function,
        "sample_function_no_params": sample_function_no_params,
        "sample_function_with_optional": sample_function_with_optional,
    }


# 测试用的类
class SampleService:
    """测试服务类，用于测试实例方法注册"""
    
    def __init__(self, name: str):
        self.name = name
    
    def get_info(self) -> Dict[str, str]:
        """获取信息"""
        return {"name": self.name, "type": "service"}
    
    def process_data(self, data: str) -> str:
        """处理数据"""
        return f"processed_{data}"
    
    def _private_method(self) -> str:
        """私有方法，不应该被注册"""
        return "private"
    
    def __special_method__(self) -> str:
        """特殊方法，不应该被注册"""
        return "special"


@pytest.fixture
def test_service():
    """创建测试服务实例"""
    return SampleService("test_service")


# 测试用的模块函数（模拟）
test_module_functions = {
    "module_func_1": lambda x: f"module_result_{x}",
    "module_func_2": lambda x, y: f"module_result_{x}_{y}",
}


@pytest.fixture
def populated_registry(function_registry, sample_functions):
    """创建已填充函数的注册表"""
    for name, func in sample_functions.items():
        function_registry.register(
            name=name,
            description=f"测试函数: {name}",
            func=func
        )
    return function_registry

