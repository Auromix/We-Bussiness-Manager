"""函数注册表 - 管理 Agent 可调用的函数。

本模块实现了函数注册表，用于管理所有可以被 Agent 调用的函数。
注册表维护函数的名称、描述、参数 Schema 和实际函数对象，并提供
转换为 LLM function calling 格式的功能。
"""
from typing import Dict, Callable, Any, List, Optional, Union, get_origin, get_args
from dataclasses import dataclass
from inspect import signature, Parameter
import json
from loguru import logger


@dataclass
class FunctionDefinition:
    """函数定义数据类，存储函数的完整信息。

    此数据类用于在函数注册表中存储函数的元数据和实际函数对象。

    Attributes:
        name: 函数的唯一标识名称，LLM 将使用此名称调用函数。
        description: 函数的描述信息，帮助 LLM 理解函数的用途和功能。
        parameters: 函数的参数 Schema，使用 JSON Schema 格式。
            包含参数的类型、是否必需、默认值等信息。
        func: 实际的函数对象，可以是同步或异步函数。

    Example:
        ```python
        def get_customer(name: str) -> dict:
            return {"name": name, "id": 123}

        func_def = FunctionDefinition(
            name="get_customer",
            description="根据名称获取顾客信息",
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            },
            func=get_customer
        )
        ```
    """
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema 格式
    func: Callable[..., Any]


