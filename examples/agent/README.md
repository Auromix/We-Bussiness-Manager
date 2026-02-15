# Agent 模块使用示例

本目录包含 Agent 模块的各种使用示例，展示如何使用 Agent 进行对话和函数调用。

## 示例列表

### 1. 基础使用示例 (`basic_example.py`)

展示 Agent 的基础功能，包括：

- **创建不同的 LLM 提供商**
  - OpenAI（GPT 系列）
  - Claude（Anthropic 系列）
  - 开源模型（兼容 OpenAI API 格式）

- **创建 Agent 实例**
  - 设置系统提示词
  - 配置对话上下文

- **进行对话**
  - 单轮对话
  - 多轮对话（利用上下文）

- **管理对话历史**
  - 查看对话历史
  - 清空对话历史

### 2. 函数调用示例 (`function_calling_example.py`)

展示如何使用 Agent 进行函数调用，包括：

- **使用装饰器标记函数**
  ```python
  @agent_callable(description="获取天气信息")
  def get_weather(city: str) -> dict:
      ...
  ```

- **手动注册函数**
  ```python
  registry.register(name="my_function", description="...", func=my_function)
  ```

- **自动注册实例方法**
  ```python
  register_instance_methods(registry, db_repo, prefix="db_")
  ```

- **自动注册多个对象**
  ```python
  auto_discover_and_register(registry, [
      (calculator, "calc_"),
      (db_service, "db_"),
  ])
  ```

- **多步骤函数调用**
  - Agent 自动处理函数调用链
  - 支持多轮迭代


## 运行示例

### 前置要求

1. **安装项目依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **设置环境变量**（根据需要选择）：
   ```bash
   # OpenAI
   export OPENAI_API_KEY="sk-..."

   # Claude
   export ANTHROPIC_API_KEY="sk-ant-..."

   # 开源模型（可选）
   export OPEN_SOURCE_BASE_URL="http://localhost:8000/v1"
   export OPEN_SOURCE_MODEL="qwen"
   export OPEN_SOURCE_API_KEY="optional-key"
   ```

### 运行基础示例

```bash
# 从项目根目录运行
python examples/agent/basic_example.py
```

### 运行函数调用示例

```bash
python examples/agent/function_calling_example.py
```

## 示例输出

运行示例后，你将看到：

1. **详细的日志输出**
   - 每个步骤的执行情况
   - 函数调用信息
   - 错误提示（如果有）

2. **对话示例**
   - 用户问题和 Agent 回答
   - 函数调用结果
   - 迭代次数统计

3. **函数注册信息**
   - 已注册的函数列表
   - 函数描述和参数

## 代码结构说明

### 基础示例 (`basic_example.py`)

主要函数：
- `example_openai()`: 使用 OpenAI Provider
- `example_claude()`: 使用 Claude Provider
- `example_open_source()`: 使用开源模型 Provider
- `example_conversation_history()`: 管理对话历史

### 函数调用示例 (`function_calling_example.py`)

主要函数：
- `example_decorator_functions()`: 使用装饰器标记的函数
- `example_manual_registration()`: 手动注册函数
- `example_instance_methods()`: 自动注册实例方法
- `example_auto_discover()`: 自动发现并注册
- `example_multi_step_function_calling()`: 多步骤函数调用

示例类：
- `Calculator`: 计算器类
- `DatabaseService`: 数据库服务类

## 关键概念

### 1. LLM Provider

所有 LLM 提供商都实现 `LLMProvider` 接口，提供统一的调用方式：

```python
from agent import create_provider

# 创建 Provider
provider = create_provider("openai", api_key="sk-...", model="gpt-4o-mini")
```

支持的 Provider：
- `openai`: OpenAI GPT 系列
- `claude`: Anthropic Claude 系列
- `open_source`: 兼容 OpenAI API 的开源模型

### 2. Function Registry

函数注册表管理所有可被 Agent 调用的函数：

```python
from agent import FunctionRegistry

registry = FunctionRegistry()
registry.register(name="my_func", description="...", func=my_func)
```

### 3. Agent

Agent 整合 LLM 和函数调用，提供统一的对话接口：

```python
from agent import Agent

agent = Agent(provider, registry, system_prompt="你是一个助手")
response = await agent.chat("查询用户信息")
```

### 4. 函数调用流程

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

## 最佳实践

### 1. 函数命名

- 使用清晰、描述性的函数名
- 使用前缀避免命名冲突（如 `db_`, `calc_`）
- 保持函数名与功能一致

### 2. 函数描述

- 提供详细的函数描述，帮助 LLM 理解函数用途
- 描述应该包括参数说明和返回值说明
- 使用中文描述（如果 Agent 使用中文）

### 3. 错误处理

- 函数应该处理可能的错误情况
- 返回有意义的错误信息
- Agent 会将错误信息传递给 LLM

### 4. Provider 选择

- **OpenAI**: 适合大多数场景，函数调用支持好
- **Claude**: 适合需要高质量回复的场景
- **开源模型**: 适合本地部署或成本敏感的场景

### 5. 对话历史管理

- 大量对话历史可能影响性能和成本
- 定期清空对话历史（`agent.clear_history()`）
- 根据需求设置合适的 `max_iterations`

## 扩展示例

你可以基于这些示例创建自己的应用：

1. **集成数据库操作**
   ```python
   from db.repository import DatabaseRepository
   from agent.functions.discovery import register_instance_methods

   db_repo = DatabaseRepository()
   register_instance_methods(registry, db_repo, prefix="db_")
   ```

2. **集成业务服务**
   ```python
   from services.membership_svc import MembershipService

   membership_svc = MembershipService(db_repo)
   register_instance_methods(registry, membership_svc, prefix="membership_")
   ```

3. **自定义函数**
   ```python
   @agent_callable(description="自定义业务函数")
   def my_business_function(param: str) -> dict:
       # 业务逻辑
       return {"result": "..."}
   ```

## 注意事项

1. **API Key 安全**
   - 不要将 API Key 硬编码在代码中
   - 使用环境变量或配置文件
   - 不要将包含 API Key 的代码提交到版本控制

2. **成本控制**
   - 函数调用会增加 API 调用次数
   - 合理设置 `max_iterations` 限制
   - 监控 API 使用量和成本

3. **错误处理**
   - 函数执行失败时，Agent 会收到错误信息
   - LLM 可能会重试或使用替代方案
   - 确保函数有适当的错误处理

4. **性能优化**
   - 大量对话历史可能影响响应速度
   - 定期清空对话历史
   - 考虑使用更快的模型（如 gpt-4o-mini）

## 相关文档

- [Agent 模块文档](../../agent/README.md)
- [Agent 架构设计](../../design/agent.md)
- [数据库示例](../database/README.md)

## 问题排查

### 问题：API Key 未设置

**错误信息**：`未设置 OPENAI_API_KEY 环境变量`

**解决方案**：
```bash
export OPENAI_API_KEY="sk-..."
```

### 问题：函数调用失败

**错误信息**：`Error executing function ...`

**可能原因**：
1. 函数参数类型不匹配
2. 函数执行时出错
3. 函数未正确注册

**解决方案**：
1. 检查函数参数类型
2. 查看函数实现是否有错误
3. 确认函数已正确注册到注册表

### 问题：开源模型连接失败

**错误信息**：`调用开源模型失败: Connection refused`

**解决方案**：
1. 确认本地模型服务正在运行
2. 检查 `OPEN_SOURCE_BASE_URL` 是否正确
3. 确认模型服务支持 OpenAI API 格式

## 贡献

如果你有新的示例想法或发现了问题，欢迎提交 Issue 或 Pull Request。

