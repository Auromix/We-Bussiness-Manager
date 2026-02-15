# Parsing 目录重组总结

## 重组完成 ✅

已成功整理 `parsing/` 目录，将适合的内容调整到 `agent/` 下。

## 最终结构

### parsing/ 目录（业务逻辑层）
```
parsing/
├── __init__.py
├── llm_parser.py          # Agent 适配器层
├── preprocessor.py         # 消息预处理器（业务逻辑）
└── pipeline.py            # 消息处理流水线（业务逻辑核心）
```

**职责**: 业务逻辑层，处理消息解析、预处理和流水线

### agent/ 目录（框架层）
```
agent/
├── agent.py               # Agent 核心
├── providers/            # LLM 提供商
├── functions/            # 函数调用机制
└── tools/                # 工具函数
    ├── __init__.py
    ├── entity_resolver.py  # 实体解析工具（从 parsing/ 移过来）
    └── README.md
```

**职责**: 框架层，提供 LLM 调用、函数调用和工具函数

## 变更详情

### 1. entity_resolver.py
- **原位置**: `parsing/entity_resolver.py`
- **新位置**: `agent/tools/entity_resolver.py`
- **原因**: 
  - 功能可以通过 Agent 直接调用数据库仓库方法实现
  - 作为工具函数更适合放在 `agent/tools/` 下
  - 保留作为可选工具，用于需要封装额外逻辑的场景

### 2. 保留在 parsing/ 的文件

#### llm_parser.py
- **保留原因**: Agent 适配器层，连接 parsing 和 agent
- **职责**: 提供向后兼容的接口，将 Agent 架构封装为 parsing 模块可用

#### preprocessor.py
- **保留原因**: 业务逻辑的一部分
- **职责**: 消息预处理（噪声过滤、意图分类、日期提取等）

#### pipeline.py
- **保留原因**: 业务逻辑核心
- **职责**: 完整的消息处理流水线

## 架构原则

### 职责分离
- **parsing/** = 业务逻辑层
  - 消息解析、预处理、流水线
  - 与业务配置和业务适配器紧密耦合
  
- **agent/** = 框架层
  - LLM 调用、函数调用机制、工具函数
  - 通用框架，可被不同业务使用

### 依赖关系
```
parsing/  →  agent/  (parsing 使用 agent)
agent/    ↛  parsing/  (agent 不依赖 parsing，保持独立性)
```

### 可复用性
- `agent/` 是通用框架，可以被不同业务使用
- `parsing/` 是当前业务的具体实现

## 使用建议

### 如果需要使用 EntityResolver

**方式 1: 直接使用工具类**
```python
from agent.tools import EntityResolver
from db.repository import DatabaseRepository

db_repo = DatabaseRepository()
resolver = EntityResolver(db_repo)
customer_id = resolver.resolve_customer("段老师")
```

**方式 2: 通过 Agent 函数调用（推荐）**
```python
# 启用函数调用后，Agent 可以直接调用：
# db_get_or_create_customer(name)
# db_get_or_create_employee(name, wechat_nickname)
# db_get_or_create_service_type(name)
```

## 文件统计

- **parsing/**: 3 个核心文件（llm_parser, preprocessor, pipeline）
- **agent/tools/**: 1 个工具文件（entity_resolver）
- **删除**: 0 个文件（entity_resolver 已迁移，未删除）

## 验证

✅ 所有文件语法正确
✅ 没有破坏性变更
✅ 向后兼容性保持
✅ 架构清晰，职责分离

## 后续建议

1. **entity_resolver 的使用**:
   - 如果不需要额外逻辑，直接使用数据库仓库方法
   - 如果需要封装逻辑，使用 `agent.tools.EntityResolver`

2. **添加新工具**:
   - 在 `agent/tools/` 下创建新文件
   - 使用 `@agent_callable` 装饰器让 Agent 自动调用

3. **保持架构清晰**:
   - 业务逻辑放在 `parsing/`
   - 通用工具放在 `agent/tools/`
   - 框架功能放在 `agent/` 其他子目录