class FunctionRegistry:
    """函数注册表，管理 Agent 可以调用的所有函数。

    函数注册表是 Agent 函数调用机制的核心组件，负责：
    1. 注册函数及其元数据（名称、描述、参数 Schema）
    2. 根据函数签名自动推断参数类型
    3. 提供函数列表供 LLM function calling 使用

    注册的函数可以包括：
    - 仓库函数（数据库查询、保存等）
    - 业务逻辑函数（会员管理、库存管理等）
    - 工具函数（格式化、计算等）

    Attributes:
        _functions: 内部字典，存储所有已注册的函数定义。
            键为函数名称，值为 FunctionDefinition 对象。

    Example:
        ```python
        registry = FunctionRegistry()

        # 手动注册函数
        registry.register(
            name="get_customer",
            description="获取顾客信息",
            func=get_customer_func,
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        )

        # 自动推断参数类型
        registry.register(
            name="save_record",
            description="保存记录",
            func=save_record_func
        )

        # 获取函数列表供 LLM 使用
        functions = registry.list_functions()
        ```
    """
    
    def __init__(self) -> None:
        """初始化函数注册表。

        创建一个空的函数注册表，可以开始注册函数。
        """
        self._functions: Dict[str, FunctionDefinition] = {}
    
    def register(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册函数到注册表中。

        此方法将函数及其元数据添加到注册表。如果函数名已存在，会覆盖
        之前的注册（会记录警告日志）。

        Args:
            name: 函数的唯一标识名称。LLM 将使用此名称调用函数，因此
                应该使用清晰、描述性的名称，如 "get_customer"、"save_record"。
            description: 函数的描述信息，用于帮助 LLM 理解函数的用途。
                描述应该清晰说明函数的功能、参数含义和返回值。
            func: 要注册的函数对象。可以是同步函数或异步函数（协程）。
                函数签名会被用于自动推断参数类型。
            parameters: 可选的参数 JSON Schema。如果为 None，将根据函数
                签名自动推断参数类型。Schema 应该遵循 JSON Schema 规范：
                {
                    "type": "object",
                    "properties": {
                        "param_name": {"type": "string", ...}
                    },
                    "required": ["param_name"]
                }

        Note:
            - 如果函数名已存在，会覆盖之前的注册并记录警告。
            - 自动推断的参数类型可能不够精确，建议手动提供 parameters。
            - 函数可以是同步或异步的，执行器会自动处理。
        """
        if name in self._functions:
            logger.warning(f"Function {name} already registered, overwriting")
        
        # 如果没有提供 parameters，尝试自动生成
        if parameters is None:
            parameters = self._infer_parameters(func)
        
        self._functions[name] = FunctionDefinition(
            name=name,
            description=description,
            parameters=parameters,
            func=func
        )
    
    def _infer_parameters(self, func: Callable[..., Any]) -> Dict[str, Any]:
        """从函数签名自动推断参数 Schema。

        此方法通过分析函数的类型注解和默认值，自动生成 JSON Schema
        格式的参数定义。支持基本的 Python 类型（str、int、float、bool、
        list、dict）和 Optional/Union 类型。

        Args:
            func: 要分析签名的函数对象。

        Returns:
            符合 JSON Schema 格式的参数定义字典，包含 type、properties
            和 required 字段。

        Note:
            - 只支持基本的 Python 类型，复杂类型可能被推断为 "string"。
            - Optional[T] 类型会被正确处理，参数变为可选。
            - 如果参数没有类型注解，默认推断为 "string"。
        """
        sig = signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            param_info = {
                "type": self._python_type_to_json_type(param.annotation)
            }
            
            if param.default != Parameter.empty:
                param_info["default"] = param.default
            else:
                required.append(param_name)
            
            properties[param_name] = param_info
        
        schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            schema["required"] = required
        
        return schema
    
    def _python_type_to_json_type(self, annotation: Any) -> str:
        """将 Python 类型注解转换为 JSON Schema 类型字符串。

        此方法将 Python 的类型注解（如 str、int、Optional[str]）转换为
        JSON Schema 类型字符串（如 "string"、"integer"）。

        Args:
            annotation: Python 类型注解，可以是类型对象或类型表达式
                （如 Optional[str]）。

        Returns:
            JSON Schema 类型字符串，可能的值为：
            - "string": 字符串类型
            - "integer": 整数类型
            - "number": 浮点数类型
            - "boolean": 布尔类型
            - "array": 列表类型
            - "object": 字典类型
            如果无法识别，默认返回 "string"。

        Note:
            - 支持处理 Optional[T] 和 Union[T, None] 类型。
            - 只提取非 None 的类型进行转换。
            - 对于未识别的类型，默认返回 "string"。
        """
        type_mapping: Dict[type, str] = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        
        # 处理 Optional 类型和 Union 类型
        origin: Optional[Any] = get_origin(annotation)
        if origin is not None:
            # 处理 Union 或 Optional（Optional 是 Union[T, None] 的别名）
            args: tuple = get_args(annotation)
            # 获取非 None 的类型
            non_none_args: List[Any] = [
                arg for arg in args if arg is not type(None)
            ]
            if non_none_args:
                return type_mapping.get(non_none_args[0], "string")
        
        return type_mapping.get(annotation, "string")
    
    def get_function(self, name: str) -> Optional[FunctionDefinition]:
        """根据名称获取函数定义。

        Args:
            name: 要查找的函数名称。

        Returns:
            如果找到，返回 FunctionDefinition 对象；否则返回 None。
        """
        return self._functions.get(name)
    
    def list_functions(self) -> List[Dict[str, Any]]:
        """列出所有已注册的函数，转换为 LLM function calling 格式。

        此方法返回所有已注册函数的列表，格式符合 LLM function calling
        的要求。每个函数包含 name、description 和 parameters 字段。

        Returns:
            函数定义列表，每个元素是一个字典，包含：
            - name (str): 函数名称
            - description (str): 函数描述
            - parameters (Dict[str, Any]): 参数 Schema（JSON Schema 格式）

        Example:
            ```python
            functions = registry.list_functions()
            # 返回:
            # [
            #     {
            #         "name": "get_customer",
            #         "description": "获取顾客信息",
            #         "parameters": {...}
            #     },
            #     ...
            # ]
            ```
        """
        return [
            {
                "name": func.name,
                "description": func.description,
                "parameters": func.parameters
            }
            for func in self._functions.values()
        ]
    
    def has_function(self, name: str) -> bool:
        """检查指定名称的函数是否已注册。

        Args:
            name: 要检查的函数名称。

        Returns:
            True 如果函数已注册，False 否则。
        """
        return name in self._functions

