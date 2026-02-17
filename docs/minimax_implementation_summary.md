# MiniMax Provider 实现总结

## 完成时间
2026-02-17

## 实现内容

根据 MiniMax 官方文档，完整实现了 MiniMax 模型的 Provider，支持通过 Anthropic 兼容接口调用 MiniMax 系列模型。

## 主要文件

### 1. 核心实现
- **agent/providers/minimax_provider.py**: MiniMax Provider 实现
  - 支持所有 MiniMax 系列模型（M2.5、M2.5-highspeed、M2.1、M2.1-highspeed、M2）
  - 实现 Interleaved Thinking（交错思维链）支持
  - 自动处理 Prompt 缓存
  - 完整的工具调用（Tool Use）支持
  - 支持多个工具同时调用

### 2. 基础架构更新
- **agent/providers/base.py**: 
  - 更新 `LLMResponse` 类，添加 `metadata` 字段
  - 支持存储 thinking 内容和 token 使用统计

- **agent/providers/__init__.py**: 
  - 导出 `MiniMaxProvider`
  - 更新工厂函数 `create_provider` 支持 "minimax" 类型

### 3. 测试
- **tests/agent/test_minimax.py**: 完整的测试套件
  - 基础对话测试
  - 函数调用与 Interleaved Thinking 测试
  - 多轮对话与上下文记忆测试
  - 所有测试通过 ✅

### 4. 示例和文档
- **examples/minimax_example.py**: 详细的使用示例
  - 基础对话示例
  - 函数调用示例
  - 多轮对话示例
  - 复杂任务示例（多步骤推理）

- **docs/minimax_usage.md**: 完整的使用指南
  - 快速开始
  - 功能特性说明
  - 最佳实践
  - 常见问题

## 核心特性

### 1. Interleaved Thinking（交错思维链）
- 模型在每轮工具调用前会进行思考
- thinking 内容存储在 `response['metadata']['thinking']` 中
- 支持查看模型的推理过程

### 2. 工具调用（Tool Use）
- 完整的函数调用支持
- 支持同时调用多个工具
- 支持同一工具的多次调用
- 自动处理 tool_use_id 映射

### 3. 响应内容缓存
- 缓存包含 tool_use 的完整响应内容
- 确保多轮对话中 tool_result 能正确匹配 tool_use
- 支持复杂的多步骤任务

### 4. Prompt 缓存
- 自动支持 MiniMax 的 Prompt 缓存功能
- Token 使用统计包含缓存信息
- 缓存生命周期 5 分钟，自动刷新

## 技术挑战与解决方案

### 挑战 1: function role 不被支持
**问题**: MiniMax API（Anthropic 兼容）不支持 "function" role，需要使用 "user" role + tool_result

**解决方案**: 
- 在消息转换时，将 "function" 消息转换为 tool_result 格式
- 维护 tool_use_id 队列，确保 tool_result 能正确匹配 tool_use

### 挑战 2: 多个工具调用时 ID 冲突
**问题**: 当同一个函数被多次调用时，简单的映射会被覆盖

**解决方案**:
- 使用队列而不是字典存储 tool_use_id
- 按照调用顺序从队列中取出对应的 ID

### 挑战 3: 多轮对话中 tool_use 信息丢失
**问题**: Agent 只保存 assistant 消息的文本内容，导致后续请求中 tool_result 找不到对应的 tool_use

**解决方案**:
- 缓存包含 tool_use 的完整响应内容
- 使用文本内容作为键，建立文本到完整内容的映射
- 在构建消息时，根据文本匹配缓存并使用完整内容

### 挑战 4: 缓存内容的生命周期管理
**问题**: 需要正确管理缓存的使用和清理，避免旧的 tool_use_id 干扰新的请求

**解决方案**:
- 每次调用开始时清空 tool_use 队列
- 在使用缓存内容时重新填充队列
- 缓存所有包含 tool_use 的响应，而不仅仅是最后一个

## 测试结果

所有测试通过 ✅：

```
测试总结
============================================================
  基础对话: ✅ 通过
  函数调用与 Interleaved Thinking: ✅ 通过
  多轮对话与上下文记忆: ✅ 通过

总计: 3/3 通过

🎉 所有测试通过！MiniMax Provider 工作正常。
```

## 使用示例

### 基础使用
```python
from agent import Agent, create_provider

provider = create_provider(
    "minimax",
    api_key="sk-api-...",
    model="MiniMax-M2.5"
)

agent = Agent(provider, system_prompt="你是一个友好的助手。")
response = await agent.chat("你好")
print(response['content'])
```

### 函数调用
```python
from agent.functions.discovery import agent_callable

@agent_callable(description="获取城市天气")
def get_weather(city: str) -> dict:
    return {"city": city, "temperature": 22}

registry = FunctionRegistry()
registry.register("get_weather", "获取天气", get_weather)

agent = Agent(provider, function_registry=registry)
response = await agent.chat("北京天气怎么样？")
```

### 查看 Thinking
```python
response = await agent.chat("计算 15 + 27")

if 'metadata' in response and 'thinking' in response['metadata']:
    print(f"思考过程: {response['metadata']['thinking']}")
```

## 性能特点

- **输出速度**: MiniMax-M2.5 约 60 TPS，MiniMax-M2.5-highspeed 约 100 TPS
- **上下文长度**: 最高支持 204,800 tokens
- **Prompt 缓存**: 自动缓存，节省成本和延迟
- **Interleaved Thinking**: 展示模型推理过程，提高可解释性

## 相关资源

- [MiniMax 官方文档](https://platform.minimaxi.com/docs)
- [MiniMax M2.5 介绍](https://minimaxi.com/news/minimax-m25)
- [Anthropic API 文档](https://docs.anthropic.com)
- [使用指南](./minimax_usage.md)

## 联系方式

如有问题：
- 邮箱: Model@minimaxi.com
- GitHub: [MiniMax-AI/MiniMax-M2.5](https://github.com/MiniMax-AI/MiniMax-M2.5/issues)

