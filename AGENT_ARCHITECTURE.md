# Agent 架构重构总结

## 概述

已将大模型调用逻辑从 `parsing/llm_parser.py` 迁移到 `agent/` 目录下，实现了模块化、可扩展的 Agent 架构。

## 架构特点

### 1. 模块化设计
- **providers/**: 多种 LLM 提供商实现（OpenAI、Claude、开源模型）
- **functions/**: 函数调用机制（注册表、执行器、仓库工具）
- **agent.py**: Agent 核心类，整合 LLM 和函数调用

### 2. 扩展性
- 易于添加新的 LLM 提供商（实现 `LLMProvider` 接口）
- 易于注册新的函数工具（通过 `FunctionRegistry`）
- 支持自定义函数调用逻辑

### 3. 与业务逻辑分离
- Agent 模块不包含业务逻辑
- 不直接操作数据库，通过仓库函数接口
- 通过函数注册机制，灵活集成各种功能

## 目录结构

```
agent/
├── __init__.py                    # 模块导出
├── agent.py                       # Agent 核心类
├── README.md                      # 使用文档
├── providers/                     # LLM 提供商
│   ├── __init__.py
│   ├── base.py                  # LLMProvider 基类
│   ├── openai_provider.py        # OpenAI 实现
│   ├── claude_provider.py        # Claude 实现
│   └── open_source_provider.py   # 开源模型实现
└── functions/                     # 函数调用
    ├── __init__.py
    ├── registry.py               # 函数注册表
    ├── executor.py               # 函数执行器
    └── discovery.py              # 函数自动发现机制
```

## 主要组件

### LLMProvider（LLM 提供商接口）

所有大模型提供商都需要实现此接口：

```python
class LLMProvider(ABC):
    async def chat(messages, functions=None, **kwargs) -> LLMResponse
    def supports_function_calling() -> bool
    @property
    def model_name() -> str
```

### FunctionRegistry（函数注册表）

管理 Agent 可调用的函数：

```python
registry = FunctionRegistry()
registry.register(name, description, func, parameters)
```

### Agent（智能体）

整合 LLM 和函数调用：

```python
agent = Agent(provider, function_registry, system_prompt)
response = await agent.chat("用户消息")
```

## 使用方式

### 1. 基础使用（不启用函数调用）

```python
from parsing.llm_parser import create_llm_parser

llm_parser = create_llm_parser()
# 与之前使用方式完全一致，向后兼容
```

### 2. 启用函数调用

在 `.env` 中设置：
```bash
ENABLE_FUNCTION_CALLING=true
```

或在代码中：
```python
# 只启用数据库函数
llm_parser = create_llm_parser(
    db_repo=db_repo,
    enable_function_calling=True
)

# 启用数据库函数 + 自定义服务
llm_parser = create_llm_parser(
    db_repo=db_repo,
    enable_function_calling=True,
    custom_function_targets=[
        (membership_svc, "membership_"),
        (inventory_svc, "inventory_"),
    ]
)
```

### 3. 直接使用 Agent

```python
from agent import Agent, create_provider
from agent.functions.registry import FunctionRegistry
from agent.functions.discovery import register_instance_methods

# 创建提供商
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")

# 创建函数注册表并自动注册仓库函数
registry = FunctionRegistry()
register_instance_methods(
    registry,
    db_repo,
    class_name="DatabaseRepository",
    prefix="db_"
)
# 自动注册所有 DatabaseRepository 的公共方法

# 创建 Agent
agent = Agent(provider, registry, system_prompt)

# 使用 - Agent 可以直接调用数据库方法
response = await agent.chat("查询顾客'段老师'的信息")
# Agent 会自动调用 db_get_or_create_customer 方法
```

## 函数自动发现机制

Agent 支持自动发现和注册代码库中的函数，无需手动包装。

### 自动注册模式

通过 `register_instance_methods()` 可以自动注册对象的所有公共方法：

```python
from agent.functions.discovery import register_instance_methods

register_instance_methods(
    registry,
    db_repo,
    class_name="DatabaseRepository",
    prefix="db_"
)
# 自动注册所有 DatabaseRepository 的公共方法，如:
# - db_get_or_create_customer
# - db_save_service_record
# - db_get_records_by_date
# - 等等...
```

### 使用装饰器标记函数

```python
from agent.functions.discovery import agent_callable

@agent_callable(description="查询顾客信息")
def get_customer_info(name: str) -> dict:
    ...
```

### 注册多个对象

```python
from agent.functions.discovery import auto_discover_and_register

auto_discover_and_register(registry, [
    (db_repo, "db_"),              # 数据库操作
    (membership_svc, "membership_"),  # 会员服务
    (inventory_svc, "inventory_"),   # 库存服务
])
```

详细用法请参考 `agent/functions/USAGE.md`

## 向后兼容性

- `parsing/llm_parser.py` 中的 `LLMParser` 接口保持不变
- `create_llm_parser()` 函数签名兼容（新增可选参数）
- 现有代码无需修改即可使用

## 扩展指南

### 添加新的 LLM 提供商

1. 在 `agent/providers/` 下创建新文件
2. 继承 `LLMProvider` 并实现接口
3. 在 `providers/__init__.py` 的 `create_provider()` 中注册

### 添加新的函数工具

1. 在 `agent/functions/` 下创建新文件
2. 定义注册函数，使用 `FunctionRegistry.register()`
3. 在需要的地方调用注册函数

## 配置说明

在 `.env` 中配置：

```bash
# LLM 提供商
PRIMARY_LLM=openai  # 或 anthropic
FALLBACK_LLM=anthropic

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 函数调用（可选）
ENABLE_FUNCTION_CALLING=false

# 开源模型（如果使用）
OPEN_SOURCE_BASE_URL=http://localhost:8000/v1
OPEN_SOURCE_MODEL=qwen
```

## 依赖更新

已在 `requirements.txt` 中添加：
- `httpx>=0.24.0`（用于开源模型提供商）

## 注意事项

1. **函数调用安全**: 只注册必要的函数，避免暴露敏感操作
2. **性能**: 函数调用会增加响应时间
3. **成本**: 函数调用会增加 API 调用次数
4. **错误处理**: 函数执行失败时，Agent 会收到错误信息

## 迁移检查清单

- [x] 创建 agent 目录结构
- [x] 实现 LLMProvider 基类和多种提供商
- [x] 实现函数调用机制
- [x] 创建 Agent 核心类
- [x] 重构 llm_parser.py 使用新架构
- [x] 保持向后兼容
- [x] 更新 main.py 支持函数调用
- [x] 创建文档

## 下一步

1. 测试各种 LLM 提供商的集成
2. 根据实际需求添加更多仓库函数
3. 优化函数调用的性能和错误处理
4. 考虑添加函数调用的权限控制

