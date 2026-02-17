# Agent 模块快速开始指南

本指南帮助您在 5 分钟内快速上手 `agent/` 模块。

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 基本使用（3 步上手）

### 步骤 1：创建 LLM Provider

```python
from agent import create_provider

# 创建 OpenAI Provider（需要设置 OPENAI_API_KEY 环境变量）
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

# 或者使用 Claude
provider = create_provider("claude", api_key="sk-ant-...")

# 或者使用 MiniMax（国内可用）
provider = create_provider("minimax", api_key="sk-api-...", model="MiniMax-M2.5")
```

### 步骤 2：创建 Agent 并对话

```python
from agent import Agent

# 创建 Agent
agent = Agent(provider, system_prompt="你是一个友好的助手")

# 进行对话
response = await agent.chat("你好")
print(response["content"])
```

### 步骤 3：注册函数并调用

```python
from agent import FunctionRegistry
from agent.functions.discovery import agent_callable, auto_discover_and_register

# 定义函数
@agent_callable(description="获取天气信息")
def get_weather(city: str) -> dict:
    return {"city": city, "temperature": 25, "condition": "晴天"}

# 创建注册表并注册函数
registry = FunctionRegistry()
auto_discover_and_register(registry, [get_weather])

# 创建带函数调用的 Agent
agent = Agent(provider, registry, system_prompt="你是天气助手")

# Agent 会自动调用函数
response = await agent.chat("北京今天天气怎么样？")
print(response["content"])
```

## 3. 完整示例

运行以下代码，体验完整流程：

```python
"""快速开始示例"""
import asyncio
import os
from agent import Agent, create_provider, FunctionRegistry
from agent.functions.discovery import agent_callable, auto_discover_and_register

# === 1. 创建 Provider ===
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("请设置 OPENAI_API_KEY 环境变量")
    exit(1)

provider = create_provider("openai", api_key=api_key, model="gpt-4o-mini")
print("✅ Provider 已创建")

# === 2. 基础对话 ===
agent = Agent(provider, system_prompt="你是一个友好的助手")
print("\n用户: 你好")
response = await agent.chat("你好")
print(f"助手: {response['content']}")

# === 3. 注册函数 ===
@agent_callable(description="计算两个数字的和")
def add(a: float, b: float) -> dict:
    return {"result": a + b}

registry = FunctionRegistry()
auto_discover_and_register(registry, [add])

agent_with_func = Agent(provider, registry, system_prompt="你是计算助手")
print("\n用户: 计算 123 + 456")
response = await agent_with_func.chat("计算 123 + 456")
print(f"助手: {response['content']}")
print(f"调用了 {len(response['function_calls'])} 个函数")

print("\n✅ 快速开始示例完成！")
```

保存为 `quickstart_demo.py` 并运行：

```bash
python quickstart_demo.py
```

## 4. 常用操作速查

### 创建不同的 Provider

```python
# OpenAI
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

# Claude
provider = create_provider("claude", api_key="sk-ant-...")

# MiniMax
provider = create_provider("minimax", api_key="sk-api-...", model="MiniMax-M2.5")

# 开源模型（兼容 OpenAI API）
provider = create_provider(
    "open_source",
    base_url="http://localhost:8000/v1",
    model="qwen"
)
```

### 注册函数

```python
# 方式1：装饰器
@agent_callable(description="我的函数")
def my_func(x: str) -> dict:
    return {"result": x}

# 方式2：手动注册
registry = FunctionRegistry()
registry.register("my_func", "我的函数", my_func)

# 方式3：自动发现
auto_discover_and_register(registry, [my_func])
```

### 多轮对话

```python
agent = Agent(provider, system_prompt="你是助手")

# 第一轮
response = await agent.chat("2 + 2 等于多少？")
print(response["content"])

# 第二轮（利用上下文）
response = await agent.chat("那 3 + 3 呢？")
print(response["content"])

# 第三轮（继续利用上下文）
response = await agent.chat("把这两个结果加起来")
print(response["content"])
```

### 清空对话历史

```python
agent.clear_history()  # 保留系统提示词
```

### 控制迭代次数

```python
# 限制最多 5 轮迭代
response = await agent.chat("复杂查询", max_iterations=5)
```

### 查看函数调用记录

```python
response = await agent.chat("查询信息")
print(f"迭代次数: {response['iterations']}")
print(f"函数调用次数: {len(response['function_calls'])}")
for func_call in response['function_calls']:
    print(f"  - {func_call['name']}({func_call['arguments']})")
```

## 5. 下一步

- 📖 **深入学习**：查看 `README.md` 了解所有功能
- 💼 **Provider 示例**：运行 `provider_example.py` 了解不同提供商
- 🔧 **函数调用**：运行 `function_calling_example.py` 学习函数调用
- 📚 **架构设计**：阅读 `design/agent.md` 了解设计原理

## 6. 常见问题

### Q: 如何设置 API Key？

A: 使用环境变量或直接传入：

```python
# 方式1：环境变量
import os
api_key = os.getenv("OPENAI_API_KEY")

# 方式2：直接传入
provider = create_provider("openai", api_key="sk-...")
```

### Q: 支持哪些模型？

A: 支持所有实现 `LLMProvider` 接口的模型：
- OpenAI GPT 系列
- Anthropic Claude 系列
- MiniMax 系列
- 兼容 OpenAI API 的开源模型

### Q: 如何切换模型？

A: 只需更换 Provider，Agent 代码无需修改：

```python
# 从 OpenAI 切换到 Claude
provider = create_provider("claude", api_key="sk-ant-...")
agent = Agent(provider)  # 其他代码不变
```

### Q: 函数调用失败怎么办？

A: Agent 会自动捕获错误并返回给 LLM，LLM 可能会重试或使用替代方案。确保函数有适当的错误处理。

### Q: 如何查看对话历史？

A: 访问 `agent.conversation_history`：

```python
for msg in agent.conversation_history:
    print(f"{msg.role}: {msg.content[:50]}")
```

---

**🎉 恭喜！您已经掌握了 Agent 模块的基本用法。现在可以开始构建您的应用了！**

