"""开源模型提供商实现 - 支持兼容 OpenAI API 格式的开源模型。

本模块实现了开源模型的提供商，支持通过 HTTP API 调用兼容 OpenAI API
格式的模型服务。可以用于接入通过 vLLM、Ollama、LocalAI 等部署的模型。
"""
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class OpenSourceProvider(LLMProvider):
    """开源模型提供商 - 支持兼容 OpenAI API 格式的模型。

    此提供商支持通过 HTTP API 接入的开源模型，只要模型服务兼容 OpenAI
    API 格式即可。常见的部署方式包括：
    - vLLM: 高性能 LLM 推理服务
    - Ollama: 本地模型运行工具
    - LocalAI: OpenAI 兼容的本地 API 服务
    - 其他兼容 OpenAI API 格式的服务

    支持的模型包括但不限于：
    - Qwen（通义千问）
    - ChatGLM
    - Llama 系列
    - Mistral
    - 其他兼容 OpenAI API 格式的模型

    Attributes:
        base_url: API 基础 URL，不包含路径部分。
        _model: 当前使用的模型名称。
        api_key: 可选的 API Key，用于身份验证。
        timeout: HTTP 请求超时时间（秒）。

    Example:
        ```python
        # 使用本地部署的 vLLM 服务
        provider = OpenSourceProvider(
            base_url="http://localhost:8000/v1",
            model="qwen",
            timeout=120.0
        )

        # 使用需要认证的服务
        provider = OpenSourceProvider(
            base_url="https://api.example.com/v1",
            model="custom-model",
            api_key="sk-...",
            timeout=60.0
        )
        ```
    """
    
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        """初始化开源模型提供商。

        Args:
            base_url: API 基础 URL，应该包含协议和主机，但不包含路径。
                例如："http://localhost:8000/v1" 或 "https://api.example.com/v1"。
                如果 URL 以 "/" 结尾，会自动去除。
            model: 要使用的模型名称。具体支持的模型取决于部署的服务。
            api_key: 可选的 API Key，如果服务需要身份验证则提供。
                会在请求头中添加 "Authorization: Bearer {api_key}"。
            timeout: HTTP 请求的超时时间（秒）。默认值为 60.0 秒。
                如果模型响应较慢，可以适当增加此值。

        Raises:
            ValueError: 如果 base_url 格式不正确。
        """
        self.base_url = base_url.rstrip("/")
        self._model = model
        self.api_key = api_key
        self.timeout = timeout
    
    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。

        Returns:
            模型名称字符串，如 "qwen"、"llama-2" 等。
        """
        return self._model
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用。

        大多数通过 OpenAI 兼容接口部署的开源模型都支持函数调用功能。
        如果模型不支持，会在实际调用时返回错误。

        Returns:
            True，假设模型支持函数调用。如果模型不支持，会在调用时失败。
        """
        return True
    
    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ) -> LLMResponse:
        """发送聊天请求到开源模型 API。

        此方法通过 HTTP POST 请求调用兼容 OpenAI API 格式的模型服务。
        请求格式完全遵循 OpenAI API 规范，因此可以与任何兼容的服务交互。

        Args:
            messages: 消息列表，会被转换为 OpenAI API 格式。
            functions: 可选的函数定义列表。如果提供，会被转换为 OpenAI
                的 tools 格式。
            temperature: 温度参数，控制回复的随机性。默认值为 0.1。
            **kwargs: 其他 API 参数，如 max_tokens、top_p 等。

        Returns:
            LLMResponse 对象，包含回复内容和可能的函数调用。

        Raises:
            httpx.HTTPError: 如果 HTTP 请求失败（网络错误、超时等）。
            httpx.HTTPStatusError: 如果服务器返回错误状态码。
            Exception: 如果响应格式不正确或其他错误。

        Note:
            - 请求发送到 {base_url}/chat/completions 端点。
            - 如果提供了 api_key，会在请求头中添加 Authorization。
            - 响应格式应该与 OpenAI API 完全一致。
            - tool_calls 中的 arguments 是 JSON 字符串，需要解析。
        """
        try:
            # 转换消息格式为 OpenAI API 格式
            api_messages: List[Dict[str, Any]] = []
            for msg in messages:
                message_dict: Dict[str, Any] = {
                    "role": msg.role,
                    "content": msg.content
                }
                # 如果消息有函数名（function 类型消息），添加到字典中
                if msg.name:
                    message_dict["name"] = msg.name
                api_messages.append(message_dict)
            
            # 准备请求体（遵循 OpenAI API 格式）
            request_body: Dict[str, Any] = {
                "model": self._model,
                "messages": api_messages,
                "temperature": temperature,
                **kwargs
            }
            
            # 如果提供了函数定义，转换为 OpenAI 的 tools 格式
            if functions:
                request_body["tools"] = [
                    {"type": "function", "function": func} for func in functions
                ]
                # tool_choice 设置为 "auto"，让模型决定是否调用函数
                request_body["tool_choice"] = "auto"
            
            # 准备请求头
            headers: Dict[str, str] = {
                "Content-Type": "application/json"
            }
            # 如果提供了 API Key，添加到请求头
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # 发送 HTTP POST 请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=request_body,
                    headers=headers
                )
                # 检查 HTTP 状态码，如果不是 2xx 会抛出异常
                response.raise_for_status()
                data: Dict[str, Any] = response.json()
            
            # 解析响应（遵循 OpenAI API 响应格式）
            choice: Dict[str, Any] = data["choices"][0]
            message: Dict[str, Any] = choice["message"]
            
            # 提取函数调用（如果有）
            function_calls: Optional[List[FunctionCall]] = None
            if "tool_calls" in message and message["tool_calls"]:
                function_calls = []
                for tool_call in message["tool_calls"]:
                    if tool_call.get("type") == "function":
                        import json
                        func: Dict[str, Any] = tool_call["function"]
                        try:
                            # arguments 是 JSON 字符串，需要解析
                            arguments: Dict[str, Any] = json.loads(
                                func.get("arguments", "{}")
                            )
                            function_calls.append(FunctionCall(
                                name=func.get("name", ""),
                                arguments=arguments
                            ))
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Failed to parse function arguments: {e}, "
                                f"raw: {func.get('arguments', '')}"
                            )
            
            return LLMResponse(
                content=message.get("content", "") or "",
                function_calls=function_calls,
                finish_reason=choice.get("finish_reason")
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling open source model: {e}")
            raise
        except Exception as e:
            logger.error(f"Open source model API error: {e}")
            raise

