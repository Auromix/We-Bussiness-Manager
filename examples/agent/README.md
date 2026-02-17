# Agent 模块使用示例

本目录提供了 `agent/` 模块的完整使用示例，帮助您快速上手并独立使用 Agent 功能。

## 📚 目录结构

```
examples/agent/
├── README.md                    # 本文档
├── QUICKSTART.md                # 快速开始指南
├── basic_usage.py               # 基础使用示例
├── provider_example.py          # 不同 Provider 使用示例
├── function_calling_example.py  # 函数调用示例
└── advanced_example.py          # 高级用法示例
```

## 🚀 快速开始

如果您是第一次使用，建议按以下顺序学习：

1. **快速开始** → 阅读 `QUICKSTART.md`，5 分钟了解基本用法
2. **基础示例** → 运行 `basic_usage.py`，了解初始化和基本对话
3. **Provider 示例** → 运行 `provider_example.py`，了解不同 LLM 提供商的使用
4. **函数调用** → 运行 `function_calling_example.py`，学习如何注册和使用函数
5. **高级用法** → 运行 `advanced_example.py`，了解高级特性

## 📖 示例说明

### 1. 基础使用 (`basic_usage.py`)

展示最基本的操作：
- 创建 LLM Provider（OpenAI、Claude、MiniMax 等）
- 创建 Agent 实例
- 进行单轮和多轮对话
- 管理对话历史

**适用场景**：第一次使用，需要了解基本操作流程

### 2. Provider 示例 (`provider_example.py`)

展示不同 LLM 提供商的使用：
- **OpenAI Provider**：GPT 系列模型
- **Claude Provider**：Anthropic Claude 系列
- **MiniMax Provider**：MiniMax 系列（国内可用）
- **OpenSource Provider**：兼容 OpenAI API 的开源模型

**适用场景**：需要了解如何切换不同的 LLM 提供商

### 3. 函数调用示例 (`function_calling_example.py`)

展示函数调用的完整流程：
- **装饰器方式**：使用 `@agent_callable` 标记函数
- **手动注册**：直接注册函数到注册表
- **自动注册**：批量注册实例方法、类方法
- **多步骤调用**：Agent 自动处理函数调用链

**适用场景**：需要让 Agent 调用外部函数或服务

### 4. 高级用法示例 (`advanced_example.py`)

展示高级特性：
- 消息解析（从非结构化文本提取结构化数据）
- 自定义系统提示词
- 控制迭代次数
- 错误处理
- 与数据库模块集成

**适用场景**：需要深入了解 Agent 的高级功能

## 💡 核心概念

### Agent - 统一对话接口

`Agent` 是 Agent 模块的统一入口，提供简洁的对话接口：

```python
from agent import Agent, create_provider

# 创建 Provider
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

# 创建 Agent
agent = Agent(provider, system_prompt="你是一个友好的助手")

# 进行对话
response = await agent.chat("你好")
print(response["content"])
```

### Provider - 多模型透明切换

Agent 通过 `LLMProvider` 抽象接口支持多种模型，切换模型只需更换 Provider：

```python
# OpenAI
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

# Claude
provider = create_provider("claude", api_key="sk-ant-...")

# MiniMax（国内可用）
provider = create_provider("minimax", api_key="sk-api-...", model="MiniMax-M2.5")

# 开源模型（兼容 OpenAI API）
provider = create_provider("open_source", base_url="http://localhost:8000/v1", model="qwen")
```

### FunctionRegistry - 函数注册表

管理所有可被 Agent 调用的函数：

```python
from agent import FunctionRegistry
from agent.functions.discovery import agent_callable, auto_discover_and_register

# 方式1：使用装饰器
@agent_callable(description="获取天气信息")
def get_weather(city: str) -> dict:
    return {"city": city, "temp": 25}

# 方式2：手动注册
registry = FunctionRegistry()
registry.register("get_weather", "获取天气信息", get_weather)

# 方式3：自动发现并注册
auto_discover_and_register(registry, [get_weather])
```

### 函数调用流程

```
用户消息 → Agent.chat() → LLM Provider
                              ↓
                        是否包含函数调用？
                        /              \
                      是                否
                      ↓                  ↓
              执行函数调用          返回最终回复
                      ↓
              将结果返回给 LLM
                      ↓
              继续迭代（最多 max_iterations 次）
```

## 🔧 运行示例

### 前置条件

```bash
# 安装依赖
pip install -r requirements.txt
```

### 设置环境变量

