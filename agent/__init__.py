"""Agent 模块 - 大模型调用和函数调用框架

本模块提供了一个可扩展的 Agent 架构，支持多种大语言模型（LLM）提供商
和函数调用（Function Calling）机制。

主要组件：
    1. LLMProvider: LLM 提供商的抽象基类，支持多种模型接入
    2. Agent: 核心 Agent 类，整合 LLM 和函数调用功能
    3. FunctionRegistry: 函数注册表，管理 Agent 可调用的函数
    4. ToolExecutor: 工具执行器，负责执行函数调用

使用示例：
    ```python
    from agent import Agent, create_provider, FunctionRegistry

    # 创建 LLM 提供商
    provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

    # 创建函数注册表
    registry = FunctionRegistry()

    # 创建 Agent
    agent = Agent(provider, registry, system_prompt="你是一个有用的助手")

    # 与 Agent 对话
    response = await agent.chat("查询顾客信息")
    ```
"""

from agent.providers import LLMProvider, create_provider
from agent.functions import FunctionRegistry, ToolExecutor
from agent.agent import Agent

__all__ = [
    "LLMProvider",
    "create_provider",
    "FunctionRegistry",
    "ToolExecutor",
    "Agent",
]

