"""Agent 核心类 - 整合 LLM 和函数调用。

本模块实现了 Agent 核心类，负责整合大语言模型（LLM）提供商和函数调用
机制，提供统一的对话接口。Agent 支持多轮对话、函数调用和自动迭代处理。
"""
from typing import List, Dict, Any, Optional, Callable
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse
from agent.functions.registry import FunctionRegistry
from agent.functions.executor import ToolExecutor


class Agent:
    """Agent 核心类，整合 LLM 提供商和函数调用机制。

    Agent 类提供了统一的对话接口，支持常规对话和函数调用。当 LLM 决定
    调用函数时，Agent 会自动执行函数并将结果返回给 LLM，实现多轮迭代
    直到获得最终回复。

    Attributes:
        provider: LLM 提供商实例，负责与底层模型交互。
        function_registry: 函数注册表，管理所有可调用的函数。
        tool_executor: 工具执行器，负责执行函数调用。
        system_prompt: 系统提示词，用于初始化对话上下文。
        conversation_history: 对话历史记录，包含所有消息。

    Example:
        ```python
        from agent import Agent, create_provider, FunctionRegistry

        provider = create_provider("openai", api_key="sk-...")
        registry = FunctionRegistry()
        agent = Agent(provider, registry, system_prompt="你是一个助手")

        response = await agent.chat("查询用户信息")
        print(response["content"])
        ```
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        function_registry: Optional[FunctionRegistry] = None,
        system_prompt: Optional[str] = None
    ) -> None:
        """初始化 Agent 实例。

        Args:
            provider: LLM 提供商实例，必须实现 LLMProvider 接口。
            function_registry: 函数注册表。如果为 None，将创建空的注册表，
                此时 Agent 不支持函数调用功能。
            system_prompt: 系统提示词，用于设置 Agent 的行为和角色。
                如果提供，会自动添加到对话历史的开头。

        Raises:
            TypeError: 如果 provider 不是 LLMProvider 的实例。
        """
        self.provider = provider
        self.function_registry = function_registry or FunctionRegistry()
        self.tool_executor = ToolExecutor(self.function_registry)
        self.system_prompt = system_prompt
        self.conversation_history: List[LLMMessage] = []
        
        # 如果提供了系统提示词，添加到历史记录
        if self.system_prompt:
            self.conversation_history.append(
                LLMMessage(role="system", content=self.system_prompt)
            )
    
    async def chat(
        self,
        user_message: str,
        max_iterations: int = 10,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """与 Agent 进行对话。

        此方法支持多轮迭代：如果 LLM 决定调用函数，Agent 会执行函数并将
        结果返回给 LLM，LLM 可以基于结果继续处理或调用更多函数，直到
        获得最终回复。

        Args:
            user_message: 用户输入的消息内容。
            max_iterations: 最大迭代次数，用于限制函数调用的循环次数。
                当达到最大次数时，即使还有函数调用也会停止并返回当前结果。
                默认值为 10。
            **kwargs: 传递给 LLM 提供商的额外参数，如 temperature、
                max_tokens 等。

        Returns:
            包含以下键的字典：
                - content (str): LLM 的最终回复内容。
                - function_calls (List[Dict[str, Any]]): 本次对话中调用的
                    所有函数列表，每个元素包含 name 和 arguments 键。
                - iterations (int): 实际执行的迭代次数。

        Raises:
            Exception: 如果 LLM 提供商调用失败或函数执行出错。

        Note:
            - 用户消息会自动添加到对话历史中。
            - 如果 LLM 不支持函数调用或未注册任何函数，将直接返回回复。
            - 函数执行错误会被捕获并作为 function 消息添加到历史中。
        """
        # 添加用户消息到对话历史
        self.conversation_history.append(
            LLMMessage(role="user", content=user_message)
        )
        
        iterations: int = 0
        function_calls_made: List[Dict[str, Any]] = []
        
        # 迭代处理：支持多轮函数调用
        while iterations < max_iterations:
            iterations += 1
            
            # 准备函数定义列表（如果支持函数调用）
            functions: Optional[List[Dict[str, Any]]] = None
            if self.function_registry and self.provider.supports_function_calling():
                functions = self.function_registry.list_functions()
            
            # 调用 LLM 提供商获取回复
            response: LLMResponse = await self.provider.chat(
                messages=self.conversation_history,
                functions=functions,
                **kwargs
            )
            
            # 将助手回复添加到对话历史
            self.conversation_history.append(
                LLMMessage(role="assistant", content=response.content)
            )
            
            # 如果没有函数调用，直接返回最终回复
            if not response.function_calls:
                return {
                    "content": response.content,
                    "function_calls": function_calls_made,
                    "iterations": iterations
                }
            
            # 处理函数调用：执行每个函数并将结果返回给 LLM
            for func_call in response.function_calls:
                # 记录函数调用信息
                function_calls_made.append({
                    "name": func_call.name,
                    "arguments": func_call.arguments
                })
                
                try:
                    # 执行函数调用
                    result: Any = await self.tool_executor.execute(
                        func_call.name,
                        func_call.arguments
                    )
                    
                    # 格式化函数执行结果为字符串
                    result_str: str = self.tool_executor.format_result(result)
                    
                    # 将函数结果作为 function 消息添加到对话历史
                    # LLM 会在下一轮迭代中看到这个结果
                    self.conversation_history.append(
                        LLMMessage(
                            role="function",
                            content=result_str,
                            name=func_call.name
                        )
                    )
                    
                except Exception as e:
                    # 函数执行失败时，记录错误并添加到对话历史
                    logger.error(f"Error executing function {func_call.name}: {e}")
                    self.conversation_history.append(
                        LLMMessage(
                            role="function",
                            content=f"错误: {str(e)}",
                            name=func_call.name
                        )
                    )
            
            # 继续循环，让 LLM 基于函数结果继续处理
        
        # 达到最大迭代次数，返回当前结果
        logger.warning(f"Reached max iterations ({max_iterations})")
        return {
            "content": response.content,
            "function_calls": function_calls_made,
            "iterations": iterations
        }
    
    async def parse_message(
        self,
        sender: str,
        timestamp: str,
        content: str,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """解析消息并提取结构化数据（兼容原有接口）。

        此方法用于从非结构化消息中提取结构化数据，通常用于解析聊天记录
        或消息日志。LLM 会分析消息内容并返回 JSON 格式的结构化数据。

        Args:
            sender: 消息发送者的名称或标识。
            timestamp: 消息的时间戳，格式可以是任意字符串。
            content: 消息的文本内容。
            **kwargs: 传递给 chat 方法的额外参数。

        Returns:
            解析后的结构化数据列表。每个元素是一个字典，包含提取的字段。
            如果解析失败，可能返回包含错误信息的字典。

        Raises:
            json.JSONDecodeError: 如果 LLM 返回的内容不是有效的 JSON 格式。

        Note:
            - 此方法会构建一个包含发送者、时间戳和内容的提示词。
            - LLM 返回的 JSON 会被解析，支持单个对象或数组格式。
            - 如果返回的是单个对象，会自动转换为列表。
        """
        # 构建解析提示词
        user_prompt: str = f"""消息发送者: {sender}
