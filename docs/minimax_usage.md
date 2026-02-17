# MiniMax Provider 使用指南

本文档介绍如何使用 MiniMax 模型提供商，包括基本配置、API 调用和最佳实践。

## 目录

- [简介](#简介)
- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [使用示例](#使用示例)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 简介

MiniMax Provider 通过 Anthropic 兼容接口支持 MiniMax 系列模型，包括：

- **MiniMax-M2.5**: 顶尖性能与极致性价比，轻松驾驭复杂任务（推荐）
- **MiniMax-M2.5-highspeed**: M2.5 极速版，输出速度约 100 TPS
- **MiniMax-M2.1**: 强大多语言编程能力
- **MiniMax-M2.1-highspeed**: M2.1 极速版
- **MiniMax-M2**: 专为高效编码与 Agent 工作流而生

### 核心特性

1. **Interleaved Thinking（交错思维链）**: 模型在每轮工具调用前会进行思考，展示推理过程
2. **优秀的工具使用能力**: 在 Code & Agent Benchmark 上达到 SOTA 水平
3. **长上下文支持**: 最高支持 204,800 tokens
4. **自动 Prompt 缓存**: 降低成本和延迟

## 快速开始

### 1. 安装依赖

```bash
pip install anthropic loguru
```

### 2. 设置环境变量

```bash
export MINIMAX_API_KEY="sk-api-..."
export MINIMAX_BASE_URL="https://api.minimaxi.com/anthropic"  # 可选，国内用户默认
export MINIMAX_MODEL="MiniMax-M2.5"  # 可选，默认 M2.5
```

### 3. 基本使用

```python
from agent import Agent, create_provider

# 创建 MiniMax Provider
provider = create_provider(
    "minimax",
    api_key="sk-api-...",
    model="MiniMax-M2.5"
)

# 创建 Agent
agent = Agent(provider, system_prompt="你是一个友好的助手。")

# 发送消息
response = await agent.chat("你好，请介绍一下你自己")
print(response['content'])
```

## 功能特性

### 1. 基础对话

```python
import asyncio
from agent import Agent, create_provider

async def basic_chat():
    provider = create_provider(
        "minimax",
        api_key="sk-api-...",
        model="MiniMax-M2.5"
    )
    
    agent = Agent(provider, system_prompt="你是一个友好的助手。")
    response = await agent.chat("Python 如何定义函数？")
    
    print(f"回复: {response['content']}")
    
    # 检查 thinking 内容
    if 'metadata' in response and 'thinking' in response['metadata']:
        print(f"思考过程: {response['metadata']['thinking']}")

asyncio.run(basic_chat())
```

### 2. 函数调用（Tool Use）

MiniMax 模型具备优秀的工具使用能力，支持 Interleaved Thinking。

```python
import asyncio
from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from agent.functions.discovery import agent_callable

# 定义工具函数
@agent_callable(description="获取指定城市的天气信息")
def get_weather(city: str) -> dict:
    """获取天气信息（模拟）"""
    return {
        "city": city,
        "temperature": 22,
        "condition": "晴天",
        "humidity": 55
    }

async def function_calling():
    provider = create_provider(
        "minimax",
        api_key="sk-api-...",
        model="MiniMax-M2.5"
    )
    
    # 注册函数
    registry = FunctionRegistry()
    registry.register("get_weather", "获取城市天气", get_weather)
    
    # 创建 Agent
    agent = Agent(
        provider,
        function_registry=registry,
        system_prompt="你是一个助手。当需要实时数据时，使用提供的工具。"
    )
    
    # 发送消息
    response = await agent.chat("北京今天天气怎么样？")
    
    print(f"回复: {response['content']}")
    print(f"调用的函数: {[fc['name'] for fc in response['function_calls']]}")
    
    # 查看 Interleaved Thinking
    if 'metadata' in response and 'thinking' in response['metadata']:
        print(f"\n💭 模型的思考过程:")
        print(response['metadata']['thinking'])

asyncio.run(function_calling())
```

### 3. 多轮对话

```python
import asyncio
from agent import Agent, create_provider

async def multi_turn():
    provider = create_provider(
        "minimax",
        api_key="sk-api-...",
        model="MiniMax-M2.5"
    )
    
    agent = Agent(provider, system_prompt="你是一个友好的助手。")
    
    # 第一轮
    response1 = await agent.chat("我叫张三，是一名软件工程师")
    print(f"第 1 轮: {response1['content']}")
    
    # 第二轮 - 测试记忆
    response2 = await agent.chat("我叫什么名字？")
    print(f"第 2 轮: {response2['content']}")
    
    # 第三轮
    response3 = await agent.chat("我的职业是什么？")
    print(f"第 3 轮: {response3['content']}")

asyncio.run(multi_turn())
```

### 4. Token 使用统计

```python
response = await agent.chat("你好")

if 'metadata' in response and 'usage' in response['metadata']:
    usage = response['metadata']['usage']
    print(f"输入 tokens: {usage['input_tokens']}")
    print(f"输出 tokens: {usage['output_tokens']}")
    
    # Prompt 缓存信息
    if usage['cache_read_input_tokens'] > 0:
        print(f"缓存命中 tokens: {usage['cache_read_input_tokens']}")
```

## 最佳实践

### 1. Interleaved Thinking

MiniMax 模型支持 Interleaved Thinking（交错思维链），在工具调用前会进行思考。为了充分发挥这一特性：

- ✅ **保留完整的对话历史**: 包括 thinking 内容
- ✅ **使用合适的 system prompt**: 引导模型进行推理
- ✅ **提供清晰的工具描述**: 帮助模型理解何时使用工具

```python
# 好的实践
agent = Agent(
    provider,
    system_prompt="你是一个助手。当需要实时数据或计算时，使用提供的工具。仔细思考是否需要调用工具。"
)
```

### 2. 工具定义

提供清晰、准确的工具描述和参数说明：

```python
@agent_callable(
    description="获取指定城市的天气信息。输入城市名称，返回温度、天气状况和湿度。"
)
def get_weather(city: str) -> dict:
    """
    Args:
        city: 城市名称，如 "北京"、"上海"
    
    Returns:
        包含天气信息的字典
    """
    # 实现...
```

### 3. Prompt 缓存

MiniMax 支持自动 Prompt 缓存，无需额外配置：

- 将静态内容（system prompt、工具定义）放在 prompt 开头
- 动态内容（用户输入）放在末尾
- 缓存生命周期为 5 分钟，自动刷新

### 4. 错误处理

```python
try:
    response = await agent.chat("你的问题")
    print(response['content'])
except Exception as e:
    logger.error(f"API 调用失败: {e}")
    # 处理错误
```

### 5. 性能优化

- 使用 `MiniMax-M2.5-highspeed` 获得更快的响应速度（约 100 TPS）
- 合理设置 `max_tokens` 参数
- 利用缓存减少重复计算

## 常见问题

### Q1: 如何选择模型？

- **MiniMax-M2.5**: 平衡性能和成本，适合大多数场景（推荐）
- **MiniMax-M2.5-highspeed**: 需要快速响应的场景
- **MiniMax-M2.1**: 多语言编程任务
- **MiniMax-M2**: 编码和 Agent 工作流

### Q2: thinking 内容没有显示？

thinking 内容存储在 `response['metadata']['thinking']` 中。如果没有，可能是：

- 模型判断不需要额外思考
- 温度设置过高（建议使用 0.1-0.7）

### Q3: 函数调用失败？

确保：

- 函数描述清晰准确
- 参数类型定义正确
- system prompt 引导模型使用工具

### Q4: 如何查看 API 使用情况？

检查 `response['metadata']['usage']`:

```python
usage = response['metadata']['usage']
print(f"输入: {usage['input_tokens']}")
print(f"输出: {usage['output_tokens']}")
print(f"缓存命中: {usage.get('cache_read_input_tokens', 0)}")
```

### Q5: 国际用户如何使用？

```python
provider = create_provider(
    "minimax",
    api_key="sk-api-...",
    model="MiniMax-M2.5",
    base_url="https://api.minimax.io/anthropic"  # 国际地址
)
```

## 更多资源

- [MiniMax 官方文档](https://platform.minimaxi.com/docs)
- [MiniMax M2.5 介绍](https://minimaxi.com/news/minimax-m25)
- [Anthropic API 文档](https://docs.anthropic.com)
- [测试示例](../tests/agent/test_minimax.py)

## 联系我们

如果遇到问题：

- 邮箱: Model@minimaxi.com
- GitHub: [MiniMax-AI/MiniMax-M2.5](https://github.com/MiniMax-AI/MiniMax-M2.5/issues)

