# 架构分析 - 复用性检查

## 🔍 当前架构分析

### 发现的耦合问题

#### 1. 业务逻辑耦合在 Pipeline 中 ❌

**位置**: `parsing/pipeline.py`

```python
# 问题：直接调用业务特定的保存方法
def _save_business_record(self, record_type: str, data: Dict[str, Any], ...):
    if record_type == 'service':
        return self.db.save_service_record(data, raw_message_id)  # 业务特定
    elif record_type == 'product_sale':
        return self.db.save_product_sale(data, raw_message_id)    # 业务特定
    elif record_type == 'membership':
        return self.db.save_membership(data, raw_message_id)       # 业务特定
```

**问题**: Pipeline 直接依赖业务逻辑，新项目需要修改 Pipeline 代码。

#### 2. 数据库 Repository 包含业务逻辑 ❌

**位置**: `db/repository.py`

```python
# 问题：Repository 包含业务特定的方法
def save_service_record(...)      # 业务特定
def save_product_sale(...)        # 业务特定
def save_membership(...)          # 业务特定
```

**问题**: Repository 应该只提供通用的数据库操作，业务逻辑应该分离。

#### 3. 业务配置耦合在配置文件中 ❌

**位置**: `config/prompts.py`, `config/known_entities.py`

```python
# 问题：包含业务特定的提示词和实体
SERVICE_TYPES = [...]  # 业务特定
SYSTEM_PROMPT = "..."  # 业务特定
```

**问题**: 新项目需要修改配置文件。

#### 4. 命令处理器直接依赖业务服务 ⚠️

**位置**: `core/command_handler.py`

```python
# 问题：直接依赖业务服务
self.summary_svc = SummaryService(db_repo)  # 业务特定
```

**问题**: 命令处理器应该通过接口依赖，而不是具体实现。

## ✅ 做得好的地方

1. **LLM 解析器抽象** ✅
   - `parsing/llm_parser.py` 使用接口，支持多种 LLM
   - 可以轻松切换 OpenAI/Claude

2. **微信集成抽象** ✅
   - `core/bot.py` 提供了 Mock 模式
   - 可以替换为其他微信桥接方案

3. **数据库抽象** ⚠️
   - 使用 SQLAlchemy ORM，可以切换数据库
   - 但 Repository 包含业务逻辑

## 🎯 重构目标

1. **业务逻辑层** - 完全独立，可替换
2. **数据库层** - 只提供通用操作，不包含业务逻辑
3. **Pipeline** - 通过接口调用业务逻辑，不直接依赖
4. **配置** - 业务配置可替换
5. **命令处理** - 通过接口依赖业务服务