消息时间: {timestamp}
消息内容:
{content}

请提取结构化数据。返回 JSON 数组格式。"""
        
        # 调用 chat 方法获取 LLM 回复
        response: Dict[str, Any] = await self.chat(user_prompt, **kwargs)
        
        # 解析 JSON 响应
        import json
        import re
        
        content_text: str = response["content"]
        
        # 清理可能的 markdown code block（LLM 可能返回 ```json ... ``` 格式）
        content_text = content_text.strip()
        if content_text.startswith("```"):
            content_text = re.sub(r'^```(?:json)?\s*', '', content_text)
            content_text = re.sub(r'\s*```$', '', content_text)
        
        try:
            # 解析 JSON 内容
            data: Any = json.loads(content_text)
            
            # 处理不同的返回格式
            if isinstance(data, dict):
                # 如果返回的是包含 records 键的字典，提取 records
                if "records" in data:
                    return data["records"]
                # 否则将单个对象转换为列表
                return [data]
            elif isinstance(data, list):
                # 如果已经是列表，直接返回
                return data
            else:
                # 意外的格式，返回噪声标记
                logger.warning(f"Unexpected response format: {type(data)}")
                return [{"type": "noise"}]
        except json.JSONDecodeError as e:
            # JSON 解析失败，记录错误并返回错误信息
            logger.error(f"JSON parse error: {e}, text: {content_text[:200]}")
            return [{"type": "noise", "error": str(e)}]
    
    def clear_history(self) -> None:
        """清空对话历史记录。

        此方法会重置 conversation_history，但会保留系统提示词（如果存在）。
        清空后，对话历史只包含系统提示词（如果有）。

        Note:
            - 清空历史后，Agent 将失去之前的所有对话上下文。
            - 如果设置了 system_prompt，它会被重新添加到历史中。
        """
        self.conversation_history = []
        if self.system_prompt:
            self.conversation_history.append(
                LLMMessage(role="system", content=self.system_prompt)
            )
    
    def register_function(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册函数到函数注册表（便捷方法）。

        这是一个便捷方法，用于直接向 Agent 的函数注册表中添加新函数。
        注册后的函数可以被 LLM 通过函数调用机制调用。

        Args:
            name: 函数的唯一标识名称，LLM 将使用此名称调用函数。
            description: 函数的描述信息，用于帮助 LLM 理解函数的用途。
                描述应该清晰说明函数的功能、参数和返回值。
            func: 要注册的函数对象，可以是同步或异步函数。
            parameters: 函数的参数 Schema（JSON Schema 格式）。如果为 None，
                将根据函数签名自动推断参数类型。

        Note:
            - 如果函数名已存在，会覆盖之前的注册（会记录警告日志）。
            - 参数 Schema 用于 LLM 理解函数参数的类型和约束。
        """
        self.function_registry.register(name, description, func, parameters)

