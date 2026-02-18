"""Agent 模块 - 大模型调用和函数调用框架。

本模块提供了一个可扩展的 Agent 架构，支持多种大语言模型（LLM）提供商
和函数调用（Function Calling）机制。

架构概览：
    ┌─────────────────────────────────────────────────┐
    │               Agent (agent.py)                  │  ← 对话控制器
    ├─────────────┬───────────────────────────────────┤
    │ Providers   │   Functions                       │
    │ ┌─────────┐ │ ┌───────────────┐                 │
    │ │ OpenAI  │ │ │ Registry      │ ← 函数注册表    │
    │ │ Claude  │ │ │ Executor      │ ← 工具执行器    │
    │ │ MiniMax │ │ │ Discovery     │ ← 自动发现      │
    │ │ Custom  │ │ └───────────────┘                 │
    │ └─────────┘ │                                   │
    └─────────────┴───────────────────────────────────┘

主要组件：
    1. LLMProvider: LLM 提供商抽象基类，支持多种模型接入
    2. Agent: 核心 Agent 类，整合 LLM 和函数调用功能
    3. FunctionRegistry: 函数注册表，管理 Agent 可调用的函数
    4. ToolExecutor: 工具执行器，负责执行函数调用

使用示例：
    ```python
    from agent import Agent, create_provider, FunctionRegistry

    # 创建 LLM 提供商（对用户透明，切换模型只需改这里）
    provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

    # 创建函数注册表并注册业务函数
    registry = FunctionRegistry()

    # 创建 Agent
    agent = Agent(provider, registry, system_prompt="你是一个有用的助手")

    # 与 Agent 对话（Agent 会自动调用函数并返回结果）
    response = await agent.chat("查询顾客信息")
    ```
"""
from agent._version import __version__
from agent.providers import LLMProvider, create_provider
from agent.providers.base import LLMMessage, LLMResponse, FunctionCall
from agent.functions import FunctionRegistry, ToolExecutor
from agent.agent import Agent

__all__ = [
    "__version__",
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "FunctionCall",
    "create_provider",
    "FunctionRegistry",
    "ToolExecutor",
    "Agent",
]