根据您要使用的 Provider，设置相应的 API Key：

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# MiniMax
export MINIMAX_API_KEY="sk-api-..."

# 开源模型（可选）
export OPEN_SOURCE_BASE_URL="http://localhost:8000/v1"
export OPEN_SOURCE_MODEL="qwen"
export OPEN_SOURCE_API_KEY="optional-key"
```

### 运行单个示例

```bash
# 基础示例
python examples/agent/basic_usage.py

# Provider 示例
python examples/agent/provider_example.py

# 函数调用示例
python examples/agent/function_calling_example.py

# 高级用法示例
python examples/agent/advanced_example.py
```

## 📝 核心 API 概览

### Agent 类

```python
class Agent:
    def __init__(
        self,
        provider: LLMProvider,
        function_registry: Optional[FunctionRegistry] = None,
        system_prompt: Optional[str] = None,
    )
    
    async def chat(
        self,
        user_message: str,
        max_iterations: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]
    
    async def parse_message(
        self,
        sender: str,
        timestamp: str,
        content: str,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]
    
    def clear_history(self) -> None
    
    def register_function(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None
```

### create_provider 工厂函数

```python
provider = create_provider(
    provider_type: str,  # "openai" | "claude" | "minimax" | "open_source"
    **kwargs
)
```

### FunctionRegistry 类

```python
class FunctionRegistry:
    def register(
        self,
        name: str,
        description: str,
        func: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None
    
    def get_function(self, name: str) -> Optional[FunctionDefinition]
    
    def has_function(self, name: str) -> bool
    
    def list_functions(self) -> List[Dict[str, Any]]
```

## 🎯 使用建议

### 对于新手

1. 先运行 `basic_usage.py` 了解基本流程
2. 阅读 `QUICKSTART.md` 快速上手
3. 根据需求选择对应的示例学习

### 对于开发者

1. 查看 `design/agent.md` 了解架构设计
2. 参考测试文件 `tests/agent/` 了解边界情况
3. 使用 `FunctionRegistry` 注册业务函数
4. 通过 `create_provider()` 灵活切换模型

### 对于不同场景

- **简单对话**：使用 `basic_usage.py` 中的示例
- **需要函数调用**：参考 `function_calling_example.py`
- **切换模型**：参考 `provider_example.py`
- **复杂业务**：参考 `advanced_example.py` 并与数据库模块集成

## 📚 相关文档

- **设计文档**：`design/agent.md` - 详细的架构设计和设计决策
- **API 文档**：查看 `agent/` 目录下各文件的 docstring
- **测试用例**：`tests/agent/` - 了解各种使用场景和边界情况
- **数据库示例**：`examples/database/` - 了解如何与数据库模块集成

## ❓ 常见问题

### Q: 如何切换不同的 LLM 提供商？

A: 只需更换 `create_provider()` 的参数：

```python
# 从 OpenAI 切换到 Claude
provider = create_provider("claude", api_key="sk-ant-...")
agent = Agent(provider)  # Agent 代码无需修改
```

### Q: 如何注册自定义函数？

A: 有多种方式，推荐使用装饰器：

```python
from agent.functions.discovery import agent_callable

@agent_callable(description="我的业务函数")
def my_function(param: str) -> dict:
    # 业务逻辑
    return {"result": "..."}
```

### Q: 如何控制函数调用的迭代次数？

A: 在 `chat()` 方法中设置 `max_iterations` 参数：

```python
response = await agent.chat("复杂查询", max_iterations=5)
```

### Q: 如何清空对话历史？

A: 使用 `clear_history()` 方法：

```python
agent.clear_history()  # 保留系统提示词
```

### Q: 如何与数据库模块集成？

A: 参考 `advanced_example.py`，使用 `register_instance_methods()` 注册数据库方法：

```python
from agent.functions.discovery import register_instance_methods
from database import DatabaseManager

db = DatabaseManager("sqlite:///data/store.db")
register_instance_methods(registry, db, prefix="db_")
```

### Q: 支持哪些 LLM 提供商？

A: 目前支持：
- OpenAI（GPT 系列）
- Claude（Anthropic 系列）
- MiniMax（国内可用）
- 兼容 OpenAI API 的开源模型（vLLM、Ollama 等）

### Q: 如何添加新的 Provider？

A: 参考 `design/agent.md` 中的扩展指南，实现 `LLMProvider` 接口并在 `create_provider()` 中注册。

## 🤝 贡献

如果您发现示例有问题或需要添加新的示例，欢迎提交 Issue 或 Pull Request。
