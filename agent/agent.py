"""Agent 核心类 - 整合 LLM 和函数调用。

本模块实现了 Agent 核心类，负责整合大语言模型（LLM）提供商和函数调用
机制，提供统一的对话接口。Agent 支持多轮对话、函数调用和自动迭代处理。

对用户透明的多模型支持：
    Agent 通过 LLMProvider 抽象接口与底层模型交互，用户无需关心
    使用的是 OpenAI、Claude 还是 MiniMax，切换模型只需更换 Provider。

函数调用流程：
    1. 用户发送消息 → Agent 调用 Provider
    2. Provider 返回 LLMResponse（可能包含 function_calls）
    3. Agent 存储 assistant 消息（包含 tool_calls 和 provider_extras）
    4. Agent 执行每个函数调用，存储 tool 消息（包含 tool_call_id）
    5. 重复 2-4 直到 LLM 给出最终回复或达到最大迭代次数
"""
from typing import List, Dict, Any, Optional, Callable
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse
from agent.functions.registry import FunctionRegistry
from agent.functions.executor import ToolExecutor


class Agent:
    """Agent 核心类，整合 LLM 提供商和函数调用机制。

    Agent 提供统一的对话接口，对用户透明地支持不同的模型提供商。
    当 LLM 决定调用函数时，Agent 自动执行并将结果返回给 LLM，
    实现多轮迭代直到获得最终回复。

    关键设计：
        - tool_calls 和 tool_call_id 的正确跟踪，确保多轮工具调用
          在所有提供商上都能正确工作
        - provider_extras 透传机制，让 Anthropic 系列提供商能在
          多轮对话中保持完整的上下文（包括 thinking 块等）

    Attributes:
        provider: LLM 提供商实例。
        function_registry: 函数注册表。
        tool_executor: 工具执行器。
        system_prompt: 系统提示词。
        conversation_history: 对话历史记录。

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
        system_prompt: Optional[str] = None,
    ) -> None:
        """初始化 Agent 实例。

        Args:
            provider: LLM 提供商实例，必须实现 LLMProvider 接口。
            function_registry: 函数注册表。如果为 None，创建空注册表。
            system_prompt: 系统提示词，设置 Agent 的行为和角色。
        """
        self.provider = provider
        self.function_registry = function_registry or FunctionRegistry()
        self.tool_executor = ToolExecutor(self.function_registry)
        self.system_prompt = system_prompt
        self.conversation_history: List[LLMMessage] = []

        # 添加系统提示词到历史记录
        if self.system_prompt:
            self.conversation_history.append(
                LLMMessage(role="system", content=self.system_prompt)
            )

    async def chat(
        self,
        user_message: str,
        max_iterations: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """与 Agent 进行对话。

        支持多轮迭代：如果 LLM 决定调用函数，Agent 会执行函数并将
        结果返回给 LLM，LLM 可以基于结果继续处理或调用更多函数，
        直到获得最终回复。

        Args:
            user_message: 用户输入的消息内容。
            max_iterations: 最大迭代次数，默认 10。
            **kwargs: 传递给 LLM 提供商的额外参数。

        Returns:
            包含以下键的字典：
                - content (str): LLM 的最终回复内容。
                - function_calls (List[Dict]): 所有函数调用记录。
                - iterations (int): 实际迭代次数。
        """
        # 添加用户消息到对话历史
        self.conversation_history.append(
            LLMMessage(role="user", content=user_message)
        )

        iterations: int = 0
        function_calls_made: List[Dict[str, Any]] = []
        response: Optional[LLMResponse] = None

        # 迭代处理：支持多轮函数调用
        while iterations < max_iterations:
            iterations += 1

            # 准备函数定义列表（如果支持函数调用且有注册函数）
            functions: Optional[List[Dict[str, Any]]] = None
            if (self.function_registry
                    and self.provider.supports_function_calling()):
                func_list = self.function_registry.list_functions()
                if func_list:
                    functions = func_list

            # 调用 LLM 提供商获取回复
            response = await self.provider.chat(
                messages=self.conversation_history,
                functions=functions,
                **kwargs,
            )

            # 将 assistant 回复添加到对话历史
            # 关键：保留 tool_calls 和 provider_extras，确保
            # Provider 在下一轮请求中能恢复完整上下文
            assistant_msg = LLMMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.function_calls,
                provider_extras=response.raw_response,
            )
            self.conversation_history.append(assistant_msg)

            # 如果没有函数调用，返回最终回复
            if not response.function_calls:
                return {
                    "content": response.content,
                    "function_calls": function_calls_made,
                    "iterations": iterations,
                }

            # 处理函数调用：执行每个函数并将结果返回给 LLM
            for func_call in response.function_calls:
                # 记录函数调用信息
                function_calls_made.append({
                    "name": func_call.name,
                    "arguments": func_call.arguments,
                })

                try:
                    # 执行函数调用
                    result: Any = await self.tool_executor.execute(
                        func_call.name, func_call.arguments
                    )

                    # 格式化函数执行结果
                    result_str: str = self.tool_executor.format_result(result)

                    # 将函数结果添加到对话历史
                    # 使用 role="tool" + tool_call_id 关联调用和结果
                    self.conversation_history.append(
                        LLMMessage(
                            role="tool",
                            content=result_str,
                            name=func_call.name,
                            tool_call_id=func_call.id,
                        )
                    )

                except Exception as e:
                    # 函数执行失败，记录错误到对话历史
                    logger.error(
                        f"Error executing function {func_call.name}: {e}"
                    )
                    self.conversation_history.append(
                        LLMMessage(
                            role="tool",
                            content=f"错误: {str(e)}",
                            name=func_call.name,
                            tool_call_id=func_call.id,
                        )
                    )

            # 继续循环，让 LLM 基于函数结果继续处理

        # 达到最大迭代次数
        logger.warning(f"Reached max iterations ({max_iterations})")
        return {
            "content": response.content if response else "",
            "function_calls": function_calls_made,
            "iterations": iterations,
        }

    async def parse_message(
        self,
        sender: str,
        timestamp: str,
        content: str,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """解析消息并提取结构化数据（兼容原有接口）。

        此方法用于从非结构化消息中提取结构化数据，LLM 会分析消息内容
        并返回 JSON 格式的结构化数据。

        Args:
            sender: 消息发送者。
            timestamp: 消息时间戳。
            content: 消息文本内容。
            **kwargs: 传递给 chat 方法的额外参数。

        Returns:
            解析后的结构化数据列表。
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

        # 清理 Markdown code block
        content_text = content_text.strip()
        if content_text.startswith("```"):
            content_text = re.sub(r'^```(?:json)?\s*', '', content_text)
            content_text = re.sub(r'\s*```$', '', content_text)

        try:
            data: Any = json.loads(content_text)

            if isinstance(data, dict):
                if "records" in data:
                    return data["records"]
                return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                return [{"type": "noise"}]
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON parse error: {e}, text: {content_text[:200]}"
            )
            return [{"type": "noise", "error": str(e)}]

    def clear_history(self) -> None:
        """清空对话历史记录，保留系统提示词。"""
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
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """注册函数到函数注册表（便捷方法）。

        Args:
            name: 函数名称。
            description: 函数描述。
            func: 函数对象（同步或异步）。
            parameters: 参数 Schema（JSON Schema 格式）。
        """
        self.function_registry.register(name, description, func, parameters)
