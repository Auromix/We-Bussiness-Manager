"""工具执行器 - 执行 Agent 调用的函数。

本模块实现了工具执行器，负责执行 Agent 通过 function calling 机制
调用的函数。执行器会从注册表中查找函数，执行函数调用，并格式化结果
供 LLM 使用。
"""
from typing import Dict, Any, Optional
from loguru import logger

from agent.functions.registry import FunctionRegistry, FunctionDefinition


class ToolExecutor:
    """工具执行器，负责执行 Agent 调用的函数。

    工具执行器是函数调用机制的执行层，负责：
    1. 从函数注册表中查找要调用的函数
    2. 执行函数调用（支持同步和异步函数）
    3. 格式化函数执行结果为字符串，供 LLM 使用

    Attributes:
        registry: 函数注册表实例，用于查找函数定义。

    Example:
        ```python
        registry = FunctionRegistry()
        registry.register("get_customer", "获取顾客", get_customer_func)

        executor = ToolExecutor(registry)
        result = await executor.execute(
            "get_customer",
            {"name": "张三"}
        )
        formatted = executor.format_result(result)
        ```
    """
    
    def __init__(self, registry: FunctionRegistry) -> None:
        """初始化工具执行器。

        Args:
            registry: 函数注册表实例，用于查找和执行函数。
                执行器会从此注册表中查找函数定义。

        Raises:
            TypeError: 如果 registry 不是 FunctionRegistry 的实例。
        """
        self.registry = registry
    
    async def execute(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """执行函数调用。

        此方法从注册表中查找函数，使用提供的参数执行函数，并返回结果。
        如果函数是异步的（协程），会自动等待其完成。

        Args:
            function_name: 要调用的函数名称，必须与注册表中的名称一致。
            arguments: 函数参数字典，键为参数名，值为参数值。
                参数值必须符合函数定义的参数类型和约束。

        Returns:
            函数执行的结果。返回值类型取决于具体函数，可以是任意类型。

        Raises:
            ValueError: 如果函数不存在于注册表中，或函数没有实现。
            Exception: 如果函数执行过程中发生错误。具体的异常类型
                取决于函数本身的实现。

        Note:
            - 函数可以是同步或异步的，执行器会自动检测并处理。
            - 如果函数返回协程对象，会自动等待其完成。
            - 函数执行过程中的所有异常都会被记录并重新抛出。
        """
        func_def: Optional[FunctionDefinition] = self.registry.get_function(
            function_name
        )
        
        if not func_def:
            raise ValueError(
                f"Function {function_name} not found in registry"
            )
        
        try:
            # 调用函数，使用关键字参数展开
            if func_def.func:
                result: Any = func_def.func(**arguments)
                # 如果结果是协程（异步函数），等待其完成
                if hasattr(result, "__await__"):
                    result = await result
                return result
            else:
                raise ValueError(
                    f"Function {function_name} has no implementation"
                )
                
        except Exception as e:
            logger.error(
                f"Error executing function {function_name} with "
                f"arguments {arguments}: {e}"
            )
            raise
    
    def format_result(self, result: Any) -> str:
        """格式化函数执行结果为字符串，供 LLM 使用。

        此方法将函数的返回值转换为字符串格式，以便添加到对话历史中。
        对于字典和列表，会转换为格式化的 JSON 字符串；对于其他类型，
        使用 str() 转换。

        Args:
            result: 函数执行的结果，可以是任意类型。

        Returns:
            格式化的字符串表示。如果 result 是 None，返回 "执行成功"。
            如果是字典或列表，返回格式化的 JSON 字符串（使用中文编码）。
            其他类型使用 str() 转换。

        Note:
            - JSON 序列化使用 ensure_ascii=False 以支持中文字符。
            - 如果 JSON 序列化失败，会回退到 str() 转换。
            - None 值会被转换为 "执行成功" 字符串。
        """
        import json
        
        if result is None:
            return "执行成功"
        
        # 如果是字典或列表，转换为格式化的 JSON 字符串
        if isinstance(result, (dict, list)):
            try:
                return json.dumps(result, ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                # JSON 序列化失败（可能包含不可序列化的对象），回退到 str()
                logger.warning(
                    f"Failed to serialize result to JSON: {e}, "
                    f"falling back to str()"
                )
                return str(result)
        
        # 其他类型直接转换为字符串
        return str(result)

