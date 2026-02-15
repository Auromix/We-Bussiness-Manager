"""函数调用模块 - 管理 Agent 可调用的函数。

本模块提供了函数调用机制的完整实现，包括：
1. FunctionRegistry: 函数注册表，管理所有可调用的函数
2. ToolExecutor: 工具执行器，负责执行函数调用
3. 自动发现机制：自动发现和注册代码库中的函数

使用示例：
    ```python
    from agent.functions import FunctionRegistry, ToolExecutor
    from agent.functions import register_instance_methods

    # 创建函数注册表
    registry = FunctionRegistry()

    # 自动注册对象的所有方法
    register_instance_methods(registry, db_repo, prefix="db_")

    # 创建执行器
    executor = ToolExecutor(registry)

    # 执行函数调用
    result = await executor.execute("db_get_customer", {"name": "张三"})
    ```
"""

from agent.functions.registry import FunctionRegistry
from agent.functions.executor import ToolExecutor
from agent.functions.discovery import (
    agent_callable,
    register_instance_methods,
    register_module_functions,
    register_class_methods,
    auto_discover_and_register
)

__all__ = [
    "FunctionRegistry",
    "ToolExecutor",
    "agent_callable",
    "register_instance_methods",
    "register_module_functions",
    "register_class_methods",
    "auto_discover_and_register",
]

