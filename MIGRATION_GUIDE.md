# 新项目迁移指南

## 🎯 目标

将当前项目重构为可复用架构，新项目只需要：
1. 实现业务逻辑适配器
2. 创建业务配置
3. 定义数据库模型
4. 修改主程序中的适配器实例

**核心框架代码（Pipeline、Bot、LLM等）不需要修改！**

## 📋 迁移步骤

### 步骤 1: 创建新项目目录结构

```
new-project/
├── business/
│   ├── __init__.py
│   └── new_project_adapter.py    # 新项目的业务逻辑适配器
├── config/
│   └── new_project_config.py     # 新项目的业务配置
├── db/
│   ├── new_project_models.py     # 新项目的数据库模型
│   └── new_project_repository.py # 新项目的数据库访问层
└── main.py                        # 主程序（修改适配器实例）
```

### 步骤 2: 实现业务逻辑适配器

创建 `business/new_project_adapter.py`:

```python
from core.business_adapter import BusinessLogicAdapter
from db.new_project_repository import NewProjectRepository
from typing import Dict, Any, Optional, List
from datetime import date

class NewProjectAdapter(BusinessLogicAdapter):
    """新项目的业务逻辑适配器"""
    
    def __init__(self, db_repo: NewProjectRepository):
        self.db = db_repo
    
    def save_business_record(self, record_type: str, data: Dict[str, Any], 
                            raw_message_id: int, confirmed: bool) -> int:
        """保存业务记录 - 根据新项目的业务逻辑实现"""
        if record_type == 'order':  # 新项目的记录类型
            return self.db.save_order(data, raw_message_id)
        elif record_type == 'payment':
            return self.db.save_payment(data, raw_message_id)
        # ... 其他记录类型
        else:
            raise ValueError(f"Unknown record type: {record_type}")
    
    def get_records_by_date(self, target_date: date, record_types: Optional[List[str]] = None) -> List[Dict]:
        """按日期查询记录"""
        return self.db.get_records_by_date(target_date, record_types)
    
    def generate_summary(self, summary_type: str, **kwargs) -> str:
        """生成汇总报告"""
        if summary_type == 'daily':
            # 实现每日汇总逻辑
            return "每日汇总..."
        # ... 其他汇总类型
        return ""
    
    def handle_command(self, command: str, args: list, context: Dict[str, Any]) -> str:
        """处理命令"""
        if command == '订单查询':
            # 实现订单查询逻辑
            return "订单查询结果..."
        # ... 其他命令
        return f"未知命令: {command}"
```

### 步骤 3: 创建业务配置

创建 `config/new_project_config.py`:

```python
from config.business_config import BusinessConfig
from typing import List, Dict

class NewProjectConfig(BusinessConfig):
    """新项目的业务配置"""
    
    def get_service_types(self) -> List[Dict[str, Any]]:
        # 返回新项目的服务类型（如果有）
        return []
    
    def get_product_categories(self) -> List[str]:
        # 返回新项目的商品类别
        return ["product_a", "product_b"]
    
    def get_membership_card_types(self) -> List[str]:
        # 返回新项目的会员卡类型（如果有）
        return []
    
    def get_llm_system_prompt(self) -> str:
        """返回新项目的 LLM 系统提示词"""
        return """你是一个新项目的数据录入助手。你的任务是从消息中提取结构化数据。

## 业务类型
1. 订单：客户下单
2. 支付：客户付款
...

## 输出格式
返回 JSON 数组，格式：
{
  "type": "order" | "payment" | "noise",
  "date": "YYYY-MM-DD",
  ...
}
"""
    
    def get_noise_patterns(self) -> List[str]:
        # 返回噪声消息模式
        return [r'^好的$', r'^收到$']
    
    def get_service_keywords(self) -> List[str]:
        # 返回服务关键词（如果有）
        return []
    
    def get_product_keywords(self) -> List[str]:
        # 返回商品关键词
        return ['商品A', '商品B']
    
    def get_membership_keywords(self) -> List[str]:
        # 返回会员关键词（如果有）
        return []
```

### 步骤 4: 创建数据库模型

创建 `db/new_project_models.py`:

```python
from sqlalchemy import Column, Integer, String, DECIMAL, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(50))
    order_date = Column(Date)
    amount = Column(DECIMAL(10, 2))
    # ... 其他字段

class Payment(Base):
    """支付表"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    payment_date = Column(Date)
    amount = Column(DECIMAL(10, 2))
    # ... 其他字段
```

### 步骤 5: 创建数据库 Repository

创建 `db/new_project_repository.py`:

```python
from db.base_repository import BaseRepository
from db.new_project_models import Base, Order, Payment
from typing import Dict, Any, List
from datetime import date

class NewProjectRepository(BaseRepository):
    """新项目的数据库访问层"""
    
    def save_order(self, data: Dict[str, Any], raw_message_id: int) -> int:
        """保存订单"""
        with self.get_session() as session:
            order = Order(
                customer_name=data.get('customer_name'),
                order_date=data.get('date'),
                amount=data.get('amount'),
                # ...
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return order.id
    
    def save_payment(self, data: Dict[str, Any], raw_message_id: int) -> int:
        """保存支付记录"""
        # 实现支付记录保存逻辑
        pass
    
    def get_records_by_date(self, target_date: date, record_types: List[str] = None) -> List[Dict]:
        """按日期查询记录"""
        # 实现查询逻辑
        pass
```

