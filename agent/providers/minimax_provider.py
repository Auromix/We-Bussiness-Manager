"""MiniMax 提供商实现。

本模块实现了 MiniMax 系列模型的提供商，通过 Anthropic SDK 兼容接口
调用 MiniMax 模型（如 MiniMax-M2.5）。

MiniMax 模型特点：
- 支持 Interleaved Thinking（交错思维链）
- 优秀的工具使用能力
- 支持长上下文（204,800 tokens）
- 在 Code & Agent Benchmark 上达到 SOTA 水平
"""
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from loguru import logger

from agent.providers.base import LLMProvider, LLMMessage, LLMResponse, FunctionCall


class MiniMaxProvider(LLMProvider):
    """MiniMax 模型提供商（通过 Anthropic SDK 兼容接口）。

    此提供商支持所有 MiniMax 系列模型，包括 MiniMax-M2.5、MiniMax-M2.5-highspeed、
    MiniMax-M2.1 等。

    Attributes:
        client: Anthropic 客户端实例，用于发送 API 请求。
        _model: 当前使用的模型名称。
        _tool_use_id_map: 跟踪函数名到 tool_use_id 的映射，用于转换 function 消息。

    Example:
        ```python
        provider = MiniMaxProvider(
            api_key="sk-api-...",
            model="MiniMax-M2.5"
        )
        ```
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "MiniMax-M2.5",
        base_url: Optional[str] = None
    ) -> None:
        """初始化 MiniMax 提供商。

        Args:
            api_key: MiniMax API Key，用于身份验证。
            model: 要使用的模型名称。支持的模型包括：
                - "MiniMax-M2.5": 顶尖性能与极致性价比（推荐）
                - "MiniMax-M2.5-highspeed": M2.5 极速版（约 100 TPS）
                - "MiniMax-M2.1": 强大多语言编程能力
                - "MiniMax-M2.1-highspeed": M2.1 极速版
                - "MiniMax-M2": 专为高效编码与 Agent 工作流而生
                默认值为 "MiniMax-M2.5"。
            base_url: API 基础 URL。默认为 MiniMax Anthropic 兼容接口。
                国内用户: https://api.minimaxi.com/anthropic
                国际用户: https://api.minimax.io/anthropic

        Raises:
            ValueError: 如果 api_key 为空或无效。
        """
        if not base_url:
            base_url = "https://api.minimaxi.com/anthropic"
        
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self._model = model
        self._tool_use_queue: List[tuple] = []  # 保存 (function_name, tool_use_id) 的队列
        self._response_cache: Dict[str, List[Any]] = {}  # 缓存响应文本到完整内容块的映射
        self._last_tool_response: Optional[List[Any]] = None  # 存储最后一次包含工具调用的完整响应
        logger.info(f"Initialized MiniMax provider with model: {model}, base_url: {base_url}")
    
    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称。

        Returns:
            模型名称字符串，如 "MiniMax-M2.5"。
        """
        return self._model
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用。

        MiniMax 模型支持工具使用（tool use）功能，并具备优秀的
        Interleaved Thinking 能力。

        Returns:
            True，因为 MiniMax 模型支持工具使用。
        """
        return True
    
    async def chat(
        self,
        messages: List[LLMMessage],
        functions: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
        **kwargs: Any
    ) -> LLMResponse:
        """发送聊天请求到 MiniMax API。

        此方法将消息列表和可选的工具定义发送给 MiniMax API（通过 Anthropic
        兼容接口），并解析返回的回复。MiniMax 模型支持 Interleaved Thinking，
        能在每轮工具调用前进行思考并决策下一步行动。

        重要提示：
        - MiniMax 模型支持 thinking 块（Interleaved Thinking），展示模型的推理过程
        - 在多轮对话中，必须保留完整的 assistant 消息（包括 thinking 内容）
        - 这样才能保持思维链的连续性，发挥模型的最佳性能

        Args:
            messages: 消息列表，会被转换为 Anthropic API 格式。system 消息
                会被单独提取到 system 参数中。
            functions: 可选的函数定义列表。如果提供，会被转换为 tools 格式。
            temperature: 温度参数，控制回复的随机性。默认值为 0.1。
            **kwargs: 其他 API 参数，如 max_tokens 等。

        Returns:
            LLMResponse 对象，包含回复内容和可能的函数调用。
            对于 MiniMax 模型，metadata 中包含 thinking 字段（如果有）。

        Raises:
            Exception: 如果 API 调用失败。

        Note:
            - MiniMax API 使用 Anthropic 兼容格式
            - system 消息需要单独传递，不能放在 messages 中
            - content 是列表，包含 thinking、text 和 tool_use 块
            - thinking 块展示模型的推理过程（Interleaved Thinking）
            - tool_use 块中的 input 已经是字典，不需要 JSON 解析
        """
        try:
            # 每次调用开始时清空队列，避免旧的 tool_use_id 干扰
            self._tool_use_queue = []
            
            # 提取 system 消息（MiniMax API 要求单独传递）
            system_messages: List[str] = [
                msg.content for msg in messages if msg.role == "system"
            ]
            system_text: Optional[str] = (
                "\n".join(system_messages) if system_messages else None
            )
            
            # 提取非 system 消息，转换为 MiniMax API 格式
            api_messages: List[Dict[str, Any]] = []
            pending_tool_results: List[Dict[str, Any]] = []  # 缓存待处理的 tool_result
            last_assistant_index = -1  # 记录最后一个 assistant 消息的索引
            
            for idx, msg in enumerate(messages):
                if msg.role == "system":
                    continue
                
                # 处理 "function" role: 转换为 tool_result 格式
                # MiniMax (Anthropic 兼容) 不支持 "function" role
                # 需要将其转换为 user role + tool_result content
                if msg.role == "function":
                    # 从队列中查找匹配的 tool_use_id
                    tool_use_id = None
                    logger.debug(f"Looking for tool_use_id for function {msg.name}, queue: {self._tool_use_queue}")
                    for i, (func_name, use_id) in enumerate(self._tool_use_queue):
                        if func_name == msg.name:
                            tool_use_id = use_id
                            # 从队列中移除已使用的项
                            self._tool_use_queue.pop(i)
                            logger.debug(f"Found tool_use_id {use_id} for function {msg.name}")
                            break
                    
                    # 如果队列中没找到，尝试从 _last_tool_response 中提取
                    if not tool_use_id and self._last_tool_response:
                        logger.debug(f"Queue empty, trying to extract from _last_tool_response (has {len(self._last_tool_response)} blocks)")
                        for block in self._last_tool_response:
                            logger.debug(f"Checking block: type={getattr(block, 'type', None)}, name={getattr(block, 'name', None)}")
                            if hasattr(block, 'type') and block.type == 'tool_use' and block.name == msg.name:
                                tool_use_id = block.id
                                logger.debug(f"Extracted tool_use_id {tool_use_id} from _last_tool_response for function {msg.name}")
                                break
                    else:
                        if not tool_use_id:
                            logger.debug(f"_last_tool_response is {self._last_tool_response}")
                    
                    if not tool_use_id:
                        # 如果还是找不到，使用函数名作为 id（fallback）
                        tool_use_id = f"call_{msg.name}"
                        logger.warning(f"Could not find tool_use_id for function {msg.name}, using fallback {tool_use_id}")
                    
                    tool_result = {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": msg.content
                    }
                    pending_tool_results.append(tool_result)
                    continue
                
                # 如果有待处理的 tool_results，先添加一个 user 消息包含它们
                if pending_tool_results:
                    api_messages.append({
                        "role": "user",
                        "content": pending_tool_results
                    })
                    pending_tool_results = []
                
                # 处理 assistant 消息：
                # 检查是否有缓存的完整响应（根据文本内容匹配）
                if msg.role == "assistant":
                    # 检查下一个消息是否是 function 调用结果
                    # 如果是，说明这个 assistant 消息触发了工具调用，需要使用缓存的完整内容
                    has_following_function = False
                    for next_msg in messages[idx+1:]:
                        if next_msg.role == "function":
                            has_following_function = True
                            break
                        elif next_msg.role in ["user", "assistant"]:
                            break
                    
                    if has_following_function:
                        # 优先使用 _response_cache 中的缓存
                        cached_content = self._response_cache.get(msg.content)
                        
                        # 如果缓存中没有，尝试使用 _last_tool_response
                        if not cached_content and self._last_tool_response:
                            cached_content = self._last_tool_response
                            logger.debug(f"Using _last_tool_response as cached content")
                        
                        if cached_content:
                            # 从缓存内容中提取 tool_use_id 并填充队列
                            for block in cached_content:
                                if hasattr(block, 'type') and block.type == 'tool_use':
                                    self._tool_use_queue.append((block.name, block.id))
                                    logger.debug(f"Extracted tool_use from cache: {block.name} -> {block.id}")
                            
                            message_dict = {
                                "role": "assistant",
                                "content": cached_content
                            }
                            logger.debug(f"Using cached response content for assistant message with tool calls ({len(cached_content)} blocks)")
                        else:
                            # 没有缓存，使用纯文本
                            logger.warning(f"No cached response found for assistant message with following function calls")
                            message_dict = {
                                "role": msg.role,
                                "content": msg.content
                            }
                    else:
                        # 普通 assistant 消息
                        message_dict = {
                            "role": msg.role,
                            "content": msg.content
                        }
                else:
                    # 保持消息的完整结构（支持列表形式的 content）
                    message_dict = {
                        "role": msg.role,
                        "content": msg.content
                    }
                
                # 如果有 name 字段，添加它
                if msg.name:
                    message_dict["name"] = msg.name
                
                api_messages.append(message_dict)
                
                if msg.role == "assistant":
                    last_assistant_index = len(api_messages) - 1
            
            # 处理剩余的 tool_results
            if pending_tool_results:
                api_messages.append({
                    "role": "user",
                    "content": pending_tool_results
                })
            
            # 准备请求参数
            request_params: Dict[str, Any] = {
                "model": self._model,
                "max_tokens": kwargs.get("max_tokens", 4096),  # MiniMax 支持长输出
                "temperature": temperature,
                "messages": api_messages,
                **{k: v for k, v in kwargs.items() if k != "max_tokens"}
            }
            
            # 如果有 system 消息，单独传递
            if system_text:
                request_params["system"] = system_text
            
            # 如果提供了函数定义，转换为 tools 格式
            if functions:
                tools = []
                for func in functions:
                    tool = {
                        "name": func.get("name"),
                        "description": func.get("description")
                    }
                    # 使用 input_schema 而不是 parameters
                    if "parameters" in func:
                        tool["input_schema"] = func["parameters"]
                    elif "input_schema" in func:
                        tool["input_schema"] = func["input_schema"]
                    tools.append(tool)
                request_params["tools"] = tools
                logger.debug(f"Converted {len(tools)} functions to tools format")
            
            # 发送请求到 MiniMax API
            logger.debug(f"Sending request to MiniMax API with {len(api_messages)} messages")
            
            # 调试：打印消息结构
            for i, msg in enumerate(api_messages):
                if isinstance(msg['content'], list):
                    logger.debug(f"Message {i}: role={msg['role']}, content blocks={[b.get('type', type(b).__name__) if isinstance(b, dict) else type(b).__name__ for b in msg['content']]}")
                else:
                    logger.debug(f"Message {i}: role={msg['role']}, content (text)")
            
            response = self.client.messages.create(**request_params)
            
            # 解析响应：MiniMax 返回的 content 是列表，包含不同类型的块
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
                    logger.debug(f"Captured thinking block: {content_block.thinking[:100]}...")
                elif content_block.type == "tool_use":
                    # 工具使用块，转换为 FunctionCall
                    if function_calls is None:
                        function_calls = []
                    # input 已经是字典，不需要 JSON 解析
                    function_calls.append(FunctionCall(
                        name=content_block.name,
                        arguments=content_block.input
                    ))
                    # 保存到队列，用于后续的 function 消息转换
                    # 使用队列而不是映射，以支持同一个函数的多次调用
                    self._tool_use_queue.append((content_block.name, content_block.id))
                    logger.debug(f"Captured tool use: {content_block.name} (id: {content_block.id})")
            
            # 缓存完整的响应内容（如果包含 tool_use）
            # 使用文本内容作为键，以便后续根据文本匹配缓存
            if function_calls:
                self._response_cache[content_text.strip()] = list(response.content)
                self._last_tool_response = list(response.content)  # 同时保存到 last_tool_response
                logger.debug(f"Cached response with {len(function_calls)} tool calls")
            
            # 创建响应对象
            llm_response = LLMResponse(
                content=content_text.strip(),
                function_calls=function_calls,
                finish_reason=response.stop_reason
            )
            
            # 如果有 thinking 内容，添加到元数据中
            if thinking_text:
                llm_response.metadata = llm_response.metadata or {}
                llm_response.metadata["thinking"] = thinking_text
                logger.info(f"Response includes thinking content ({len(thinking_text)} chars)")
            
            # 记录 token 使用情况
            if hasattr(response, 'usage'):
                usage = response.usage
                llm_response.metadata = llm_response.metadata or {}
                llm_response.metadata["usage"] = {
                    "input_tokens": getattr(usage, 'input_tokens', 0),
                    "output_tokens": getattr(usage, 'output_tokens', 0),
                    "cache_creation_input_tokens": getattr(usage, 'cache_creation_input_tokens', 0),
                    "cache_read_input_tokens": getattr(usage, 'cache_read_input_tokens', 0),
                }
                logger.debug(f"Token usage: {llm_response.metadata['usage']}")
            
            return llm_response
            
        except Exception as e:
            logger.error(f"MiniMax API error: {e}")
            raise

