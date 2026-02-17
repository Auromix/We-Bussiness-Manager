"""Anthropic Claude 提供商实现。

本模块实现了 Anthropic Claude 系列模型的提供商，支持通过 Anthropic API
调用 Claude 模型。
"""
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class ClaudeProvider(LLMProvider):
    """Anthropic Claude 模型提供商。

    此提供商支持所有 Anthropic Claude 系列模型，包括 Claude Sonnet、
    Claude Opus 等。

    Attributes:
        client: Anthropic 客户端实例，用于发送 API 请求。
        _model: 当前使用的模型名称。

    Example:
        ```python
        provider = ClaudeProvider(
            api_key="sk-ant-...",
            model="claude-sonnet-4-20250514"
        )
        ```
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        base_url: Optional[str] = None
    ) -> None:
        """初始化 Claude 提供商。

        Args:
            api_key: Anthropic API Key，用于身份验证。可以从 Anthropic 官网获取。
            model: 要使用的模型名称。支持的模型包括：
                - "claude-sonnet-4-20250514": Claude Sonnet 4（推荐）
                - "claude-opus-3-20240229": Claude Opus 3
                - "claude-3-5-sonnet-20241022": Claude 3.5 Sonnet
                默认值为 "claude-sonnet-4-20250514"。
            base_url: 自定义 API 基础 URL（可选）。用于兼容的 API 服务。

        Raises:
            ValueError: 如果 api_key 为空或无效。
        """
        if base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = Anthropic(api_key=api_key)
        self._model = model
    
    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。

        Returns:
            模型名称字符串，如 "claude-sonnet-4-20250514"。
        """
        return self._model
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用。

        Claude 模型支持工具使用（tool use）功能，相当于函数调用。

        Returns:
            True，因为 Claude 模型支持工具使用。
        """
        return True
    
    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ) -> LLMResponse:
        """发送聊天请求到 Anthropic Claude API。

        此方法将消息列表和可选的工具定义发送给 Claude API，并解析返回的
        回复。Claude API 使用 "tools" 参数而不是 "functions"，并且需要将
        system 消息单独提取出来。

        Args:
            messages: 消息列表，会被转换为 Claude API 格式。system 消息
                会被单独提取到 system 参数中。
            functions: 可选的函数定义列表。如果提供，会被转换为 Claude
                的 tools 格式。
            temperature: 温度参数，控制回复的随机性。默认值为 0.1。
            **kwargs: 其他 Claude API 参数，如 max_tokens 等。

        Returns:
            LLMResponse 对象，包含回复内容和可能的函数调用。
            对于 MiniMax 模型，额外包含 thinking 字段（Interleaved Thinking）。

        Raises:
            Exception: 如果 Claude API 调用失败。可能是网络错误、API 密钥
                无效、模型不存在等原因。

        Note:
            - Claude API 要求 system 消息单独传递，不能放在 messages 中。
            - Claude 使用 "tools" 参数，格式与 OpenAI 略有不同。
            - Claude 返回的 content 是列表，包含 text、thinking 和 tool_use 块。
            - tool_use 块中的 input 已经是字典，不需要 JSON 解析。
            - MiniMax 模型支持 thinking 块（交错思维链），展示模型的推理过程。
        """
        try:
            # Claude API 要求 system 消息单独提取，不能放在 messages 中
            system_messages: List[str] = [
                msg.content for msg in messages if msg.role == "system"
            ]
            system_text: Optional[str] = (
                "\n".join(system_messages) if system_messages else None
            )
            
            # 提取非 system 消息
            claude_messages: List[Dict[str, Any]] = []
            for msg in messages:
                if msg.role == "system":
                    continue
                # 保持消息的完整结构（支持列表形式的 content）
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # 准备请求参数
            request_params: Dict[str, Any] = {
                "model": self._model,
                "max_tokens": kwargs.get("max_tokens", 2048),
                "temperature": temperature,
                "messages": claude_messages,
                **{k: v for k, v in kwargs.items() if k != "max_tokens"}
            }
            
            # 如果有 system 消息，单独传递
            if system_text:
                request_params["system"] = system_text
            
            # 如果提供了函数定义，转换为 Claude 的 tools 格式
            if functions:
                # Claude 使用 tools 参数，需要将 parameters 转换为 input_schema
                claude_tools = []
                for func in functions:
                    tool = {
                        "name": func.get("name"),
                        "description": func.get("description")
                    }
                    # Claude 使用 input_schema 而不是 parameters
                    if "parameters" in func:
                        tool["input_schema"] = func["parameters"]
                    elif "input_schema" in func:
                        tool["input_schema"] = func["input_schema"]
                    claude_tools.append(tool)
                request_params["tools"] = claude_tools
            
            # 发送请求到 Claude API
            response = self.client.messages.create(**request_params)
            
            # 解析响应：Claude 返回的 content 是列表，包含不同类型的块
            content_text: str = ""
            thinking_text: str = ""  # MiniMax 特有的 thinking 内容
            function_calls: Optional[List[FunctionCall]] = None
            
            for content_block in response.content:
                if content_block.type == "text":
                    # 文本块，累积到 content_text
                    content_text += content_block.text
                elif content_block.type == "thinking":
                    # MiniMax 特有：思考块（Interleaved Thinking）
                    thinking_text += content_block.thinking
                elif content_block.type == "tool_use":
                    # 工具使用块，转换为 FunctionCall
                    if function_calls is None:
                        function_calls = []
                    # Claude 的 input 已经是字典，不需要 JSON 解析
                    function_calls.append(FunctionCall(
                        name=content_block.name,
                        arguments=content_block.input
                    ))
            
            # 创建响应对象
            llm_response = LLMResponse(
                content=content_text,
                function_calls=function_calls,
                finish_reason=response.stop_reason
            )
            
            # 如果有 thinking 内容，添加到元数据中
            if thinking_text:
                llm_response.metadata = llm_response.metadata or {}
                llm_response.metadata["thinking"] = thinking_text
                logger.debug(f"Captured thinking content: {thinking_text[:100]}...")
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise

