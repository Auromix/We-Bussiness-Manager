# Agent 模块文档

Agent 模块提供了统一的大模型调用和函数调用框架，支持多种模型接入，具备良好的扩展性和模块性。

## 架构设计

```
agent/
├── __init__.py              # 模块导出
├── agent.py                 # Agent 核心类
├── providers/               # LLM 提供商
│   ├── __init__.py
│   ├── base.py             # 提供商基类
│   ├── openai_provider.py  # OpenAI 实现
│   ├── claude_provider.py  # Claude 实现
│   └── open_source_provider.py  # 开源模型实现
└── functions/               # 函数调用
    ├── __init__.py
    ├── registry.py         # 函数注册表
    ├── executor.py         # 函数执行器
    └── discovery.py        # 函数自动发现机制
```

## 核心概念

### 1. LLMProvider（LLM 提供商）

所有大模型提供商都需要实现 `LLMProvider` 接口，提供统一的调用方式。

支持的提供商：
- **OpenAI**: GPT-4, GPT-4o-mini 等
- **Claude**: Claude Sonnet, Claude Opus 等
- **开源模型**: 任何兼容 OpenAI API 格式的模型（通过 HTTP API）

### 2. FunctionRegistry（函数注册表）

管理 Agent 可以调用的所有函数，包括：
- 仓库函数（查询、保存等）
- 业务逻辑函数
- 工具函数

### 3. Agent（智能体）

整合 LLM 和函数调用，提供统一的对话接口。

## 使用示例

### 基础使用

```python
from agent import Agent, create_provider

# 创建提供商
provider = create_provider(
    "openai",
    api_key="sk-...",
    model="gpt-4o-mini"
)

# 创建 Agent
agent = Agent(provider, system_prompt="你是一个助手")

# 对话
response = await agent.chat("你好")
print(response["content"])
```

### 启用函数调用（自动发现模式）

```python
from agent import Agent, create_provider, FunctionRegistry
from agent.functions.discovery import register_instance_methods
from db.repository import DatabaseRepository

# 创建数据库仓库
db_repo = DatabaseRepository()

# 创建函数注册表
function_registry = FunctionRegistry()

# 自动注册 db_repo 的所有公共方法
# 方法会被注册为: db_get_customer, db_save_service_record 等
register_instance_methods(
    function_registry,
    db_repo,
    class_name="DatabaseRepository",
    prefix="db_"
)

# 创建提供商和 Agent
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")
agent = Agent(provider, function_registry, system_prompt="你是一个助手")

# 现在 Agent 可以直接调用数据库方法
response = await agent.chat("查询顾客'段老师'的信息")
# Agent 会自动调用 db_get_or_create_customer 方法
```

### 注册多个对象

```python
from agent.functions.discovery import auto_discover_and_register
from services.membership_svc import MembershipService

membership_svc = MembershipService(db_repo)

# 注册多个对象，使用前缀避免命名冲突
auto_discover_and_register(function_registry, [
    (db_repo, "db_"),              # 数据库操作
    (membership_svc, "membership_"),  # 会员服务
])
```

### 使用装饰器标记函数

```python
from agent.functions.discovery import agent_callable

@agent_callable(description="自定义查询函数")
def my_custom_function(param1: str, param2: int = 10) -> dict:
    """自定义函数"""
    return {"result": f"{param1}: {param2}"}

# 自动注册标记的函数
from agent.functions.discovery import auto_discover_and_register
registry = FunctionRegistry()
auto_discover_and_register(registry, [my_custom_function])
```

### 手动注册函数

```python
from agent.functions.registry import FunctionRegistry

def my_custom_function(param1: str, param2: int) -> dict:
    """自定义函数"""
    return {"result": f"{param1}: {param2}"}

registry = FunctionRegistry()
registry.register(
    name="my_custom_function",
    description="这是一个自定义函数",
    func=my_custom_function
    # parameters 会自动推断，也可以手动指定
)
```

### 使用开源模型

```python
from agent import Agent, create_provider

# 使用兼容 OpenAI API 格式的开源模型
provider = create_provider(
    "open_source",
    base_url="http://localhost:8000/v1",  # 模型服务地址
    model="qwen",  # 模型名称
    api_key="optional-key"  # 如果需要
)

agent = Agent(provider, system_prompt="你是一个助手")
response = await agent.chat("你好")
```

## 集成到现有代码

### 在 parsing/llm_parser.py 中使用

`create_llm_parser` 函数已经更新为使用新的 Agent 架构，同时保持向后兼容：

```python
from parsing.llm_parser import create_llm_parser
from db.repository import DatabaseRepository

db_repo = DatabaseRepository()

# 不启用函数调用（默认）
llm_parser = create_llm_parser()

# 启用函数调用
llm_parser = create_llm_parser(
    db_repo=db_repo,
    enable_function_calling=True
)
```

### 在 main.py 中启用

设置环境变量 `ENABLE_FUNCTION_CALLING=true` 即可启用函数调用功能。

## 扩展性

### 添加新的 LLM 提供商

1. 在 `agent/providers/` 下创建新的提供商文件
2. 继承 `LLMProvider` 基类
3. 实现 `chat()` 和 `supports_function_calling()` 方法
4. 在 `providers/__init__.py` 中注册

示例：

```python
from agent.providers.base import LLMProvider, LLMMessage, LLMResponse

class MyCustomProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        # 初始化
        pass
    
    async def chat(self, messages, functions=None, **kwargs) -> LLMResponse:
        # 实现聊天逻辑
        pass
    
    def supports_function_calling(self) -> bool:
        return True
    
    @property
    def model_name(self) -> str:
        return self._model
```

### 添加新的函数工具

在 `agent/functions/` 下创建新的工具文件，注册函数到注册表：

```python
from agent.functions.registry import FunctionRegistry

def register_my_tools(registry: FunctionRegistry, dependencies):
    """注册自定义工具"""
    registry.register(
        name="my_tool",
        description="工具描述",
        func=my_function,
        parameters={...}
    )
```

## 注意事项

1. **函数调用安全**: 只注册必要的函数，避免暴露敏感操作
2. **错误处理**: 函数执行失败时，Agent 会收到错误信息并可以重试
3. **性能**: 函数调用会增加 LLM 的响应时间，合理使用
4. **成本**: 函数调用会增加 API 调用次数，注意成本控制

## 配置

在 `.env` 文件中配置：

```bash
# LLM 配置
PRIMARY_LLM=openai  # 或 anthropic
FALLBACK_LLM=anthropic
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 函数调用（可选）
ENABLE_FUNCTION_CALLING=true

# 开源模型配置（如果使用）
OPEN_SOURCE_BASE_URL=http://localhost:8000/v1
OPEN_SOURCE_MODEL=qwen
```