### 步骤 6: 修改主程序

修改 `main.py`:

```python
# 导入新项目的适配器和配置
from business.new_project_adapter import NewProjectAdapter
from config.new_project_config import NewProjectConfig
from db.new_project_repository import NewProjectRepository

# 在 main() 函数中：
def main():
    # ... 其他初始化代码 ...
    
    # 使用新项目的配置
    business_config = NewProjectConfig()
    
    # 使用新项目的数据库
    db_repo = NewProjectRepository()
    db_repo.create_tables()
    
    # 使用新项目的业务逻辑适配器
    business_adapter = NewProjectAdapter(db_repo)
    
    # 使用新配置初始化预处理器
    preprocessor = MessagePreProcessor(config=business_config)
    
    # 使用新配置的提示词初始化 LLM
    llm_parser = create_llm_parser(system_prompt=business_config.get_llm_system_prompt())
    
    # 其他代码不需要修改！
    pipeline = MessagePipeline(preprocessor, llm_parser, db_repo, business_adapter)
    command_handler = CommandHandler(db_repo, business_adapter)
    # ...
```

## ✅ 迁移检查清单

### 核心框架（不需要修改）

- [x] `parsing/pipeline.py` - 通过适配器调用业务逻辑
- [x] `core/bot.py` - 微信集成，可替换
- [x] `parsing/llm_parser.py` - LLM 调用，可替换
- [x] `core/command_handler.py` - 通过适配器调用业务逻辑
- [x] `core/scheduler.py` - 通过适配器调用业务逻辑

### 新项目需要实现

- [ ] `business/new_project_adapter.py` - 业务逻辑适配器
- [ ] `config/new_project_config.py` - 业务配置
- [ ] `db/new_project_models.py` - 数据库模型
- [ ] `db/new_project_repository.py` - 数据库访问层
- [ ] 修改 `main.py` 中的适配器实例

## 📊 架构对比

### 重构前（耦合）

```
Pipeline → db.save_service_record()  # 直接调用业务方法
CommandHandler → SummaryService()    # 直接依赖业务服务
Preprocessor → SERVICE_KEYWORDS      # 硬编码业务关键词
```

### 重构后（解耦）

```
Pipeline → BusinessLogicAdapter.save_business_record()  # 通过接口
CommandHandler → BusinessLogicAdapter.generate_summary()  # 通过接口
Preprocessor → BusinessConfig.get_service_keywords()  # 从配置获取
```

## 🎯 复用性验证

### 验证点 1: LLM 调用 ✅

- 支持多种 LLM（OpenAI/Claude）
- 系统提示词可从业务配置获取
- 可以轻松替换为其他 LLM 服务

### 验证点 2: 微信集成 ✅

- Bot 类提供抽象接口
- 支持 Mock 模式
- 可以替换为其他微信桥接方案

### 验证点 3: 数据库 ✅

- 使用 SQLAlchemy ORM
- 可以切换数据库（SQLite/PostgreSQL）
- 业务逻辑通过 Repository 封装

### 验证点 4: 业务逻辑 ✅

- 通过 `BusinessLogicAdapter` 接口完全解耦
- 新项目只需实现接口
- 核心代码不需要修改

## 📝 示例：新项目模板

见 `PROJECT_TEMPLATE.md` 获取完整的新项目模板。

## 🔍 常见问题

### Q1: 如何替换 LLM？

```python
# 在 main.py 中
from parsing.llm_parser import create_llm_parser

# 使用业务配置的提示词
llm_parser = create_llm_parser(system_prompt=business_config.get_llm_system_prompt())
```

### Q2: 如何替换微信桥接？

```python
# 实现自己的 Bot 类
class CustomWeChatBot:
    def __init__(self, router):
        # 实现微信连接逻辑
        pass
    
    def start(self):
        # 启动逻辑
        pass

# 在 main.py 中使用
bot = CustomWeChatBot(router)
```

### Q3: 如何添加新的命令？

在 `BusinessLogicAdapter.handle_command()` 中实现：

```python
def handle_command(self, command: str, args: list, context: Dict[str, Any]) -> str:
    if command == '新命令':
        # 实现新命令逻辑
        return "结果"
    # ...
```

## ✅ 总结

重构后的架构支持：

1. ✅ **LLM 调用独立** - 可替换，支持多种 LLM
2. ✅ **微信集成独立** - 可替换，支持多种桥接方案
3. ✅ **数据库独立** - 可切换，业务逻辑分离
4. ✅ **业务逻辑独立** - 通过接口完全解耦

**新项目只需要实现业务逻辑适配器和配置，核心框架代码完全复用！**

